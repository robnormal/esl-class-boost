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
from common.upload_notification import poll_sqs_for_s3_file_forever, S3Upload

from paragraph_extractor import extract_paragraphs
from common.sqs_client import sqs_client

# Configuration
SUBMISSIONS_BUCKET = environment.require('SUBMISSIONS_BUCKET')
PARAGRAPHS_BUCKET = environment.require('PARAGRAPHS_BUCKET')

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
submissions_table = dynamodb.Table(SUBMISSIONS_TABLE)
queue_client = sqs_client.for_queue(PARAGRAPHS_QUEUE)

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

def process_record(s3_upload: S3Upload):
    # File hash functions as the submission_id
    save_submission_to_db(s3_upload.file_hash, s3_upload.user_id)

    paragraphs = extract_paragraphs(s3_upload.tmp_file_path)

    # Upload paragraphs to paragraphs bucket
    output_key = f"{os.path.splitext(s3_upload.key)[0]}_paragraphs.json"
    upload_paragraphs(PARAGRAPHS_BUCKET, output_key, paragraphs)

    logger.info(f"Successfully processed {s3_upload.key} into {output_key}")

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

    for s3_upload in poll_sqs_for_s3_file_forever(queue_client, 5):
        logger.info(f"Processing file from bucket {s3_upload.bucket} with key {s3_upload.key}...")
        process_record(s3_upload)

if __name__ == "__main__":
    main()
