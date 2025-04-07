import json
import sys
import os
import tempfile
from contextlib import contextmanager
import boto3

from common.logger import logger
from sqs_client import QueueClient

sqs = boto3.client('sqs')
s3 = boto3.client('s3')

@contextmanager
def poll_sqs_for_s3_file(queue_client: QueueClient):
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
            message = json.loads(msg['Body'])

            for record in message.get('Records', []):
                if record.get('eventName') != 'ObjectCreated:Put':
                    continue

                bucket = record['s3']['bucket']['name']
                key = record['s3']['object']['key']
                filename = key.split('/')[-1]
                logger.info(f"S3 bucket {bucket} key {key}")

                with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as tmp:
                    logger.info('Downloading...')
                    s3.download_file(bucket, key, tmp.name)
                    tmp_path = tmp.name
                    logger.info(f"Downloaded to {tmp_path}")

                try:
                    yield tmp_path, bucket, key, message
                finally:
                    os.remove(tmp_path)

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
            with poll_sqs_for_s3_file(queue_client) as poll_result:
                yield poll_result
            consecutive_errors = 0  # Reset error counter on success

        except Exception as e:
            logger.error(f"Error polling queue: {e}", exc_info=True)
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                logger.error("Too many consecutive errors. Shutting down...")
                sys.exit(1)
            continue
