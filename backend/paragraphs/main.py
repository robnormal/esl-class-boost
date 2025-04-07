import os
import json
import signal
import sys
import time
import boto3

###
# Load environment variables before other code
#
# Do *NOT* load custom code before load_dotenv(), or else the env variables might not be loaded
###
from dotenv import load_dotenv
load_dotenv()

###
# Load custom code after this point
###
from common.constants import PARAGRAPHS_QUEUE, SUBMISSIONS_TABLE
from common.envvar import environment
from common.logger import logger
from common.s3_upload_from_sqs_notification import poll_sqs_for_s3_file_forever
from paragraph_extractor import extract_paragraphs
from sqs_client import sqs_client

# Configuration
SUBMISSIONS_BUCKET = environment.require('SUBMISSIONS_BUCKET')
PARAGRAPHS_BUCKET = environment.require('PARAGRAPHS_BUCKET')

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
submissions_table = dynamodb.Table(SUBMISSIONS_TABLE)
queue_client = sqs_client.for_queue(PARAGRAPHS_QUEUE)

def extract_submission_data_from_key(key):
    """Extract user ID from S3 key format: uploads/{user_id}/{file_hash}.txt"""
    parts = key.split('/')
    if len(parts) >= 3 and parts[0] == 'uploads':
        return parts[1], parts[2]
    else:
        raise ValueError(f"Invalid S3 key format: {key}")

def save_submission_to_db(submission_id, user_id):
    logger.info(f"Saving submission {submission_id} for user {user_id} to DynamoDB...")
    """Write submission record to DynamoDB."""
    submissions_table.put_item(Item={
        'submission_id': submission_id,
        'user_id': user_id,
        'created_at': int(time.time())
    })

def upload_paragraphs(bucket, key, paragraphs):
    """Upload paragraphs to S3."""
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(paragraphs),
        ContentType='application/json'
    )

def process_record(temp_file, key):
    user_id, submission_id = extract_submission_data_from_key(key)
    save_submission_to_db(submission_id, user_id)

    paragraphs = extract_paragraphs(temp_file)

    # Upload paragraphs to paragraphs bucket
    output_key = f"{os.path.splitext(key)[0]}_paragraphs.json"
    upload_paragraphs(PARAGRAPHS_BUCKET, output_key, paragraphs)

    logger.info(f"Successfully processed {key} into {output_key}")

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

    for poll_result in poll_sqs_for_s3_file_forever(queue_client, 5):
        temp_file_path, bucket, key, _msg = poll_result
        logger.info(f"Processing file from bucket {bucket} with key {key}...")
        process_record(temp_file_path, key)

if __name__ == "__main__":
    main()
