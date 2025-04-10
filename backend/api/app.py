import os
import boto3
import requests
from boto3.dynamodb.conditions import Key
from requests import Response
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_cognito import CognitoAuth, cognito_auth_required, current_cognito_jwt
from functools import wraps

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from common.constants import SUBMISSIONS_TABLE, VOCABULARY_TABLE, SUMMARIES_TABLE
from common.envvar import environment
from common.logger import logger
from common.summary_repo import SummaryRepo
from common.vocabulary_word_repo import VocabularyWordRepo

# Flask app setup
app = Flask(__name__)

# Configure Cognito
app.config['COGNITO_REGION'] = environment.require('AWS_REGION')
app.config['COGNITO_USERPOOL_ID'] = environment.require('COGNITO_USERPOOL_ID')
app.config['COGNITO_APP_CLIENT_ID'] = environment.require('COGNITO_APP_CLIENT_ID')
app.config['COGNITO_CHECK_TOKEN_EXPIRATION'] = True

cognito = CognitoAuth(app)

IS_LOCAL = environment.require('IS_LOCAL')
AWS_REGION = environment.require('AWS_REGION')
SUBMISSIONS_BUCKET = environment.require('SUBMISSIONS_BUCKET')
CORS_ORIGINS = environment.require('CORS_ORIGINS').split(',')

CORS(app, origins=CORS_ORIGINS,
     supports_credentials=True,
     expose_headers=["Content-Type", "Authorization"],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Max file size
MAX_BYTES = 100 * 1024 * 1024  # 100 MB

# Initialize AWS Clients
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
s3_client = boto3.client("s3", region_name=AWS_REGION)

# Reference DynamoDB tables
submissions_table = dynamodb.Table(SUBMISSIONS_TABLE)
vocab_table = dynamodb.Table(VOCABULARY_TABLE)
summary_table = dynamodb.Table(SUMMARIES_TABLE)

# New decorator to only apply cognito in prod
def conditional_cognito_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not IS_LOCAL:
            # Apply Cognito authentication in non-development environments
            return cognito_auth_required(f)(*args, **kwargs)
        else:
            # Bypass Cognito authentication in development
            return f(*args, **kwargs)
    return decorated_function

def get_user_id():
    if app.config['ENV'] == 'development':
        return 'dev-user'
    else:
        # Use Cognito for production
        return current_cognito_jwt['sub']

def submitted_file_content(req) -> tuple[bytes, None]|tuple[None, tuple[Response, int]]:
    """
    Extracts file content (as bytes) from an uploaded file, URL, or raw text.
    Enforces the 100MB max size limit.
    Returns: (bytes) or (None, error_response)
    """
    uploaded_file = req.files.get("file")
    input_url = req.form.get("url")
    input_text = req.form.get("text")

    if uploaded_file and uploaded_file.filename != "":
        content_bytes = uploaded_file.read()
    elif input_url:
        try:
            response = requests.get(input_url, timeout=10)
            response.raise_for_status()
            content_bytes = response.content
        except Exception as e:
            return None, (jsonify({"error": f"Failed to download URL: {str(e)}"}), 400)
    elif input_text:
        content_bytes = input_text.encode("utf-8")
    else:
        return None, (jsonify({"error": "No file uploaded"}), 400)

    if len(content_bytes) > MAX_BYTES:
        return None, (jsonify({"error": "File exceeds 100MB limit."}), 413)
    else:
        return content_bytes, None

@app.route("/generate-upload-url", methods=["POST"])
@conditional_cognito_auth
def generate_upload_url():
    """
    Generates a presigned S3 URL for uploading a file.
    The submission_id is deterministically computed from the file content and user_id.
    """
    user_id = request.json.get('user_id')
    file_name = request.json.get('file_name')
    file_hash = request.json.get('file_hash')
    file_extension = os.path.splitext(file_name)[1] if file_name else ""

    if not user_id or not file_name or not file_hash:
        return jsonify({"error": "Missing required fields: user_id, file_name, content_preview"}), 400

    # Compute deterministic hash using user_id + content preview
    s3_key = f"uploads/{user_id}/{file_hash}{file_extension}"

    try:
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': SUBMISSIONS_BUCKET, 'Key': s3_key, 'ContentType': 'text/plain'},
            ExpiresIn=300
        )
    except Exception as e:
        return jsonify({'error': f"Failed to generate presigned URL: {str(e)}"}), 500

    return jsonify({
        'submission_id': file_hash,
        'upload_url': presigned_url,
        's3_key': s3_key
    })

def get_submission_vocabulary(user_id, submission_id):
    vocab_response = vocab_table.query(
        KeyConditionExpression=Key('user_id').eq(user_id) &
                                Key('submission_paragraph_word').begins_with(f"#VOCAB#{submission_id}#")
    )
    vocab_data = {}
    for item in vocab_response.get('Items', []):
        _, _, paragraph_number, word = item['submission_paragraph_word'].split('#')
        if paragraph_number not in vocab_data:
            vocab_data[paragraph_number] = []
        vocab_data[paragraph_number].append(word)

    return vocab_data

def get_submission_summaries(user_id, submission_id):
    summary_response = summary_table.query(
        KeyConditionExpression=Key('user_id').eq(user_id) &
                                Key('submission_paragraph').begins_with(f"#SUMMARY#{submission_id}#")
    )
    summaries = {}
    for item in summary_response.get('Items', []):
        _, _, paragraph_number = item['submission_paragraph'].split('#')
        summaries[paragraph_number] = item['summary']

    return summaries

@app.route("/files/<submission_id>/details", methods=["GET"])
@conditional_cognito_auth
def get_submission_details(submission_id):
    """Returns the first 10 words, vocabulary, and summary for each paragraph of a submission."""

    user_id = get_user_id()

    # Fetch vocabulary from DynamoDB
    try:
        vocab_data = VocabularyWordRepo(vocab_table).get_by_submission(user_id, submission_id)
    except Exception as e:
        return jsonify({"submission_id": submission_id, "error": f"DynamoDB error: {str(e)}"}), 500

    try:
        summaries = SummaryRepo(summary_table).get_by_submission(user_id, submission_id)
    except Exception as e:
        return jsonify({"submission_id": submission_id, "error": f"DynamoDB error: {str(e)}"}), 500

    # Combine data
    details = []
    paragraph_count = max(len(vocab_data), len(summaries))
    for i in range(paragraph_count):
        details.append({
            "paragraph_index": i,
            "vocabulary": vocab_data[i],
            "summary": summaries[i] if i < len(summaries) else ""
        })
    return jsonify({"submission_id": submission_id, "details": details})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
