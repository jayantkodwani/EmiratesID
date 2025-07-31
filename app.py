import os
from flask import Flask, request, jsonify, render_template
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Use environment variables for security
endpoint = os.environ.get("AZURE_FORMRECOGNIZER_ENDPOINT")
key = os.environ.get("AZURE_FORMRECOGNIZER_KEY")

client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
MAX_FILE_SIZE_MB = 4

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['image']
    if file and allowed_file(file.filename):
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0)

        if file_length > MAX_FILE_SIZE_MB * 1024 * 1024:
            return jsonify({"error": "File too large. Max 4MB allowed."}), 400

        poller = client.begin_analyze_document("Emirates_ID_Front_V2", document=file)
        result = poller.result()

        extracted_data = {}
        for doc in result.documents:
            for field, val in doc.fields.items():
                extracted_data[field] = val.value

        return jsonify(extracted_data)
    else:
        return jsonify({"error": "Invalid file format. Only images and PDFs are allowed."}), 400

if __name__ == '__main__':
    app.run(debug=True)
