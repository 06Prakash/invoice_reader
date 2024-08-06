import logging
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from pdf2image import convert_from_path
import pytesseract
import json
import csv
import io
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from .preprocessing import preprocess_image
from .extraction import extract_value

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a file handler and set the log level
file_handler = logging.FileHandler('/app/logs/app.log')
file_handler.setLevel(logging.DEBUG)

# Create a log formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

progress_lock = Lock()
progress = 0

def register_extract_routes(app):
    global progress  # Declare progress as global

    def extract_from_pdf(filename, template, upload_folder, total_pages, progress_file):
        global progress  # Declare progress as global inside the function
        pdf_path = os.path.join(upload_folder, filename)
        logger.info(f"Extraction started for {filename} at {pdf_path} using template {template['name']} ...")
        try:
            pages = convert_from_path(pdf_path, 300)
        except Exception as e:
            logger.error(f"Error converting PDF: {str(e)}")
            return filename, {'error': str(e)}, []

        extracted_data = {}
        original_lines = []
        page_count = len(pages)

        for page_number, page_data in enumerate(pages):
            try:
                image_path = f"{filename}_page_{page_number}.jpg"
                logger.info(f"Processing page {page_number} of {filename}")
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

                # Update progress file
                with progress_lock:
                    progress += 1
                    overall_progress = int((progress / total_pages) * 100)
                    with open(progress_file, 'w') as pf:
                        logger.info(f"Current progress: {overall_progress}%")
                        pf.write(str(overall_progress))

            except Exception as e:
                logger.error(f"Error processing page {page_number} of {filename}: {e}")
                continue

        return filename, extracted_data, original_lines

    @app.route('/extract', methods=['POST'])
    @jwt_required()
    def extract_data():
        global progress  # Declare progress as global inside the function
        data = request.json
        if 'filenames' not in data or 'template' not in data:
            logger.error('Filenames and template are required')
            return jsonify({'message': 'Filenames and template are required'}), 400

        filenames = data['filenames']
        template_name = data['template']
        output_format = data.get('output_format', 'json')
        upload_folder = app.config['UPLOAD_FOLDER']
        progress_file = os.path.join(upload_folder, 'progress.txt')

        # Create the progress file
        with open(progress_file, 'w') as pf:
            pf.write('0')

        if template_name == "Default Template":
            template_path = 'resources/json_templates/default_template.json'
        else:
            template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{template_name}.json')

        if not os.path.exists(template_path):
            logger.error('Template not found')
            return jsonify({'message': 'Template not found'}), 404

        with open(template_path, 'r') as f:
            template = json.load(f)

        # Set the maximum number of workers to 2 for now
        max_workers = 2

        total_pages = sum([len(convert_from_path(os.path.join(upload_folder, filename), 300)) for filename in filenames])
        progress = 0  # Ensure progress starts at zero

        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(extract_from_pdf, filename, template, upload_folder, total_pages, progress_file) for filename in filenames]
            for future in as_completed(futures):
                results.append(future.result())

        response_data = {filename: data for filename, data, _ in results}
        lines_data = {filename: lines for filename, _, lines in results}

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

        text_data = ""
        for filename, data, _ in results:
            text_data += f"File: {filename}\n"
            text_data += "\n".join([f"{key}: {value}" for key, value in data.items()])
            text_data += "\n\n"

        # Ensure progress file is set to 100% after all processing is done
        with open(progress_file, 'w') as pf:
            pf.write('100')

        return jsonify({
            'json_data': response_data,
            'lines_data': lines_data,
            'csv_data': csv_data,
            'text_data': text_data
        }), 200

    @app.route('/progress', methods=['GET'])
    @jwt_required()
    def get_progress():
        upload_folder = app.config['UPLOAD_FOLDER']
        progress_file = os.path.join(upload_folder, 'progress.txt')
        try:
            with open(progress_file, 'r') as f:
                progress = f.read()
            return jsonify({'progress': progress}), 200
        except FileNotFoundError:
            return jsonify({'progress': '0'}), 200
