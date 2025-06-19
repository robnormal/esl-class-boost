import pytest
from moto import mock_aws
import os
import boto3
from common.summary_repo import SummaryRepo, NewSummary, Summary
from common.constants import SUMMARIES_TABLE

@pytest.fixture(scope="module")
@mock_aws
def aws_credentials():
    """Mocked AWS Credentials for boto3."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    yield
    # Clean up
    del os.environ['AWS_ACCESS_KEY_ID']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    del os.environ['AWS_SECURITY_TOKEN']
    del os.environ['AWS_SESSION_TOKEN']
    del os.environ['AWS_DEFAULT_REGION']

@pytest.fixture(scope="module")
def dynamodb_resource(aws_credentials):
    # Set up the mock DynamoDB environment with module scope
    return boto3.resource('dynamodb', region_name='us-east-1')

@pytest.fixture(scope="module")
def dynamodb_table(dynamodb_resource):
    existing_tables = dynamodb_resource.meta.client.list_tables()['TableNames']
    if SUMMARIES_TABLE in existing_tables:
        return dynamodb_resource.Table(SUMMARIES_TABLE)

    # Create the table once
    table = dynamodb_resource.create_table(
        TableName=SUMMARIES_TABLE,
        KeySchema=[
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'submission_paragraph', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'user_id', 'AttributeType': 'N'},
            {'AttributeName': 'submission_paragraph', 'AttributeType': 'S'}
        ],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )
    table.meta.client.get_waiter('table_exists').wait(
        TableName=SUMMARIES_TABLE,
        WaiterConfig={
            'Delay': 1,
            'MaxAttempts': 10
        }
    )
    return table

@pytest.fixture(scope="function")
def clear_table(dynamodb_table):
    # Clear all items from the table before each test
    scan = dynamodb_table.scan()
    with dynamodb_table.batch_writer() as batch:
        for item in scan['Items']:
            batch.delete_item(
                Key={
                    'user_id': item['user_id'],
                    'submission_paragraph': item['submission_paragraph']
                }
            )
    return dynamodb_table

@pytest.fixture(scope="function")
def summary_repo(clear_table):
    # Create a SummaryRepo instance using the cleared table
    return SummaryRepo(clear_table)


def test_record_from_item(summary_repo):
    # Example test for record_from_item
    item = {
        'user_id': 1,
        'submission_paragraph': 'SUMMARY#sub1#1',
        'paragraph_start': 'Once upon a time',
        'summary': 'A short summary',
        'created_at': 1234567890
    }
    summary = summary_repo.record_from_item(item)
    assert summary is not None
    assert summary.user_id == 1
    assert summary.submission_id == 'sub1'
    assert summary.paragraph_number == 1
    assert summary.paragraph_start == 'Once upon a time'
    assert summary.summary == 'A short summary'
    assert summary.created_at == 1234567890


def test_item_from_new_record_for_insert(summary_repo):
    new_summary = NewSummary(
        user_id=1,
        submission_id='sub1',
        paragraph_number=1,
        paragraph_start='Once upon a time',
        summary='A short summary'
    )
    item = summary_repo.item_from_new_record_for_insert(new_summary)
    assert item['user_id'] == 1
    assert item['submission_paragraph'] == 'SUMMARY#sub1#1'
    assert item['paragraph_start'] == 'Once upon a time'
    assert item['summary'] == 'A short summary'
    assert 'created_at' in item


def test_item_from_record(summary_repo):
    summary = Summary(
        user_id=1,
        submission_id='sub1',
        paragraph_number=1,
        paragraph_start='Once upon a time',
        summary='A short summary',
        created_at=1234567890
    )
    item = summary_repo.item_from_record(summary)
    assert item['user_id'] == 1
    assert item['submission_paragraph'] == 'SUMMARY#sub1#1'
    assert item['paragraph_start'] == 'Once upon a time'
    assert item['summary'] == 'A short summary'
    assert item['created_at'] == 1234567890


def test_create(dynamodb_table):
    summary_repo = SummaryRepo(dynamodb_table)
    new_summary = NewSummary(
        user_id=1,
        submission_id='sub1',
        paragraph_number=1,
        paragraph_start='Once upon a time',
        summary='A short summary'
    )
    item = summary_repo.create(new_summary)
    assert item['user_id'] == 1
    assert item['submission_paragraph'] == 'SUMMARY#sub1#1'
    assert item['paragraph_start'] == 'Once upon a time'
    assert item['summary'] == 'A short summary'
    assert 'created_at' in item


def test_save_many(dynamodb_table):
    summary_repo = SummaryRepo(dynamodb_table)
    new_summaries = [
        NewSummary(
            user_id=1,
            submission_id='sub1',
            paragraph_number=i,
            paragraph_start=f'Start {i}',
            summary=f'Summary {i}'
        ) for i in range(3)
    ]
    summary_repo.save_many(new_summaries)
    for i in range(3):
        response = summary_repo.table.get_item(
            Key={
                'user_id': 1,
                'submission_paragraph': f'SUMMARY#sub1#{i}'
            }
        )
        item = response.get('Item')
        assert item is not None
        assert item['paragraph_start'] == f'Start {i}'
        assert item['summary'] == f'Summary {i}'


def test_get_by_submission(dynamodb_table):
    summary_repo = SummaryRepo(dynamodb_table)
    # Insert some items first
    new_summaries = [
        NewSummary(
            user_id=1,
            submission_id='sub1',
            paragraph_number=i,
            paragraph_start=f'Start {i}',
            summary=f'Summary {i}'
        ) for i in range(3)
    ]
    summary_repo.save_many(new_summaries)

    # Test retrieval
    summaries = summary_repo.get_by_submission(1, 'sub1')
    assert len(summaries) == 3
    for i, summary in enumerate(summaries):
        assert summary.user_id == 1
        assert summary.submission_id == 'sub1'
        assert summary.paragraph_number == i
        assert summary.paragraph_start == f'Start {i}'
        assert summary.summary == f'Summary {i}'

# Additional tests for other methods can be added here following a similar pattern.
