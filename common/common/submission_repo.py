import time
from enum import Enum

import boto3
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from boto3.dynamodb.conditions import Key

from common.constants import SUBMISSIONS_TABLE
from common.logger import logger

class SubmissionState(Enum):
    PENDING = 0
    PROCESSING = 1
    PARAGRAPHED = 2

@dataclass
class BaseSubmission:
    user_id: str
    submission_id: str
    state: SubmissionState
    filename: Optional[str] = None
    paragraph_count: Optional[int] = None

    def s3_base_path(self) -> str:
        return f"uploads/{self.user_id}/{self.submission_id}"

@dataclass
class NewSubmission(BaseSubmission):
    pass

@dataclass
class Submission(BaseSubmission):
    created_at: int = int(time.time())

class SubmissionRepo:
    def __init__(self, table):
        self.table = table

    def record_from_item(self, item: Dict[str, Any]) -> Submission|None:
        user_id: str = str(item.get('user_id', ''))
        submission_id = str(item.get('submission_id', ''))
        if not user_id or not submission_id:
            return None

        try:
            return Submission(
                user_id=user_id,
                submission_id=submission_id,
                state=SubmissionState(item.get('state')),
                filename=item.get('filename'),
                paragraph_count=item.get('paragraph_count'),
                created_at=item.get('created_at'),
            )
        except Exception as e:
            logger.error(f"Bad item in submissions table: {item.get('submission_id', None)}")
            return None

    def _item_from_base_record(self, base_record: BaseSubmission) -> Dict[str, Any]:
        item = {
            'user_id': base_record.user_id,
            'submission_id': base_record.submission_id,
            'state': base_record.state.value,
        }

        # Add optional fields if they exist
        if base_record.filename:
            item['filename'] = base_record.filename
        if base_record.paragraph_count is not None:
            item['paragraph_count'] = base_record.paragraph_count

        return item

    def item_from_new_record_for_insert(self, new_record: NewSubmission) -> Dict[str, Any]:
        item = self._item_from_base_record(new_record)
        item.update({'created_at': int(time.time())})
        return item

    def item_from_record(self, record: Submission) -> Dict[str, Any]:
        item = self._item_from_base_record(record)
        item.update({'created_at': record.created_at})
        return item

    def create(self, new_submission: NewSubmission) -> Dict[str, Any]:
        """Creates a new submission record in DynamoDB."""
        item = self.item_from_new_record_for_insert(new_submission)
        logger.info(f"Creating submission {new_submission.submission_id} for user {new_submission.user_id}")
        self.table.put_item(Item=item)
        return item

    def get_by_id(self, user_id: str, submission_id: str) -> Submission|None:
        """Find a submission by its user_id and submission_id."""
        response = self.table.get_item(
            Key={
                'user_id': user_id,
                'submission_id': submission_id
            }
        )

        item = response.get('Item')
        if not item:
            return None

        return self.record_from_item(item)

    def get_by_user(self, user_id: str) -> List[Submission]:
        """Find all submissions for a given user."""
        response = self.table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )

        submissions = []
        for item in response.get('Items', []):
            submission = self.record_from_item(item)
            if submission:
                submissions.append(submission)

        return submissions

    def get_by_filename(self, user_id: str, filename: str) -> List[Submission]:
        """Find submissions by filename for a given user."""
        response = self.table.query(
            KeyConditionExpression=Key('user_id').eq(user_id),
            FilterExpression='filename = :filename',
            ExpressionAttributeValues={
                ':filename': filename
            }
        )

        submissions = []
        for item in response.get('Items', []):
            submission = self.record_from_item(item)
            submissions.append(submission)

        return submissions

    def update_state(self, user_id: str, submission_id: str, new_state: str) -> None:
        """Update the state of an existing submission."""
        logger.info(f"Updating submission {submission_id} state to {new_state}")
        self.table.update_item(
            Key={
                'user_id': user_id,
                'submission_id': submission_id
            },
            UpdateExpression="SET #state = :new_state",
            ExpressionAttributeNames={
                '#state': 'state'
            },
            ExpressionAttributeValues={
                ':new_state': new_state
            }
        )

    def update_paragraph_count(self, user_id: str, submission_id: str, paragraph_count: int) -> None:
        """Update the paragraph_count of an existing submission."""
        logger.info(f"Updating submission {submission_id} with paragraph_count {paragraph_count}")
        self.table.update_item(
            Key={
                'user_id': user_id,
                'submission_id': submission_id
            },
            UpdateExpression="SET paragraph_count = :paragraph_count",
            ExpressionAttributeValues={
                ':paragraph_count': paragraph_count
            }
        )

    def delete(self, user_id: str, submission_id: str) -> None:
        """Delete a submission record."""
        logger.info(f"Deleting submission {submission_id} for user {user_id}")
        self.table.delete_item(
            Key={
                'user_id': user_id,
                'submission_id': submission_id
            }
        )

# Initialize the repo with the DynamoDB table
dynamodb = boto3.resource('dynamodb')
submissions_table = dynamodb.Table(SUBMISSIONS_TABLE)
submission_repo = SubmissionRepo(submissions_table)
