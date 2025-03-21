import uuid
import boto3
from flask import Flask, request, jsonify

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

# AWS Configuration
AWS_REGION = "us-east-1"
DYNAMODB_TABLE_NAME = "SubmissionsTable"
DYNAMODB_VOCAB_TABLE = "VocabularyTable"
S3_BUCKET_NAME = "your-s3-bucket"
S3_BASE_URL = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com"

# Initialize AWS Clients
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
s3_client = boto3.client("s3", region_name=AWS_REGION)

# Reference DynamoDB tables
submissions_table = dynamodb.Table(DYNAMODB_TABLE_NAME)
vocab_table = dynamodb.Table(DYNAMODB_VOCAB_TABLE)

@app.route("/submit-url", methods=["POST"])
def submit_url():
    """Stores the submitted file URL in DynamoDB."""
    data = request.get_json()
    if "file_url" not in data:
        return jsonify({"error": "Missing 'file_url' in request body"}), 400

    file_id = str(uuid.uuid4())
    file_url = data["file_url"]

    try:
        submissions_table.put_item(
            Item={
                "file_id": file_id,
                "file_url": file_url
            }
        )
    except Exception as e:
        return jsonify({"error": f"DynamoDB error: {str(e)}"}), 500

    return jsonify({"file_id": file_id, "file_url": file_url, "message": "Submission successful."})

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
