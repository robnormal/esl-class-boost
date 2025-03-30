import os
import json
import logging
import boto3
import tempfile
from paragraph_extractor import TextExtractor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AWS clients
sqs = boto3.client('sqs')
s3 = boto3.client('s3')

# Configuration
QUEUE_URL = os.environ['PARAGRAPHS_QUEUE_URL']
SUBMISSIONS_BUCKET = os.environ['SUBMISSIONS_BUCKET']
PARAGRAPHS_BUCKET = os.environ['PARAGRAPHS_BUCKET']

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

def process_message(message):
    """Process a single SQS message."""
    try:
        # Parse the S3 event from the message
        body = json.loads(message['Body'])
        for record in body['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            logger.info(f"Processing file: {key} from bucket: {bucket}")
            
            # Download the file
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
                
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise

def main():
    """Main function to poll SQS queue."""
    logger.info("Starting paragraphs service...")
    
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
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        # Don't delete the message if processing failed
                        continue
                        
        except Exception as e:
            logger.error(f"Error polling queue: {e}")
            continue

if __name__ == "__main__":
    main()
