from flask import request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
import pytesseract
import json
import csv
import io
import os
from datetime import datetime
import numpy as np
from .preprocessing import preprocess_image
from .extraction import extract_value
from .validation import validate_date, validate_time, validate_number, extract_number

def register_routes(app):
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    @app.route('/upload', methods=['POST'])
    def upload_file():
        if 'file' not in request.files:
            return jsonify({'message': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return jsonify({'filename': filename}), 200
        return jsonify({'message': 'File type not allowed'}), 400

    @app.route('/templates', methods=['POST'])
    def save_template():
        data = request.json
        template_name = data['name']
        if template_name == "Default Template":
            template_name = 'default_template'
        template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{template_name}.json')
        with open(template_path, 'w') as f:
            json.dump(data, f)
        return jsonify({'message': 'Template saved successfully'}), 200

    @app.route('/templates', methods=['GET'])
    def get_templates():
        templates = [f.split('.')[0] for f in os.listdir(app.config['TEMPLATE_FOLDER']) if f.endswith('.json')]
        return jsonify(templates), 200

    @app.route('/default_template', methods=['GET'])
    def get_default_template():
        template_path = 'resources/json_templates/default_template.json'
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                template = json.load(f)
            return jsonify(template), 200
        return jsonify({'message': 'Default template not found'}), 404

    @app.route('/templates/<name>', methods=['GET'])
    def get_template(name):
        if name == "default":
            template_path = 'resources/json_templates/default_template.json'
        else:
            template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{name}.json')

        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                template = json.load(f)
            return jsonify(template), 200
        return jsonify({'message': 'Template not found'}), 404

    @app.route('/extract', methods=['POST'])
    def extract_data():
        data = request.json
        if 'filename' not in data or 'template' not in data:
            return jsonify({'message': 'Filename and template are required'}), 400

        filename = data['filename']
        template_name = data['template']
        output_format = data.get('output_format', 'json')

        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if template_name == "Default Template":
            template_path = 'resources/json_templates/default_template.json'
        else:
            template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{template_name}.json')

        if not os.path.exists(pdf_path):
            return jsonify({'message': 'File not found'}), 404
        if not os.path.exists(template_path):
            return jsonify({'message': 'Template not found'}), 404

        with open(template_path, 'r') as f:
            template = json.load(f)

        pages = convert_from_path(pdf_path, 300)
        extracted_data = {}
        original_lines = []

        for page_number, page_data in enumerate(pages):
            image_path = f"page_{page_number}.jpg"
            page_data.save(image_path, 'JPEG')

            image_path = preprocess_image(image_path)

            page_text = pytesseract.image_to_string(image_path)
            os.remove(image_path)

            original_lines.extend(page_text.split('\n'))

            # Update your extract_data function call
            for field in template['fields']:
                name = field['name']
                keyword = field['keyword']
                separator = field.get('separator', ':')
                index = field.get('index', '1')
                indices = [int(i) for i in index.split(',')]
                boundaries = field.get('boundaries', {'left': '', 'right': '', 'up': '', 'down': ''})
                data_type = field.get('data_type', 'text')
                multiline = field.get('multiline', False)
                value = extract_value(page_text, keyword, separator, boundaries, data_type, indices, multiline)
                extracted_data[name] = value

        if output_format == 'json':
            return jsonify({'extracted_data': extracted_data, 'lines_data': original_lines}), 200
        elif output_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(extracted_data.keys())
            writer.writerow(extracted_data.values())
            csv_data = output.getvalue()
            return jsonify({'extracted_data': extracted_data, 'csv_data': csv_data, 'lines_data': original_lines}), 200
        elif output_format == 'text':
            text_data = "\n".join([f"{key}: {value}" for key, value in extracted_data.items()])
            return jsonify({'extracted_data': extracted_data, 'text_data': text_data, 'lines_data': original_lines}), 200
        else:
            return jsonify({'message': 'Unsupported output format'}), 400

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
