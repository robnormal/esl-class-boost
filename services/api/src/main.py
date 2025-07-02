import os
import traceback
from typing import List, Dict

import boto3
import requests
from boto3.dynamodb.conditions import Key
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_cognito import CognitoAuth, cognito_auth_required, current_cognito_jwt
import json

# Load environment variables
from dotenv import load_dotenv


load_dotenv()

from common.constants import SUBMISSIONS_TABLE, VOCABULARY_TABLE, SUMMARIES_TABLE
from common.envvar import environment
from common.logger import logger
from common.summary_repo import SummaryRepo
from common.vocabulary_word_repo import VocabularyWordRepo, VocabularyWord
from common.submission_repo import submission_repo, NewSubmission, SubmissionState, SubmissionRepo, SUBMISSION_COMPLETED

# Flask app setup
app = Flask(__name__)

# Configure Cognito
app.config['COGNITO_REGION'] = environment.require('AWS_REGION')
app.config['COGNITO_USERPOOL_ID'] = environment.require('COGNITO_USERPOOL_ID')
app.config['COGNITO_APP_CLIENT_ID'] = environment.require('COGNITO_APP_CLIENT_ID')
app.config['COGNITO_CHECK_TOKEN_EXPIRATION'] = True

cognito = CognitoAuth(app)

IS_LOCAL = not environment.is_prod()
AWS_REGION = environment.require('AWS_REGION')
SUBMISSIONS_BUCKET = environment.require('SUBMISSIONS_BUCKET')
PARAGRAPHS_BUCKET = environment.require('PARAGRAPHS_BUCKET')
CORS_ORIGINS = environment.require('CORS_ORIGINS').split(',')
FLASK_PORT = environment.require('FLASK_PORT')

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

# decorator to only apply cognito in prod
def conditional_cognito_auth(f):
    if not IS_LOCAL:
        return cognito_auth_required(f)
    else:
        return f

def get_user_id():
    if IS_LOCAL:
        return 'dev-user'
    else:
        # Use Cognito for production
        return current_cognito_jwt['username']

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

def get_submission_state_name(submission_item) -> str:
    logger.info(submission_item)
    try:
        state = submission_item.get('state')
        if state == SubmissionState.RECEIVED.value:
            return 'received'
        elif state < SUBMISSION_COMPLETED:
            return 'processing'
        elif state == SUBMISSION_COMPLETED:
            return 'complete'
        else:
            return str(state)

    except Exception as _e:
        logger.error(traceback.format_exc())
        return 'Invalid state'

@app.route("/api/health", methods=["GET"])
def health():
    return {"status": "ok"}

@app.route("/api/generate-upload-url", methods=["POST"])
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

        # Save submission record to DynamoDB
        new_submission = NewSubmission(
            user_id=user_id,
            submission_id=file_hash,
            state=SubmissionState.RECEIVED.value,
            filename=file_name
        )
        submission_repo.create(new_submission)
        logger.info(f"Created submission record for {file_hash}")

    except Exception as e:
        logger.error(f"Error in generate_upload_url: {e}", exc_info=True)
        return jsonify({'error': f"Failed to process request: {str(e)}"}), 500

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

def group_by_paragraph(vocabulary_words: List[VocabularyWord]) -> Dict[int, List[str]]:
    grouped_by_paragraph = {}
    for vocabulary_word in vocabulary_words:
        if vocabulary_word.paragraph_number not in grouped_by_paragraph:
            grouped_by_paragraph[vocabulary_word.paragraph_number] = []
        grouped_by_paragraph[vocabulary_word.paragraph_number].append(vocabulary_word.word)
    return grouped_by_paragraph

@app.route("/api/files/<submission_id>/details", methods=["GET"])
@conditional_cognito_auth
def get_submission_details(submission_id):
    logger.info(f'get_submission_details ${submission_id}')

    """Returns the first 10 words, vocabulary, and summary for each paragraph of a submission."""
    user_id = get_user_id()

    submission = SubmissionRepo(submissions_table).get_by_id(user_id, submission_id)
    if submission.state != SUBMISSION_COMPLETED:
        return jsonify({"submission_id": submission_id, "error": f"Submission not ready yet. Try again later."}), 503

    # Fetch vocabulary from DynamoDB
    try:
        vocab_data = VocabularyWordRepo(vocab_table).get_by_submission(user_id, submission_id)
    except Exception as e:
        logger.error(e, exc_info=True)
        return jsonify({"submission_id": submission_id, "error": f"DynamoDB error: {str(e)}"}), 500

    try:
        summaries = SummaryRepo(summary_table).get_by_submission(user_id, submission_id)
    except Exception as e:
        logger.error(e, exc_info=True)
        return jsonify({"submission_id": submission_id, "error": f"DynamoDB error: {str(e)}"}), 500

    words_by_paragraph = group_by_paragraph(vocab_data)
    summaries_by_paragraph = {}
    for summary in summaries:
        summaries_by_paragraph[summary.paragraph_number] = summary

    # Combine data
    details = []
    paragraph_count = max(len(words_by_paragraph), len(summaries_by_paragraph.keys()))
    for i in range(paragraph_count):
        details.append({
            "paragraph_index": i,
            "vocabulary": words_by_paragraph.get(i, []),
            "summary": summaries_by_paragraph[i].summary if i in summaries_by_paragraph else "",
            "paragraph_start": summaries_by_paragraph[i].paragraph_start if i in summaries_by_paragraph else "",
        })
    return jsonify({"submission_id": submission_id, "details": details})

@app.route("/api/files/<submission_id>/text", methods=["GET"])
@conditional_cognito_auth
def get_submission_text(submission_id):
    """Returns the paragraphs of the submission as a list."""
    logger.info(f'get_submission_text {submission_id}')
    user_id = get_user_id()

    # Verify submission exists and belongs to user
    submission = SubmissionRepo(submissions_table).get_by_id(user_id, submission_id)
    if not submission:
        return jsonify({"error": "Submission not found"}), 404

    try:
        print(f"Fetching {submission.s3_base_path()}.json from {PARAGRAPHS_BUCKET}")
        # Get the JSON file from S3
        response = s3_client.get_object(
            Bucket=PARAGRAPHS_BUCKET,
            Key=f"{submission.s3_base_path()}.json"
        )
        paragraphs = json.loads(response['Body'].read().decode('utf-8'))
        if not isinstance(paragraphs, list):
            return jsonify({"error": "Paragraphs data is not a list"}), 500
        return jsonify({"paragraphs": paragraphs})
    except Exception as e:
        logger.error(f"Error retrieving submission text: {e}", exc_info=True)
        return jsonify({"error": f"Failed to retrieve submission text: {str(e)}"}), 500


@app.route("/api/submissions", methods=["GET"])
@conditional_cognito_auth
def get_submissions_list():
    """
    Returns a list of all submissions for the current user.
    Format expected by frontend:
    {
        "submissions": [
            {
                "id": string,
                "filename": string,
                "created_at": string (ISO date),
                "status": string
            }
        ]
    }
    """
    user_id = get_user_id()
    logger.info(f'get_submissions_list for user {user_id}')

    try:
        # Query the submissions table for all submissions by this user
        response = submissions_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )

        submissions = []
        for item in response.get('Items', []):
            # Transform DynamoDB item to the format expected by the frontend
            submissions.append({
                "id": item.get('submission_id'),
                "filename": item.get('filename', 'Unnamed Document'),
                "created_at": item.get('created_at', None),
                "status": get_submission_state_name(item),
            })

        # Sort submissions by created_at (newest first)
        submissions.sort(key=lambda x: x.get('created_at') or 0, reverse=True)

        return jsonify({"submissions": submissions})

    except Exception as e:
        logger.error(f"Error fetching submissions: {e}", exc_info=True)
        return jsonify({"error": f"Failed to fetch submissions: {str(e)}"}), 500

@app.route("/api/definition/<word>", methods=["GET"])
def get_word_definition(word):
    """Proxy to dictionaryapi.dev to get the definition of a word."""
    try:
        resp = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
            timeout=10
        )
        if resp.status_code != 200:
            return jsonify({"error": f"DictionaryAPI error: {resp.status_code}"}), resp.status_code
        data = resp.json()
        # data is a list of entries, each with meanings, each with definitions
        definitions = []
        if isinstance(data, list):
            for entry in data:
                for meaning in entry.get("meanings", []):
                    part_of_speech = meaning.get("partOfSpeech")
                    for definition in meaning.get("definitions", []):
                        def_text = definition.get("definition")
                        if def_text:
                            definitions.append({
                                "definition": def_text,
                                "partOfSpeech": part_of_speech
                            })
        return jsonify(definitions)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch definition: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=FLASK_PORT)
