from flask import request, jsonify
from pdf2image import convert_from_path
import pytesseract
import json
import csv
import io
import os
from .preprocessing import preprocess_image
from .extraction import extract_value

def register_extract_routes(app):
    @app.route('/extract', methods=['POST'])
    def extract_data():
        data = request.json
        if 'filenames' not in data or 'template' not in data:
            return jsonify({'message': 'Filenames and template are required'}), 400

        filenames = data['filenames']
        template_name = data['template']
        output_format = data.get('output_format', 'json')

        results = []
        progress_file = os.path.join(app.config['UPLOAD_FOLDER'], 'progress.txt')
        with open(progress_file, 'w') as f:
            f.write('0')

        for current_file_index, filename in enumerate(filenames):
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if template_name == "Default Template":
                template_path = 'resources/json_templates/default_template.json'
            else:
                template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{template_name}.json')

            if not os.path.exists(pdf_path):
                return jsonify({'message': f'File {filename} not found'}), 404
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

            results.append((filename, extracted_data, original_lines))
            progress = int((int(current_file_index) + 1) / len(filenames) * 100)
            with open(progress_file, 'w') as f:
                f.write(str(progress))
        if output_format in ['json', 'csv', 'text']:
            response_data = {filename: data for filename, data, _ in results}
            lines_data = {filename: lines for filename, _, lines in results}

            # Prepare CSV format
            csv_output = io.StringIO()
            csv_writer = csv.writer(csv_output)
            headers = set()
            for _, data, _ in results:
                headers.update(data.keys())
            csv_writer.writerow(['filename'] + list(headers))
            for filename, data, _ in results:
                row = [filename] + [data.get(header, '') for header in headers]
                csv_writer.writerow(row)
            csv_data = csv_output.getvalue()

            # Prepare text format
            text_data = ""
            for filename, data, _ in results:
                text_data += f"File: {filename}\n"
                text_data += "\n".join([f"{key}: {value}" for key, value in data.items()])
                text_data += "\n\n"

            return jsonify({
                'json_data': response_data,
                'lines_data': lines_data,
                'csv_data': csv_data,
                'text_data': text_data
            }), 200
        else:
            return jsonify({'message': 'Unsupported output format'}), 400

    @app.route('/progress', methods=['GET'])
    def get_progress():
        progress_file = os.path.join(app.config['UPLOAD_FOLDER'], 'progress.txt')
        with open(progress_file, 'r') as f:
            progress = f.read()
        return jsonify({'progress': int(progress)})
