import os
import json
import logging
import boto3
import tempfile
import signal
import sys
import time
from paragraph_extractor import TextExtractor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AWS clients
sqs = boto3.client('sqs')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
submissions_table = dynamodb.Table(os.environ.get('SUBMISSIONS_TABLE'))

# Configuration
QUEUE_URL = os.environ.get('PARAGRAPHS_QUEUE_URL')
SUBMISSIONS_BUCKET = os.environ.get('SUBMISSIONS_BUCKET')
PARAGRAPHS_BUCKET = os.environ.get('PARAGRAPHS_BUCKET')

# Validate required environment variables
required_env_vars = ['PARAGRAPHS_QUEUE_URL', 'SUBMISSIONS_BUCKET', 'PARAGRAPHS_BUCKET', 'SUBMISSIONS_TABLE']
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

def extract_submission_data_from_key(key):
    """Extract user ID from S3 key format: uploads/{user_id}/{file_hash}.txt"""
    parts = key.split('/')
    if len(parts) >= 3 and parts[0] == 'uploads':
        return parts[1], parts[2]
    else:
        raise ValueError(f"Invalid S3 key format: {key}")

def write_to_dynamodb(submission_id, user_id):
    """Write submission record to DynamoDB."""
    submissions_table.put_item(
        Item={
            'submission_id': submission_id,
            'user_id': user_id,
            'created_at': int(time.time())
        }
    )
    logger.info(f"Successfully wrote submission {submission_id} to DynamoDB")

def download_file(bucket, key):
    """Download a file from S3 to a temporary location."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        s3.download_fileobj(bucket, key, temp_file)
        return temp_file.name

def upload_paragraphs(bucket, key, paragraphs):
    """Upload paragraphs to S3."""
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(paragraphs),
        ContentType='application/json'
    )

def process_record(record):
    """Process a single S3 record."""
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']

    logger.info(f"Processing file: {key} from bucket: {bucket}")

    user_id, submission_id = extract_submission_data_from_key(key)
    write_to_dynamodb(submission_id, user_id)
    temp_file = download_file(bucket, key)

    try:
        # Extract paragraphs
        extractor = TextExtractor(temp_file)
        text = extractor.extract()
        paragraphs = extractor.extract_paragraphs(text)

        # Upload paragraphs to paragraphs bucket
        output_key = f"{os.path.splitext(key)[0]}_paragraphs.json"
        upload_paragraphs(PARAGRAPHS_BUCKET, output_key, paragraphs)

        logger.info(f"Successfully processed {key} into {output_key}")

    finally:
        # Clean up temporary file
        os.unlink(temp_file)

def process_message(message):
    body = json.loads(message['Body'])
    for record in body['Records']:
        process_record(record)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
    sys.exit(0)

def main():
    """Main function to poll SQS queue."""
    logger.info("Starting paragraphs service...")

    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    consecutive_errors = 0
    max_consecutive_errors = 5

    while True:
        try:
            # Receive messages from SQS
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20  # Long polling
            )

            if 'Messages' in response:
                for message in response['Messages']:
                    try:
                        process_message(message)

                        # Delete the message after successful processing
                        sqs.delete_message(
                            QueueUrl=QUEUE_URL,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        consecutive_errors = 0  # Reset error counter on success

                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            logger.error("Too many consecutive errors. Shutting down...")
                            sys.exit(1)
                        continue

        except Exception as e:
            logger.error(f"Error polling queue: {e}")
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                logger.error("Too many consecutive errors. Shutting down...")
                sys.exit(1)
            continue

if __name__ == "__main__":
    main()
