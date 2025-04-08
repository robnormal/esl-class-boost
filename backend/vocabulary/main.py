###
# Load environment variables before other code
#
# Do *NOT* load custom code before load_dotenv(), or else the env variables might not be loaded
###
from decimal import Decimal
from typing import Dict

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
from common.constants import SUBMISSIONS_TABLE, VOCABULARY_QUEUE, VOCABULARY_TABLE, \
    DYNAMODB_MAX_BATCH_SIZE
from common.envvar import environment
from common.logger import logger
from common.upload_notification import poll_sqs_for_s3_file_forever, S3Upload
from common.sqs_client import sqs_client
from nlp_word_extraction import parse_paragraphs, WordFromText

# Configuration
PARAGRAPHS_BUCKET = environment.require('PARAGRAPHS_BUCKET')

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
submissions_table = dynamodb.Table(SUBMISSIONS_TABLE)
queue_client = sqs_client.for_queue(VOCABULARY_QUEUE)

def word_db_record(user_id, submission_id, word_obj: WordFromText) -> Dict[str, str|int|float]:
    # composite sort key: "#VOCAB#<submission id>#<paragraph number>#word"
    submission_paragraph_word = f"#VOCAB#{submission_id}#{word_obj.first_paragraph}#{word_obj.word}"

    # Current timestamp for created_at field
    created_at = int(time.time())

    return {
        'user_id': user_id,
        'submission_paragraph_word': submission_paragraph_word,
        'word': word_obj.word,
        'frequency': Decimal(str(word_obj.language_frequency)), # Dynamo supports Decimal, not float
        'paragraph_index': word_obj.first_paragraph,
        'count': word_obj.count,
        'created_at': created_at
    }


def process_record(s3_upload: S3Upload):
    with open(s3_upload.tmp_file_path, 'r', encoding='utf-8', errors='replace') as file:
        paragraphs = json.load(file)

    words = parse_paragraphs(paragraphs)
    user_id = s3_upload.user_id
    submission_id = s3_upload.file_hash

    logger.info(f"Processing {len(words)} vocabulary words for submission {submission_id}")

    # Prepare batch write items
    items_to_write = []
    for word_obj in words:
        record = word_db_record(user_id, submission_id, word_obj)
        items_to_write.append({'PutRequest': {'Item': record}})

    # Process items in batches
    for i in range(0, len(items_to_write), DYNAMODB_MAX_BATCH_SIZE):
        batch = items_to_write[i:i + DYNAMODB_MAX_BATCH_SIZE]
        dynamodb.batch_write_item(RequestItems={VOCABULARY_TABLE: batch})
        logger.info(f"Successfully wrote batch of {len(batch)} items")

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
        process_record(s3_upload)

if __name__ == "__main__":
    main()
