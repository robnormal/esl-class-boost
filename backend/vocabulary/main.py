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
from common.constants import VOCABULARY_QUEUE
from common.envvar import environment
from common.logger import logger
from common.upload_notification import poll_sqs_for_s3_file_forever, S3Upload
from common.sqs_client import sqs_client
from common.vocabulary_word_repo import NewVocabularyWord, vocabulary_word_repo
from nlp_word_extraction import parse_paragraphs

# Configuration
PARAGRAPHS_BUCKET = environment.require('PARAGRAPHS_BUCKET')

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
queue_client = sqs_client.for_queue(VOCABULARY_QUEUE)

def process_record(s3_upload: S3Upload):
    with open(s3_upload.tmp_file_path, 'r', encoding='utf-8', errors='replace') as file:
        paragraphs = json.load(file)

    words = parse_paragraphs(paragraphs)
    user_id = s3_upload.user_id
    submission_id = s3_upload.file_hash

    logger.info(f"Processing {len(words)} vocabulary words for submission {submission_id}")

    # Prepare batch write items
    new_vocabulary_words = []
    for word_obj in words:
        record = NewVocabularyWord(
            user_id=user_id,
            submission_id=submission_id,
            paragraph_number=word_obj.first_paragraph,
            word=word_obj.word,
        )
        new_vocabulary_words.append(record)

    vocabulary_word_repo.create_many(new_vocabulary_words)
    logger.info(f"Successfully saved {len(words)} vocabulary words for submission {submission_id}")


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
