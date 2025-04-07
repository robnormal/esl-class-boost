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
from common.constants import SUBMISSIONS_TABLE, VOCABULARY_QUEUE
from common.envvar import environment
from common.logger import logger
from common.upload_notification import poll_sqs_for_s3_file_forever, S3Upload
from sqs_client import sqs_client

# Configuration
PARAGRAPHS_BUCKET = environment.require('PARAGRAPHS_BUCKET')

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
submissions_table = dynamodb.Table(SUBMISSIONS_TABLE)
queue_client = sqs_client.for_queue(VOCABULARY_QUEUE)


# TODO: implement
def process_record(s3_upload: S3Upload):
    pass

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
