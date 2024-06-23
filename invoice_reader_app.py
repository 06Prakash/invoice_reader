from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import pandas as pd
import re

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Set the Tesseract command path for Docker container
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

def pdf_to_images(pdf_path):
    return convert_from_path(pdf_path, 300)

def extract_text_from_image(image):
    return pytesseract.image_to_string(image)

def parse_invoice_text(text, fields, separator):
    invoice_data = {field: None for field in fields}
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        for field in fields:
            if field in line:
                parts = line.split(separator)
                if len(parts) > 1:
                    invoice_data[field] = parts[1].strip()
    return invoice_data

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'invoice_reader_ui.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filename)
        return jsonify({'message': 'File uploaded successfully', 'filename': filename})

@app.route('/extract', methods=['POST'])
def extract_data():
    data = request.get_json()
    pdf_path = data['filename']
    fields = data['fields']
    separator = data['separator']
    output_format = data['output_format']

    images = pdf_to_images(pdf_path)
    extracted_data = []

    for image in images:
        text = extract_text_from_image(image)
        parsed_data = parse_invoice_text(text, fields, separator)
        extracted_data.append(parsed_data)

    if output_format == 'json':
        return jsonify({'extracted_data': extracted_data})
    elif output_format == 'csv':
        df = pd.DataFrame(extracted_data)
        csv_output = df.to_csv(index=False)
        return csv_output
    elif output_format == 'txt':
        txt_output = ""
        for item in extracted_data:
            for key, value in item.items():
                txt_output += f"{key}: {value}\n"
            txt_output += "\n"
        return txt_output
    else:
        return jsonify({'error': 'Invalid output format'}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
