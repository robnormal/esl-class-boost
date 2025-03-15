import pytest
import openai
from unittest.mock import patch, MagicMock
from paragraph_summarizer import summarize_paragraph

@pytest.fixture
def mock_openai_client():
    """Fixture to mock the OpenAI client globally."""
    with patch("paragraph_summarizer.client") as mock_client:
        mock_chat = MagicMock()
        mock_client.chat.completions.create = mock_chat
        yield mock_chat

def long_paragraph():
    return "abcd " * 100 # 500 characters

def test_summarize_paragraph_success(mock_openai_client):
    """Test summarizing a paragraph successfully."""
    mock_openai_client.return_value.choices = [
        MagicMock(message=MagicMock(content="This is a summary."))
    ]

    summary = summarize_paragraph(long_paragraph(), subject="history")

    assert summary == "This is a summary."
    mock_openai_client.assert_called_once()

def test_summarize_short_paragraph(mock_openai_client):
    """Test that short paragraphs are returned unchanged."""
    paragraph = "This is short."
    summary = summarize_paragraph(paragraph)

    assert summary == paragraph
    mock_openai_client.assert_not_called()  # API should not be called for short paragraphs

def test_summarize_paragraph_invalid_response(mock_openai_client):
    """Test handling an invalid response from OpenAI API."""
    mock_openai_client.return_value.choices = []  # Simulate empty API response

    with pytest.raises(ValueError, match="Invalid response structure received from OpenAI API."):
        summarize_paragraph(long_paragraph(), subject="history")

def test_summarize_paragraph_openai_error(mock_openai_client):
    """Test handling an OpenAI API error."""
    mock_openai_client.side_effect = openai.OpenAIError("API failure")

    with pytest.raises(openai.OpenAIError, match="API failure"):
        summarize_paragraph(long_paragraph(), subject="history")

def test_summarize_paragraph_unexpected_error(mock_openai_client):
    """Test handling of unexpected errors."""
    mock_openai_client.side_effect = Exception("Unexpected issue")

    with pytest.raises(Exception, match="Unexpected issue"):
        summarize_paragraph(long_paragraph(), subject="history")
