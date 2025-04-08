###
# Load environment variables before other code
#
# Do *NOT* load custom code before load_dotenv(), or else the env variables might not be loaded
###
from dotenv import load_dotenv
load_dotenv()

###
# Load dependencies after this point
###
import json
import signal
import sys
import boto3
import time
from common.constants import SUMMARIES_QUEUE, SUMMARIES_TABLE, SUMMARIES_PER_SUBMISSION_LIMIT
from common.envvar import environment
from common.logger import logger
from common.upload_notification import poll_sqs_for_s3_file_forever, S3Upload
from common.sqs_client import sqs_client
from paragraph_summarizer import summarize_paragraph


# Configuration
PARAGRAPHS_BUCKET = environment.require('PARAGRAPHS_BUCKET')

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
summaries_table = dynamodb.Table(SUMMARIES_TABLE)
queue_client = sqs_client.for_queue(SUMMARIES_QUEUE)


def process_record(s3_upload: S3Upload):
    with open(s3_upload.tmp_file_path, 'r', encoding='utf-8', errors='replace') as file:
        paragraphs = json.load(file)

    user_id = s3_upload.user_id
    submission_id = s3_upload.file_hash

    paragraph_count = len(paragraphs)
    if paragraph_count > SUMMARIES_PER_SUBMISSION_LIMIT:
        logger.error(f"Submission {submission_id} has {paragraph_count} paragraphs. Limiting to {SUMMARIES_PER_SUBMISSION_LIMIT}.")
        paragraphs = paragraphs[:SUMMARIES_PER_SUBMISSION_LIMIT]

    # Process each paragraph and save its summary immediately
    summaries_count = 0

    logger.info(f"Summarizing {len(paragraphs)} paragraphs for submission {submission_id}")
    for i, paragraph in enumerate(paragraphs):
        summary = summarize_paragraph(paragraph)
        if not summary:
            logger.error(f"No summary found for submission {submission_id}, paragraph {i}")
            continue

        # Create a record for the summary
        summary_record = {
            'user_id': user_id,
            'submission_paragraph': f"#SUMMARY#{submission_id}#{i}",
            'summary': summary,
            'created_at': int(time.time())
        }

        # Save each summary immediately instead of batching
        summaries_table.put_item(Item=summary_record)
        summaries_count += 1

    logger.info(f"Successfully saved {summaries_count} paragraph summaries for submission {submission_id}")


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
