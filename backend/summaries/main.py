###
# Load environment variables before other code
#
# Do *NOT* load custom code before load_dotenv(), or else the env variables might not be loaded
###
from time import sleep
from typing import Tuple

from dotenv import load_dotenv
load_dotenv()

###
# Load dependencies after this point
###
import json
import signal
import sys
import boto3
from common.constants import SUMMARIES_QUEUE, SUMMARIES_PER_SUBMISSION_LIMIT, PARAGRAPH_INTRO_WORDS
from common.envvar import environment
from common.logger import logger
from common.upload_notification import poll_sqs_for_s3_file_forever, S3Upload
from common.sqs_client import sqs_client
from common.summary_repo import NewSummary, summary_repo
from paragraph_summarizer import summarize_paragraph

# Configuration
PARAGRAPHS_BUCKET = environment.require('PARAGRAPHS_BUCKET')

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
queue_client = sqs_client.for_queue(SUMMARIES_QUEUE)

def filter_paragraphs(paragraphs: list[str]) -> Tuple[list[str], bool]:
    long_paragraphs = [paragraph for paragraph in paragraphs if len(paragraph.strip()) >= 300]
    count = len(long_paragraphs)
    if count <= SUMMARIES_PER_SUBMISSION_LIMIT:
        return long_paragraphs, True
    else:
        return long_paragraphs[:SUMMARIES_PER_SUBMISSION_LIMIT], False

def process_record(s3_upload: S3Upload):
    with open(s3_upload.tmp_file_path, 'r', encoding='utf-8', errors='replace') as file:
        all_paragraphs = json.load(file)

    paragraphs, all_included = filter_paragraphs(all_paragraphs)
    if not all_included:
        logger.error(f"Submission {s3_upload.file_hash} has {len(all_paragraphs)} paragraphs. Limiting to {SUMMARIES_PER_SUBMISSION_LIMIT}.")

    user_id = s3_upload.user_id
    submission_id = s3_upload.file_hash

    # Process each paragraph and save its summary immediately
    summaries_count = 0

    logger.info(f"Summarizing {len(paragraphs)} paragraphs for submission {submission_id}")
    for i, paragraph in enumerate(paragraphs):
        summary_text = summarize_paragraph(paragraph)
        if not summary_text:
            logger.error(f"No summary found for submission {submission_id}, paragraph {i}")
            continue

        # Save each summary immediately instead of batching
        new_summary = NewSummary(
            user_id=user_id,
            submission_id=submission_id,
            paragraph_number=i,
            paragraph_start=' '.join(paragraph.split()[:PARAGRAPH_INTRO_WORDS]),
            summary=summary_text,
        )
        summary_repo.create(new_summary)
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
        try:
            process_record(s3_upload)
        except Exception as e:
            logger.error(f"Error processing file {s3_upload.key}: {e}", exc_info=True)

if __name__ == "__main__":
    main()
