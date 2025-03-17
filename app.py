from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt", "pdf", "docx", "html", "md"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/process-url", methods=["POST"])
def process_url():
    """Acknowledge URL submission but discard the content."""
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    return jsonify({"message": "URL received", "url": url}), 200

@app.route("/process-text", methods=["POST"])
def process_text():
    """Acknowledge text submission but discard the content."""
    data = request.json
    text = data.get("text")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    return jsonify({"message": "Text received", "text_length": len(text)}), 200

@app.route("/upload-file", methods=["POST"])
def upload_file():
    """Acknowledge file upload but discard the file."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    # Acknowledge receipt but discard the file
    filename = secure_filename(file.filename)

    return jsonify({"message": "File received", "filename": filename}), 200

if __name__ == "__main__":
    app.run(debug=True)
