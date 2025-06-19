import os
import json
import signal
import sys
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
from common.submission_repo import submission_repo, SubmissionState

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

def upload_paragraphs(bucket, key, paragraphs):
    """Upload paragraphs to S3."""
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(paragraphs),
        ContentType='application/json'
    )

def process_record(s3_upload: S3Upload):
    logger.info(f"Processing file {s3_upload.user_id}/{s3_upload.file_hash}")
    # File hash functions as the submission_id
    submission_repo.update_state(
        s3_upload.user_id,
        s3_upload.file_hash,
        SubmissionState.RECEIVED.value
    )
    paragraphs = extract_paragraphs(s3_upload.tmp_file_path)

    # Upload paragraphs to paragraphs bucket
    output_key = f"{os.path.splitext(s3_upload.key)[0]}.json"
    upload_paragraphs(PARAGRAPHS_BUCKET, output_key, paragraphs)
    submission_repo.update_paragraph_count(
        s3_upload.user_id,
        s3_upload.file_hash,
        len(paragraphs)
    )

    submission_repo.update_state(
        s3_upload.user_id,
        s3_upload.file_hash,
        SubmissionState.PARAGRAPHED.value
    )

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
        try:
            process_record(s3_upload)
        except Exception as e:
            logger.error(f"Error processing file {s3_upload.key}: {e}", exc_info=True)


if __name__ == "__main__":
    main()
