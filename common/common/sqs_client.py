import boto3
import logging
import json
from typing import Optional, Dict, Any, List, Generator
from common.envvar import environment

logger = logging.getLogger(__name__)

class SQSClient:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            endpoint_url = environment.require('AWS_ENDPOINT_URL') if environment.require('IS_LOCAL') else None
            self._client = boto3.client(
                'sqs',
                region_name=environment.require('AWS_REGION'),
                endpoint_url=endpoint_url,
                aws_access_key_id=environment.require('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=environment.require('AWS_SECRET_ACCESS_KEY')
            )

        return self._client

    def for_queue(self, queue_name: str) -> 'QueueClient':
        """Get a QueueClient instance for a specific queue."""
        return QueueClient(queue_name, self._get_client())

class QueueClient:
    def __init__(self, queue_name: str, client: boto3.client):
        self.queue_name = queue_name
        self.client = client
        self._queue_url = None

    @property
    def queue_url(self) -> str:
        """Get or create the queue URL. Throws error if queue does not exist."""
        if self._queue_url is None:
            self._queue_url = self.client.get_queue_url(QueueName=self.queue_name)['QueueUrl']
        return self._queue_url

    def send_message(self, message_body: str, message_attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a message to the queue."""
        params = {
            'QueueUrl': self.queue_url,
            'MessageBody': message_body
        }
        if message_attributes:
            params['MessageAttributes'] = message_attributes
        return self.client.send_message(**params)

    def receive_messages(self, max_messages: int = 1, wait_time_seconds: int = 20) -> List[Dict[str, Any]]:
        """Receive messages from the queue."""
        response = self.client.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_time_seconds
        )
        return response.get('Messages', [])

    def delete_message(self, receipt_handle: str) -> Dict[str, Any]:
        """Delete a message from the queue using its receipt handle."""
        return self.client.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=receipt_handle
        )

    def purge_queue(self) -> Dict[str, Any]:
        """Purge all messages from the queue."""
        return self.client.purge_queue(QueueUrl=self.queue_url)

    def change_message_visibility(self, receipt_handle: str, visibility_timeout: int) -> Dict[str, Any]:
        """Change the visibility timeout of a message."""
        return self.client.change_message_visibility(
            QueueUrl=self.queue_url,
            ReceiptHandle=receipt_handle,
            VisibilityTimeout=visibility_timeout
        )

def records_from_sqs_message(sqs_message: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """
    Extract records from an SQS message, handling both direct SQS messages and SNS notifications.

    Args:
        sqs_message: The message received from SQS

    Returns:
        Generator of records from the message

    Raises:
        KeyError: If the SQS message is missing required fields
        json.JSONDecodeError: If the message body cannot be parsed as JSON
        ValueError: If the message format is invalid
    """
    message = json.loads(sqs_message['Body'])

    if 'TopicArn' in message and message.get('Type') == 'Notification':
        try:
            message = json.loads(message['Message'])
        except json.JSONDecodeError:
            logger.error(f"Expected message from SNS topic, got `{message}`")
            return

    for record in message.get('Records', []):
        yield record


sqs_client = SQSClient()
