import os
import json
import logging
import tempfile
import signal
import sys
import time

from common.envvar import environment
from paragraph_extractor import TextExtractor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import boto3
from sqs_client import sqs_client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SUBMISSIONS_TABLE = 'submissions'
QUEUE_NAME = 'history-learning-paragraphs'
SUBMISSIONS_BUCKET = environment.require('SUBMISSIONS_BUCKET')
PARAGRAPHS_BUCKET = environment.require('PARAGRAPHS_BUCKET')

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
submissions_table = dynamodb.Table(SUBMISSIONS_TABLE)

# Initialize SQS client
queue_client = sqs_client.for_queue(QUEUE_NAME)

def extract_submission_data_from_key(key):
    """Extract user ID from S3 key format: uploads/{user_id}/{file_hash}.txt"""
    parts = key.split('/')
    if len(parts) >= 3 and parts[0] == 'uploads':
        return parts[1], parts[2]
    else:
        raise ValueError(f"Invalid S3 key format: {key}")

def write_to_dynamodb(submission_id, user_id):
    """Write submission record to DynamoDB."""
    submissions_table.put_item(Item={
        'submission_id': submission_id,
        'user_id': user_id,
        'created_at': int(time.time())
    })

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

def signal_handler(_signum, _frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal. Cleaning up...")
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
            logger.info("Receiving messages from SQS...")

            # Receive messages from SQS
            messages = queue_client.receive_messages(max_messages=1, wait_time_seconds=20)

            for message in messages:
                try:
                    process_message(message)

                    # Delete the message after successful processing
                    queue_client.delete_message(message['ReceiptHandle'])
                    consecutive_errors = 0  # Reset error counter on success

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("Too many consecutive errors. Shutting down...")
                        sys.exit(1)
                    continue

        except Exception as e:
            logger.error(f"Error polling queue: {e}", exc_info=True)
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                logger.error("Too many consecutive errors. Shutting down...")
                sys.exit(1)
            continue

if __name__ == "__main__":
    main()
