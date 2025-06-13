import sys
import os
import tempfile
from contextlib import contextmanager
from typing import Iterator

import boto3

from common.logger import logger
from common.sqs_client import QueueClient, records_from_sqs_message

sqs = boto3.client('sqs')
s3 = boto3.client('s3')


def submission_id_from_s3_key(key):
    """Extract user ID from S3 key format: uploads/{user_id}/{file_hash}.txt"""
    parts = key.split('/')
    if len(parts) >= 3 and parts[0] == 'uploads':
        user_id = parts[1]
        submission_id = os.path.splitext(parts[2])[0]
        return user_id, submission_id
    else:
        raise ValueError(f"Invalid S3 key format: {key}")

class S3Upload:
    def __init__(self, sqs_record):
        self.record = sqs_record
        self.bucket = sqs_record['s3']['bucket']['name']
        self.key = sqs_record['s3']['object']['key']
        self.filename = self.key.split('/')[-1]
        self.user_id, self.file_hash = submission_id_from_s3_key(self.key)

        logger.info(f"S3 bucket {self.bucket} key {self.key}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{self.filename}") as tmp:
            s3.download_file(self.bucket, self.key, tmp.name)
            self.tmp_file_path = tmp.name
            logger.info(f"Downloaded to {self.tmp_file_path}")

    def __del__(self):
        os.remove(self.tmp_file_path)

@contextmanager
def poll_sqs_for_s3_file(queue_client: QueueClient) -> Iterator[S3Upload]:
    while True:
        logger.info('Requesting now...')
        messages = queue_client.receive_messages(max_messages=1, wait_time_seconds=10)
        if not messages:
            logger.info('No messages found, requesting again...')
            continue

        msg = messages[0]
        logger.info(msg)
        receipt_handle = msg['ReceiptHandle']

        try:
            for record in records_from_sqs_message(msg):
                if record.get('eventName') != 'ObjectCreated:Put':
                    continue

                upload = S3Upload(record)
                yield upload

                queue_client.delete_message(receipt_handle)
                return  # Exit after processing one file

        except Exception as e:
            print(f"Error handling message: {e}")
            continue

def poll_sqs_for_s3_file_forever(queue_client: QueueClient, max_consecutive_errors: int):
    consecutive_errors = 0

    while True:
        try:
            logger.info("Receiving messages from SQS...")
            with poll_sqs_for_s3_file(queue_client) as s3_upload:
                yield s3_upload
            consecutive_errors = 0  # Reset error counter on success

        except Exception as e:
            logger.error(f"Error polling queue: {e}", exc_info=True)
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                logger.error("Too many consecutive errors. Shutting down...")
                sys.exit(1)
            continue
