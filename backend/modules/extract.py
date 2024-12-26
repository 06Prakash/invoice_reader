from flask import request, jsonify
from flask_jwt_extended import jwt_required
from concurrent.futures import ThreadPoolExecutor, as_completed
from pdf2image import convert_from_path
from .logging_util import setup_logger
from .azure_extraction import extract_with_azure
from .template_extraction import extract_with_template_logic
from .progress_tracker import ProgressTracker
import os
import json
import csv
import io

logger = setup_logger()
# Create a tracker instance
progress_tracker = ProgressTracker()


def register_extract_routes(app):
    @app.route('/extract', methods=['POST'])
    @jwt_required()
    def extract_data():
        """
        Handles data extraction from PDF files using either Azure Form Recognizer
        or template-based methods based on client requirements.
        """
        data = request.json

        # Validate input data
        if 'filenames' not in data or 'template' not in data:
            logger.error('Filenames and template are required')
            return jsonify({'message': 'Filenames and template are required'}), 400

        # Get configurations from app.config
        upload_folder = app.config['UPLOAD_FOLDER']
        template_folder = app.config['TEMPLATE_FOLDER']
        logger.info(template_folder)
        progress_file = os.path.join(upload_folder, 'progress.txt')

        # Extract filenames and template details
        filenames = data['filenames']
        template_name = data['template']
        extraction_model = data.get('extraction_model', 'NIRA Standard').strip()
        azure_endpoint = app.config['AZURE_ENDPOINT']
        azure_key = app.config['AZURE_KEY']
        # output_format = data.get('output_format', 'json')

        # Initialize progress tracking
        with open(progress_file, 'w') as pf:
            pf.write('0')

        # # Load template
        # template_path = os.path.join(template_folder, f'{template_name}.json')
        # logger.info(template_path)
        # if not os.path.exists(template_path):
        #     logger.error('Template not found')
        #     return jsonify({'message': 'Template not found'}), 404

        # with open(template_path, 'r') as f:
        #     template = json.load(f)

        # Determine total pages for progress tracking
        total_pages = sum(len(convert_from_path(os.path.join(upload_folder, filename), 300)) for filename in filenames)
        # Reset progress tracker
        progress_tracker.reset_progress()

        # Use ThreadPoolExecutor for concurrent processing
        results = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            for filename in filenames:
                if 'nira standard' in extraction_model.lower():
                    futures.append(
                        executor.submit(
                            extract_with_template_logic, filename, template_name, template_folder, upload_folder, total_pages, progress_file, progress_tracker
                        )
                    )
                else:
                    futures.append(
                        executor.submit(
                            extract_with_azure, filename, upload_folder, total_pages, progress_file, progress_tracker, extraction_model, azure_endpoint, azure_key
                        )
                    )

            for future in as_completed(futures):
                results.append(future.result())

        # Process results
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

        # Mark progress as 100%
        with open(progress_file, 'w') as pf:
            pf.write('100')

        # Return extracted data in multiple formats
        return jsonify({
            'json_data': response_data,
            'lines_data': lines_data,
            'csv_data': csv_data,
            'text_data': text_data
        }), 200

    @app.route('/progress', methods=['GET'])
    @jwt_required()
    def get_progress():
        """
        Fetches the progress of ongoing extractions.
        """
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
        Returns a list of available extraction models.
        """
        try:
            extraction_models = [
                "NIRA standard",
                "NIRA AI - handwritten (Custom)",
                "NIRA AI - Invoice (PB)",
                "NIRA AI - Printed Text (PB)",
                "NIRA AI - Printed Tables (PB)",
                "NIRA AI - Printed business card (PB)",
                "NIRA AI - Printed receipt (PB)"
            ]
            logger.info("Extraction models fetched successfully.")
            return jsonify({"models": extraction_models}), 200
        except Exception as e:
            logger.error(f"Error fetching extraction models: {e}")
            return jsonify({"error": "Failed to fetch extraction models"}), 500
