import uuid
import boto3
import requests
import chardet
from flask import Flask, request, jsonify
from requests import Response

##
# TODO: CORS headers
#
# The following headers need to be set to work with API Gateway:
# Access-Control-Allow-Origin
# Access-Control-Allow-Headers
# Access-Control-Allow-Methods
#
##

# Flask app setup
app = Flask(__name__)

# TODO: read these from the environment
AWS_REGION = "us-east-2"
DYNAMODB_TABLE_NAME = "submissions"
DYNAMODB_VOCAB_TABLE = "vocabulary_words"
S3_BUCKET_NAME = "rhr79-history-learning-submissions"
S3_BASE_URL = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com"

# Max file size
MAX_BYTES = 100 * 1024 * 1024  # 100 MB

# Initialize AWS Clients
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
s3_client = boto3.client("s3", region_name=AWS_REGION)

# Reference DynamoDB tables
submissions_table = dynamodb.Table(DYNAMODB_TABLE_NAME)
vocab_table = dynamodb.Table(DYNAMODB_VOCAB_TABLE)


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
def generate_upload_url():
    """
    Generates a presigned S3 URL for uploading a file.
    The submission_id is deterministically computed from the file content and user_id.
    """
    user_id = request.json.get('user_id')
    file_name = request.json.get('file_name')
    file_hash = request.json.get('file_hash')

    if not user_id or not file_name or not file_hash:
        return jsonify({"error": "Missing required fields: user_id, file_name, content_preview"}), 400

    # Compute deterministic hash using user_id + content preview
    s3_key = f"uploads/{user_id}/{file_hash}.txt"

    try:
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key, 'ContentType': 'text/plain'},
            ExpiresIn=300
        )
    except Exception as e:
        return jsonify({'error': f"Failed to generate presigned URL: {str(e)}"}), 500

    return jsonify({
        'submission_id': file_hash,
        'upload_url': presigned_url,
        's3_key': s3_key
    })

@app.route("/submit-text", methods=["POST"])
def submit_text():
    """
    Accepts a file, URL, or raw text, saves it to S3
    """
    user_id = request.form.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing required field: 'user_id'"}), 400

    file_bytes, error_response = submitted_file_content(request)
    if error_response:
        return error_response

    try:
        detected_encoding = chardet.detect(file_bytes)["encoding"]
        content_text = file_bytes.decode(detected_encoding or "utf-8")
    except Exception as e:
        return jsonify({"error": f"Failed to decode content: {str(e)}"}), 400

    submission_id = str(uuid.uuid4())
    s3_key = f"uploads/{submission_id}.txt"
    s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

    try:
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=s3_key, Body=content_text.encode("utf-8"))

    except Exception as e:
        return jsonify({"error": f"AWS error: {str(e)}"}), 500

    return jsonify({
        "submission_id": submission_id,
        "file_url": s3_url,
        "message": "Text successfully submitted and saved."
    })

@app.route("/files", methods=["GET"])
def list_files():
    """Returns the list of submitted file URLs from DynamoDB."""
    try:
        response = submissions_table.scan()
        files = response.get("Items", [])
    except Exception as e:
        return jsonify({"error": f"DynamoDB error: {str(e)}"}), 500

    return jsonify(files)

@app.route("/files/<file_id>/summaries", methods=["GET"])
def get_summaries(file_id):
    """Fetches paragraph summaries from an S3 file."""
    s3_key = f"summaries/{file_id}.txt"

    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        summaries = response["Body"].read().decode("utf-8").split("\n")
    except s3_client.exceptions.NoSuchKey:
        return jsonify({"file_id": file_id, "error": "Summaries not found"}), 404

    return jsonify({"file_id": file_id, "summaries": summaries})

@app.route("/files/<file_id>/vocabulary", methods=["GET"])
def get_vocabulary(file_id):
    """Returns extracted vocabulary words per paragraph from DynamoDB."""
    try:
        response = vocab_table.get_item(Key={"file_id": file_id})
        vocab_data = response.get("Item", {}).get("vocabulary", {})
    except Exception as e:
        return jsonify({"file_id": file_id, "error": f"DynamoDB error: {str(e)}"}), 500

    return jsonify({"file_id": file_id, "vocabulary": vocab_data})

# Lambda Entry Point
def lambda_handler(event, context):
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)

    return app(event, context)

if __name__ == "__main__":
    app.run(debug=True)
