import time
import boto3
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import Table

from common.constants import VOCABULARY_TABLE
from common.logger import logger

@dataclass
class BaseVocabularyWord:
    user_id: int
    submission_id: str
    paragraph_number: int
    word: str

@dataclass
class NewVocabularyWord(BaseVocabularyWord):
    pass

@dataclass
class VocabularyWord(BaseVocabularyWord):
    created_at: int = int(time.time())

class VocabularyWordRepo:
    def __init__(self, table: Table):
        self.table = table

    @staticmethod
    def record_from_item(item: Dict[str, Any]) -> Optional[VocabularyWord]:
        key_parts = item.get('submission_paragraph_word').split('#')
        if len(key_parts) != 4:
            return None
        _, submission_id, paragraph_number, word = key_parts

        return VocabularyWord(
            user_id=item.get('user_id'),
            submission_id=submission_id,
            paragraph_number=int(paragraph_number),
            word=item.get('word'),
            created_at=item.get('created_at'),
        )

    @staticmethod
    def _item_from_base_record(base_record: BaseVocabularyWord) -> Dict[str, Any]:
        key = f"VOCAB#{base_record.submission_id}#{base_record.paragraph_number}#{base_record.word}"
        return {
            'user_id': base_record.user_id,
            'submission_paragraph_word': key,
        }

    def item_from_new_record_for_insert(self, new_record: NewVocabularyWord) -> Dict[str, Any]:
        item = self._item_from_base_record(new_record)
        item.update({'created_at': int(time.time())})
        return item

    def item_from_record(self, record: VocabularyWord) -> Dict[str, Any]:
        item = self._item_from_base_record(record)
        item.update({'created_at': record.created_at})
        return item

    def create(self, new_vocabulary_word: NewVocabularyWord):
        item = self.item_from_new_record_for_insert(new_vocabulary_word)
        self.table.put_item(Item=item)
        return item

    def create_many(self, new_vocabulary_words: list[NewVocabularyWord]):
        items = []
        with self.table.batch_writer() as batch:
            for new_vocabulary_word in new_vocabulary_words:
                item = self.item_from_new_record_for_insert(new_vocabulary_word)
                batch.put_item(Item=item)
                items.append(item)

    def get_by_submission(self, user_id, submission_id) -> List[VocabularyWord]:
        response = self.table.query(
            KeyConditionExpression=Key('user_id').eq(user_id) &
                                   Key('submission_paragraph_word').begins_with(f"VOCAB#{submission_id}#")
        )

        vocabulary_words = []
        for item in response.get('Items', []):
            vocabulary_word = self.record_from_item(item)
            if vocabulary_word:
                vocabulary_words.append(vocabulary_word)
            else:
                logger.error(f"Invalid vocabulary_word {item.get('user_id')}/{item.get('submission_paragraph_word')}")
        return vocabulary_words

dynamodb = boto3.resource('dynamodb')
vocab_table = dynamodb.Table(VOCABULARY_TABLE)
vocabulary_word_repo = VocabularyWordRepo(vocab_table)
