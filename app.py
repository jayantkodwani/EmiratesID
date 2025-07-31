import os
from flask import Flask, request, jsonify, render_template
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)

# Use environment variables for security
endpoint = os.environ.get("AZURE_FORMRECOGNIZER_ENDPOINT")
key = os.environ.get("AZURE_FORMRECOGNIZER_KEY")

client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
MAX_FILE_SIZE_MB = 4

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_fields(result):
    data = {}
    for doc in result.documents:
        for field, val in doc.fields.items():
            # Always return raw OCR-extracted string, not typed Python object
            data[field] = val.content if hasattr(val, 'content') else str(val.value)
    return data

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

        # Read file once and reuse for both models
        file_bytes = file.read()
        file1 = BytesIO(file_bytes)
        file2 = BytesIO(file_bytes)

        try:
            # Analyze with Model 1
            poller1 = client.begin_analyze_document("Emirates_ID_Front_V2", document=file1)
            result1 = poller1.result()
            data1 = extract_fields(result1)

            # Analyze with Model 2
            poller2 = client.begin_analyze_document("Emirates_ID_Back", document=file2)
            result2 = poller2.result()
            data2 = extract_fields(result2)

            # Combine results under separate sections
            combined_result = {
                "Emirates_ID_Front": data1,
                "Emirates_ID_Back": data2
            }

            return jsonify(combined_result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    else:
        return jsonify({"error": "Invalid file format. Only images and PDFs are allowed."}), 400

if __name__ == '__main__':
    app.run(debug=True)
