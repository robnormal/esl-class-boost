import json
import tempfile
import os
from unittest.mock import patch, MagicMock
import pytest
from main import process_message, PARAGRAPHS_BUCKET


@pytest.fixture
def mock_sqs_message():
    return {
        'Body': json.dumps({
            'Records': [{
                's3': {
                    'bucket': {'name': 'input-bucket'},
                    'object': {'key': 'uploads/test_user/abc123.txt'}
                }
            }]
        }),
        'ReceiptHandle': 'mock-receipt-handle'
    }


@patch('main.upload_paragraphs')
@patch('main.TextExtractor')
@patch('main.download_file')
@patch('main.write_to_dynamodb')
def test_process_message_success(
        mock_write_dynamo,
        mock_download_file,
        mock_text_extractor_class,
        mock_upload_paragraphs,
        mock_sqs_message
):
    # We're mocking the download function, so we have to create the file anyway, so it can be
    # deleted by the cleanup logic in main.process_record
    temp_file_path = tempfile.NamedTemporaryFile(delete=False).name
    mock_download_file.return_value = temp_file_path

    # Mock the TextExtractor behavior
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = "This is a test.\n\nThis is paragraph two."
    mock_extractor.extract_paragraphs.return_value = [
        "This is a test.",
        "This is paragraph two."
    ]
    mock_text_extractor_class.return_value = mock_extractor

    process_message(mock_sqs_message)

    mock_download_file.assert_called_once_with('input-bucket', 'uploads/test_user/abc123.txt')
    mock_text_extractor_class.assert_called_once_with(temp_file_path)
    mock_upload_paragraphs.assert_called_once_with(
        PARAGRAPHS_BUCKET,
        'uploads/test_user/abc123_paragraphs.json',
        ["This is a test.", "This is paragraph two."]
    )

    mock_write_dynamo.assert_called_once_with('abc123.txt', 'test_user')
    assert not os.path.exists(temp_file_path), "Temporary file was not deleted"
