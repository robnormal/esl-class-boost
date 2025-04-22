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
from common.constants import SUMMARIES_QUEUE, SUMMARIES_PER_SUBMISSION_LIMIT, PARAGRAPH_INTRO_WORDS
from common.envvar import environment
from common.logger import logger
from common.upload_notification import poll_sqs_for_s3_file_forever, S3Upload
from common.sqs_client import sqs_client
from common.summary_repo import NewSummary, summary_repo
from paragraph_summarizer import summarize_paragraphs

# Configuration
PARAGRAPHS_BUCKET = environment.require('PARAGRAPHS_BUCKET')

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
queue_client = sqs_client.for_queue(SUMMARIES_QUEUE)

def paragraph_should_be_summarized(paragraph: str) -> bool:
    return len(paragraph.strip()) >= 300

def process_record(s3_upload: S3Upload):
    user_id = s3_upload.user_id
    submission_id = s3_upload.file_hash
    with open(s3_upload.tmp_file_path, 'r', encoding='utf-8', errors='replace') as file:
        paragraphs = json.load(file)

    # Process each paragraph and save its summary immediately
    summaries_count = 0

    logger.info(f"Received {len(paragraphs)} paragraphs for submission {submission_id}")
    summaries = summarize_paragraphs(paragraphs)
    for i, summary_text in enumerate(summaries):
        # Save each summary immediately instead of batching
        new_summary = NewSummary(
            user_id=user_id,
            submission_id=submission_id,
            paragraph_number=i,
            paragraph_start=' '.join(paragraphs[i].split()[:PARAGRAPH_INTRO_WORDS]),
            summary=summary_text,
        )
        summary_repo.create(new_summary)
        summaries_count += 1

        if summaries_count > SUMMARIES_PER_SUBMISSION_LIMIT:
            logger.error(f"Limiting submission {s3_upload.file_hash} to {SUMMARIES_PER_SUBMISSION_LIMIT} summaries")
            break

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
