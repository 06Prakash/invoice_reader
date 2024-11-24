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
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
# import numpy as np
# from PIL import Image
# import cv2
# import easyocr
# from transformers import pipeline, AutoModelForTokenClassification, AutoTokenizer

# # Azure Form Recognizer Configuration
key_vault_url = os.getenv("KEY_VAULT_URL")
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

# Retrieve secrets
AZURE_ENDPOINT = secret_client.get_secret("azure-form-recognizer-endpoint").value
AZURE_KEY = secret_client.get_secret("azure-form-recognizer-key").value

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# File handler for logging
file_handler = logging.FileHandler('/app/logs/app.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


progress_lock = Lock()
progress = 0

def register_extract_routes(app):
    global progress

    def extract_from_pdf(filename, template, upload_folder, total_pages, progress_file):
        global progress
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
                    capture_mode = field.get('capture_mode', 'between')
                    value = extract_value(page_text, keyword, separator, boundaries, capture_mode, data_type, indices, multiline, logger)
                    extracted_data[name] = value

                # Update progress
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

    def process_simple_types(value):
        """
        Processes simple types (str, int, float) and removes commas from strings.
        """
        if isinstance(value, str):
            return value.replace(',', '')  # Remove commas
        return value


    def process_dictionary(value):
        """
        Processes dictionary types, ensuring nested fields are properly serialized.
        """
        return {
            k: process_field(v)
            for k, v in value.items()
        }


    def process_custom_object(value):
        """
        Processes custom objects by accessing their __dict__ attribute and serializing fields.
        """
        return {
            k: process_field(v)
            for k, v in value.__dict__.items()
        }


    def process_field(field):
        """
        Processes individual field values based on their data type.
        """
        if field is None:
            return None  # Handle NoneType field gracefully

        field_value = None
        if hasattr(field, "value"):
            field_value = field.value
        elif hasattr(field, "content"):
            field_value = field.content

        # If field_value is still None, return None
        if field_value is None:
            return None

        # Process based on the type of field_value
        if isinstance(field_value, (str, int, float)):  # Simple types
            return process_simple_types(field_value)
        elif isinstance(field_value, dict):  # Dictionary type
            return process_dictionary(field_value)
        elif hasattr(field_value, '__dict__'):  # Custom objects
            return process_custom_object(field_value)
        elif isinstance(field_value, list):  # List type
            return [process_field(item) for item in field_value]  # Process each item in the list
        else:
            return str(field_value).replace(',', '')  # Fallback to string and remove commas


    
    def extraction_model_mapping(extraction_model):
        model_mapping = {
            "Nira standard": "Standard",
            "Nira AI - Custom handwritten": "MutualFundModelSundaramFinance",
            "Nira AI - Invoice": "prebuilt-invoice",
            "Nira AI - Printed Text": "prebuilt-read",
            "Nira AI - Printed business card": "prebuilt-businessCard",
            "Nira AI - Printed receipt": "prebuilt-receipt",
        }
        return model_mapping[extraction_model]
    
    def flatten_nested_field(data, delimiter=" | ", replace_newline_with=" | "):
        """
        Flattens a nested field into a single string, removing newlines and using a custom delimiter.

        :param data: The nested JSON field to flatten
        :param delimiter: The delimiter to use for separating nested values
        :param replace_newline_with: Replacement for newlines in string values
        :return: A flattened string representation of the field
        """
        if isinstance(data, dict):
            # Recursively process each key-value pair and join with the delimiter
            return delimiter.join(f"{key}: {flatten_nested_field(value, delimiter, replace_newline_with)}"
                                for key, value in data.items() if value)
        elif isinstance(data, list):
            # Process each item in the list
            return delimiter.join(flatten_nested_field(item, delimiter, replace_newline_with) for item in data)
        elif isinstance(data, str):
            # Replace newlines in string values
            return data.replace("\n", replace_newline_with).strip()
        elif data is not None:
            # Convert other types to string and return
            return str(data).strip()
        else:
            return "N/A"  # Placeholder for null or missing values


    def extract_with_azure(filename, upload_folder, total_pages, progress_file, extraction_model):
        """
        Extracts data from a PDF using Azure Form Recognizer and writes progress.

        :param filename: Name of the PDF file to process
        :param upload_folder: Folder containing the file
        :param total_pages: Total number of pages to process across all files
        :param progress_file: Path to the progress file to update progress
        :param extraction_model: Model for extracting the current file
        :return: Tuple of (filename, extracted_data, original_lines)
        """
        document_analysis_client = DocumentAnalysisClient(endpoint=AZURE_ENDPOINT, credential=AzureKeyCredential(AZURE_KEY))
        pdf_path = os.path.join(upload_folder, filename)
        logger.info(f"Starting Azure extraction for {filename} at {pdf_path}.")

        global progress

        try:
            current_model = extraction_model_mapping(extraction_model)
            with open(pdf_path, "rb") as document:
                poller = document_analysis_client.begin_analyze_document(current_model, document)
                result = poller.result()

            extracted_data = {}
            original_lines = []

            # Extract fields and remove confidence scores
            for idx, doc in enumerate(result.documents):
                for name, field in doc.fields.items():
                    logger.info("=-=-=-=-=-=-=-=")
                    logger.info(name)
                    logger.info(field)
                    logger.info("=-=-=-=-=-=-=-=")

                    # Process field and flatten nested fields
                    field_value = process_field(field)  # Call process_field function
                    if isinstance(field_value, (dict, list)):
                        # Flatten nested fields into a single string with newline separation
                        extracted_data[name] = flatten_nested_field(field_value)
                    else:
                        extracted_data[name] = field_value

                    # # Remove commas and ensure compatibility for CSV
                    # if isinstance(field_value, (str, int, float)):  # Simple types
                    #     if isinstance(field_value, str):
                    #         field_value = field_value.replace(',', '')  # Remove commas
                    #     extracted_data[name] = field_value
                    # elif isinstance(field_value, dict):  # Handle dictionary type
                    #     extracted_data[name] = {
                    #         k: (v.value if hasattr(v, "value") else v.content if hasattr(v, "content") else str(v)).replace(',', '')
                    #         if isinstance((v.value if hasattr(v, "value") else v), str) else v
                    #         for k, v in field_value.items()
                    #     }
                    # elif hasattr(field_value, '__dict__'):  # Custom objects
                    #     sanitized_dict = {
                    #         k: (str(v).replace(',', '') if isinstance(v, str) else v)
                    #         for k, v in field_value.__dict__.items()
                    #     }
                    #     extracted_data[name] = sanitized_dict
                    # else:
                    #     extracted_data[name] = str(field_value).replace(',', '')  # Fallback to string and remove commas

            # Log the final extracted_data
            logger.info("Final extracted data:")
            logger.info(extracted_data)# Fallback to string and remove commas

            # Extract original lines from the document
            for page in result.pages:
                for line in page.lines:
                    original_lines.append(line.content)

            # Update progress in the progress file based on the number of pages
            with progress_lock:
                progress += len(result.pages)
                overall_progress = int((progress / total_pages) * 100)
                with open(progress_file, 'w') as pf:
                    logger.info(f"Current progress: {overall_progress}%")
                    pf.write(str(overall_progress))

            return filename, extracted_data, original_lines

        except Exception as e:
            logger.error(f"Azure extraction failed for {filename}: {str(e)}")
            return filename, {'error': str(e)}, []


    @app.route('/extract', methods=['POST'])
    @jwt_required()
    def extract_data():
        global progress
        data = request.json
        if 'filenames' not in data or 'template' not in data:
            logger.error('Filenames and template are required')
            return jsonify({'message': 'Filenames and template are required'}), 400

        filenames = data['filenames']
        template_name = data['template']
        output_format = data.get('output_format', 'json')
        extraction_model = data.get('extraction_model', 'Nira Standard').replace("(PB)", "").replace("(Custom)", "").strip()
        upload_folder = app.config['UPLOAD_FOLDER']
        progress_file = os.path.join(upload_folder, 'progress.txt')

        # Create progress file
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

        max_workers = 2
        total_pages = sum([len(convert_from_path(os.path.join(upload_folder, filename), 300)) for filename in filenames])
        progress = 0  # Reset progress

        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for filename in filenames:
                logger.info(f"Extraction Model {extraction_model}")
                if 'nira standard' not in extraction_model.lower():  # Use Azure extraction
                    futures.append(
                        executor.submit(extract_with_azure, filename, upload_folder, total_pages, progress_file, extraction_model)
                    )
                else:  # Use template-based extraction
                    futures.append(
                        executor.submit(
                            extract_from_pdf, filename, template, upload_folder, total_pages, progress_file
                        )
                    )

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

    @app.route('/extraction-models', methods=['GET'])
    def get_extraction_models():
        """
        Fetches the list of available extraction models.

        :return: A JSON response containing the list of extraction models.
        """
        try:
            extraction_models = [
                "Nira standard",
                "Nira AI - handwritten (Custom)",
                "Nira AI - Invoice (PB)",
                "Nira AI - Printed Text (PB)",
                "Nira AI - Printed business card (PB)",
                "Nira AI - Printed receipt (PB)"
            ]
            logger.info("Extraction models fetched successfully.")
            return jsonify({"models": extraction_models}), 200
        except Exception as e:
            logger.error(f"Error fetching extraction models: {e}")
            return jsonify({"error": "Failed to fetch extraction models"}), 500