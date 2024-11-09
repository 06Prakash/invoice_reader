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
import easyocr
import numpy as np
import cv2
from transformers import pipeline, AutoModelForTokenClassification, AutoTokenizer
from PIL import Image

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# File handler for logging
file_handler = logging.FileHandler('/app/logs/app.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Define model directories
easyocr_model_dir = '/root/.EasyOCR/model'
huggingface_cache_dir = '/root/.cache/huggingface/transformers'
model_dir = "dbmdz/bert-large-cased-finetuned-conll03-english"

# Check if EasyOCR model files exist
easyocr_required_files = ['craft_mlt_25k.pth', 'english_g2.pth']
easyocr_model_exists = all(os.path.exists(os.path.join(easyocr_model_dir, f)) for f in easyocr_required_files)

# Initialize EasyOCR reader based on model presence
if easyocr_model_exists:
    logger.info("EasyOCR models found. Initializing without download.")
    ocr_reader = easyocr.Reader(['en'], model_storage_directory=easyocr_model_dir, download_enabled=False)
else:
    logger.info("EasyOCR models missing. Downloading models.")
    ocr_reader = easyocr.Reader(['en'], model_storage_directory=easyocr_model_dir, download_enabled=True)

# Check if Hugging Face model files exist
huggingface_model_path = os.path.join(huggingface_cache_dir, model_dir)
huggingface_model_exists = os.path.exists(huggingface_model_path)

# Define model directories
huggingface_cache_dir = '/root/.cache/huggingface/transformers'

# Load the tokenizer and model with specified cache directory
try:
    tokenizer = AutoTokenizer.from_pretrained(model_dir, cache_dir=huggingface_cache_dir)
    model = AutoModelForTokenClassification.from_pretrained(model_dir, cache_dir=huggingface_cache_dir)
    logger.info("Hugging Face NER model loaded successfully from cache.")
except Exception as e:
    logger.error(f"Failed to load Hugging Face NER model: {e}")
    raise e

# Initialize the pipeline with the loaded model and tokenizer
nlp_ner = pipeline("ner", model=model, tokenizer=tokenizer)


progress_lock = Lock()
progress = 0

def register_extract_routes(app):
    global progress

    def enhanced_extract_from_pdf(filename, template, upload_folder, total_pages, progress_file):
        pdf_path = os.path.join(upload_folder, filename)
        logger.info(f"Enhanced extraction started for {filename} at {pdf_path} using template {template['name']} ...")

        try:
            # Convert PDF to images
            pages = convert_from_path(pdf_path, 300)
        except Exception as e:
            logger.error(f"Error converting PDF: {str(e)}")
            return filename, {'error': str(e)}, []

        extracted_data = {}
        original_lines = []
        page_count = len(pages)

        for page_number, page_data in enumerate(pages):
            try:
                # Convert page to grayscale and apply thresholding for better OCR accuracy
                image = np.array(page_data.convert('L'))
                _, thresh_image = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                processed_image = Image.fromarray(thresh_image)
                logger.info(f"Processed page {page_number} of {filename} for OCR")

                # Run OCR and extract text
                page_text = ocr_reader.readtext(np.array(processed_image), detail=0)
                page_text = "\n".join(page_text)
                original_lines.extend(page_text.split('\n'))

                # NLP-based Field Extraction
                for field in template['fields']:
                    name = field['name']
                    keyword = field['keyword']
                    separator = field.get('separator', ':')
                    index = field.get('index', '1')
                    indices = [int(i) for i in index.split(',')]
                    boundaries = field.get('boundaries', {'left': '', 'right': '', 'up': '', 'down': ''})
                    data_type = field.get('data_type', 'text')
                    multiline = field.get('multiline', False)

                    # Run NLP to find entities and potential matches
                    entities = nlp_ner(page_text)
                    matches = [ent['word'] for ent in entities if keyword.lower() in ent['word'].lower()]
                    
                    if matches:
                        extracted_data[name] = matches[0]
                    else:
                        # Fallback to custom extraction function for complex fields
                        extracted_data[name] = extract_value(page_text, keyword, separator, boundaries, data_type, indices, multiline)

                # Update progress
                with progress_lock:
                    global progress
                    progress += 1
                    overall_progress = int((progress / total_pages) * 100)
                    with open(progress_file, 'w') as pf:
                        logger.info(f"Current progress: {overall_progress}%")
                        pf.write(str(overall_progress))

            except Exception as e:
                logger.error(f"Error processing page {page_number} of {filename}: {e}")
                continue

        return filename, extracted_data, original_lines

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
                    value = extract_value(page_text, keyword, separator, boundaries, data_type, indices, multiline)
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
        use_enhanced = data.get('use_enhanced', False)
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
            if use_enhanced:
                futures = [executor.submit(enhanced_extract_from_pdf, filename, template, upload_folder, total_pages, progress_file) for filename in filenames]
            else:
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
