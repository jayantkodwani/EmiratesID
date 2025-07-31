import os
from flask import Flask, request, jsonify, render_template
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

app = Flask(__name__)

# Use environment variables for security
endpoint = os.environ.get("AZURE_FORMRECOGNIZER_ENDPOINT")
key = os.environ.get("AZURE_FORMRECOGNIZER_KEY")

client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['image']
    poller = client.begin_analyze_document("Emirates_ID_Front_V2", document=file)
    result = poller.result()

    extracted_data = {}
    for doc in result.documents:
        for field, val in doc.fields.items():
            extracted_data[field] = val.value

    return jsonify(extracted_data)

if __name__ == '__main__':
    app.run(debug=True)


