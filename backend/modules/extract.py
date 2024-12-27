from flask import request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        is_valid, error_response, status_code = validate_input(data)
        if not is_valid:
            return error_response, status_code

        # Get configurations from app.config
        upload_folder = app.config['UPLOAD_FOLDER']
        template_folder = app.config['TEMPLATE_FOLDER']
        progress_file = os.path.join(upload_folder, 'progress.txt')

        # Extract filenames and template details
        filenames = data['filenames']
        template_name = data['template']
        extraction_model = data.get('extraction_model', 'NIRA Standard').strip()
        azure_endpoint = app.config['AZURE_ENDPOINT']
        azure_key = app.config['AZURE_KEY']

        # Initialize progress tracking
        progress_tracker.initialize_progress(progress_file)

        # Determine total pages for progress tracking
        total_pages = progress_tracker.calculate_total_pages(filenames, upload_folder)

        # Perform extraction
        results = perform_extraction(filenames, template_name, template_folder, upload_folder, total_pages, progress_file, extraction_model, azure_endpoint, azure_key)

        # Process results
        response_data, lines_data, csv_data, text_data = process_results(results)

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

    @app.route('/downloads/<filename>', methods=['GET'])
    def download_file(filename):
        """
        Serves the Excel file for download.
        """
        output_folder = app.config['OUTPUT_FOLDER']  # Add OUTPUT_FOLDER to your config
        return send_from_directory(output_folder, filename, as_attachment=True)
    
    ##############################################################
    ################ Non routing functions #######################
    ##############################################################
    def validate_input(data):
        """
        Validates the input data for the extraction request.
        """
        if 'filenames' not in data or 'template' not in data:
            logger.error('Filenames and template are required')
            return False, jsonify({'message': 'Filenames and template are required'}), 400
        return True, None, None

    def process_results(results):
        """
        Processes the results from concurrent extraction tasks.
        """
        response_data = {filename: data for filename, data, _ in results}
        lines_data = {filename: lines for filename, _, lines in results}

        csv_output = io.StringIO()
        csv_writer = csv.writer(csv_output)
        headers = set()

        # Collect headers from all results
        for _, data, _ in results:
            if isinstance(data, dict):
                headers.update(data.keys())
            elif isinstance(data, list) and data:
                for item in data:
                    if isinstance(item, dict):
                        headers.update(item.keys())

        # Write headers and rows to CSV
        csv_writer.writerow(['filename'] + list(headers))
        for filename, data, _ in results:
            if isinstance(data, dict):
                row = [filename] + [data.get(header, '') for header in headers]
                csv_writer.writerow(row)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        row = [filename] + [item.get(header, '') for header in headers]
                        csv_writer.writerow(row)

        csv_data = csv_output.getvalue()

        text_data = ""
        for filename, data, _ in results:
            text_data += f"File: {filename}\n"
            if isinstance(data, dict):
                text_data += "\n".join([f"{key}: {value}" for key, value in data.items()])
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        text_data += "\n".join([f"{key}: {value}" for key, value in item.items()])
                        text_data += "\n"
            else:
                text_data += f"Unhandled data type: {type(data)}\n"
            text_data += "\n"

        return response_data, lines_data, csv_data, text_data


    def perform_extraction(filenames, template_name, template_folder, upload_folder, total_pages, progress_file, extraction_model, azure_endpoint, azure_key):
        """
        Performs extraction concurrently using Azure or template-based logic.
        """
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

        return results
