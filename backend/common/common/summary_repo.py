import time
import boto3
from typing import List, Dict, Any
from dataclasses import dataclass
from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import Table

from common.constants import SUMMARIES_TABLE
from common.logger import logger

@dataclass
class BaseSummary:
    user_id: int
    submission_id: str
    paragraph_number: int
    paragraph_start: str
    summary: str

@dataclass
class NewSummary(BaseSummary):
    pass

@dataclass
class Summary(BaseSummary):
    created_at: int = int(time.time())

class SummaryRepo:
    def __init__(self, table: Table):
        self.table = table

    def record_from_item(self, item: Dict[str, Any]):
        key_parts = item.get('submission_paragraph').split('#')
        if len(key_parts) != 3:
            return None
        _, submission_id, paragraph_number = key_parts

        return Summary(
            user_id=item.get('user_id'),
            submission_id=submission_id,
            paragraph_number=int(paragraph_number),
            paragraph_start=item.get('paragraph_start'),
            summary=item.get('summary'),
            created_at=item.get('created_at'),
        )

    def _item_from_base_record(self, base_record: BaseSummary) -> Dict[str, Any]:
        return {
            'user_id': base_record.user_id,
            'submission_paragraph': f"SUMMARY#{base_record.submission_id}#{base_record.paragraph_number}",
            'paragraph_start': base_record.paragraph_start,
            'summary': base_record.summary,
        }

    def item_from_new_record_for_insert(self, new_record: NewSummary) -> Dict[str, Any]:
        item = self._item_from_base_record(new_record)
        item.update({'created_at': int(time.time())})
        return item

    def item_from_record(self, record: Summary) -> Dict[str, Any]:
        item = self._item_from_base_record(record)
        item.update({'created_at': record.created_at})
        return item

    def create(self, new_summary: NewSummary):
        item = self.item_from_new_record_for_insert(new_summary)
        self.table.put_item(Item=item)
        return item

    def save_many(self, new_summaries: list[NewSummary]):
        items = []
        with self.table.batch_writer() as batch:
            for new_summary in new_summaries:
                item = self.item_from_new_record_for_insert(new_summary)
                batch.put_item(Item=item)
                items.append(item)

    def get_by_submission(self, user_id, submission_id) -> List[Summary]:
        response = self.table.query(
            KeyConditionExpression=Key('user_id').eq(user_id) &
                                   Key('submission_paragraph').begins_with(f"SUMMARY#{submission_id}#")
        )

        summaries = []
        for item in response.get('Items', []):
            summary = self.record_from_item(item)
            if summary:
                summaries.append(summary)
            else:
                logger.error(f"Invalid summary {item.get('user_id')}/{item.get('submission_paragraph')}")
        return summaries

    def delete_by_submission(self, user_id, submission_id):
        response = self.table.query(
            KeyConditionExpression=Key('user_id').eq(user_id) &
                                   Key('submission_paragraph').begins_with(f"SUMMARY#{submission_id}#")
        )

        items_to_delete = response.get('Items', [])
        with self.table.batch_writer() as batch:
            for item in items_to_delete:
                batch.delete_item(
                    Key={
                        'user_id': item['user_id'],
                        'submission_paragraph': item['submission_paragraph']
                    }
                )

dynamodb = boto3.resource('dynamodb')
summaries_table = dynamodb.Table(SUMMARIES_TABLE)
summary_repo = SummaryRepo(summaries_table)
