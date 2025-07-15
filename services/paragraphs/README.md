# Paragraphs Service

A microservice that extracts paragraphs from documents of various formats as
part of the ESL Class Boost pipeline. It processes uploaded documents and converts them into
JSON arrays of UTF-8 paragraph strings.

## Overview

The service:
- Polls SQS for new upload notifications
- Reads files uploaded to an S3 bucket
- Extracts text in the form of paragraphs from uploaded documents
- Uses OCR to extract text from images
- Supports multiple file formats (PDF, Word, RTF, HTML, images, plain text)
- Stores extracted paragraphs as JSON in S3
- Updates submission status in DynamoDB

```
SQS Queue → File Download → Paragraph Extraction → S3 Upload → DynamoDB Update
```

## Installation

### Prerequisites

- Python 3.8+
- Poetry
- AWS credentials
- Google Cloud credentials (for PDF processing and OCR)

### Setup

1. Install dependencies:
   ```bash
   cd services/paragraphs
   poetry install
   ```
2. Copy `.env.EXAMPLE` to `.env` and update variables for your environment.
3. Set up Google Cloud Document AI:
   - Create a Document AI processor in Google Cloud Console
   - Download service account credentials
   - Set the credentials as described in `.env.EXAMPLE`

## Usage

### Running the Service

```bash
cd services/paragraphs
poetry run python src/main.py
```

The service will:
1. Connect to the configured SQS queue
2. Poll for file upload notifications
3. Process files and extract paragraphs
4. Upload results to S3 and update DynamoDB

### Manual Processing

To use the paragraph extraction functionality directly:

```python
from paragraph_extractor import extract_paragraphs

# Extract paragraphs from a file
paragraphs = extract_paragraphs('/path/to/document.pdf', min_length=100)
print(f"Extracted {len(paragraphs)} paragraphs")
```

### Testing

Run the test suite:
```bash
cd services/paragraphs
poetry run pytest tests/
```

### Paragraph Extraction Settings

- **Minimum Length**: Paragraphs shorter than 100 characters are filtered out by default
- **Text Cleaning**: Normalizes whitespace and removes excessive line breaks
- **Format Handling**: Each file type has specialized extraction logic

## File Processing Details

### PDF Processing
- Uses Google Cloud Document AI Layout Parser
- Handles complex layouts, multi-column text, and OCR
- Maintains paragraph structure across page breaks
- Reconstructs hyphenated words split across lines

### Word Document Processing
- Primary: Uses `python-docx` library
- Fallback: Uses `mammoth` for text extraction
- Preserves paragraph structure from document formatting

### HTML Processing
- Extracts text from `<p>` tags using BeautifulSoup
- Ignores HTML formatting and focuses on content

### Plain Text Processing
- Splits on double newlines (`\n\n`)
- Simple but effective for well-formatted text files

## Output Format

The service outputs JSON files containing arrays of paragraph strings:

```json
[
  "This is the first paragraph extracted from the document. It contains meaningful content that meets the minimum length requirement.",
  "This is the second paragraph with additional content and context.",
  "..."
]
```

## Error Handling

- **File Type Errors**: Unsupported file types raise `ValueError`
- **Processing Errors**: Logged with full stack traces
- **SQS Failures**: Messages are requeued for retry
- **S3 Errors**: Failures are logged and submission status reflects error state

## Development

### Adding New File Types

1. Create a new extraction function in `paragraph_extractor.py`
2. Add the file extension to the `paragraphs_from_file()` function
3. Add appropriate dependencies to `pyproject.toml`
4. Create test fixtures and tests

## Monitoring

- CloudWatch logs (in AWS environments)
- DynamoDB submission status updates
- Logging

### Performance Considerations

- PDF processing is slower due to AI analysis
- Large files may require increased timeout settings
- Consider file size limits for memory usage
