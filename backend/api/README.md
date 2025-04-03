# English Vocabulary Tool API

Flask backend for processing text files and extracting vocabulary.

## Setup

1. Install dependencies:
```bash
pip install flask flask-cors boto3 requests chardet
```

2. Configure AWS credentials:
- Set up AWS credentials in `~/.aws/credentials` or environment variables
- Required permissions: S3 and DynamoDB access

3. Environment variables (optional):
```bash
export AWS_REGION=us-east-2
export S3_BUCKET_NAME=rhr79-history-learning-submissions
```

## Running

```bash
python app.py
```

Server runs on `http://localhost:5000`

## API Endpoints

- `POST /generate-upload-url`: Generate S3 upload URL
- `POST /submit-text`: Submit text file/URL
- `GET /files`: List submitted files
- `GET /files/<file_id>/summaries`: Get paragraph summaries
- `GET /files/<file_id>/vocabulary`: Get vocabulary words 