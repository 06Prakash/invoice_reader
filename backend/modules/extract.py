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


def register_extract_routes(app):
    @app.route('/extract', methods=['POST'])
    @jwt_required()
    def extract_data():
        """
        Handles data extraction from PDF files using either Azure Form Recognizer
        or template-based methods based on client requirements.
        """
        data = request.json

        # Create a tracker instance
        progress_tracker = ProgressTracker()
        
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
        extraction_model = data.get('extraction_model', 'NIRA AI - Printed Text (PB)').strip()
        azure_endpoint = app.config['AZURE_ENDPOINT']
        azure_key = app.config['AZURE_KEY']

        # Initialize progress tracking
        progress_tracker.initialize_progress(progress_file)

        # Determine total pages for progress tracking
        total_pages = progress_tracker.calculate_total_pages(filenames, upload_folder)

        # Perform extraction
        results = perform_extraction(
            filenames, template_name, template_folder, upload_folder, total_pages,
            progress_file, extraction_model, azure_endpoint, azure_key, progress_tracker
        )

        # Process results
        response_data, lines_data, csv_data, text_data, excel_paths = process_results(results)

        # Mark progress as 100%
        with open(progress_file, 'w') as pf:
            pf.write('100')

        # Return extracted data in multiple formats
        return jsonify({
            'json_data': response_data,  # Only the JSON content
            'lines_data': lines_data,    # Original lines
            'csv_data': csv_data,        # Combined CSV
            'text_data': text_data,      # Combined text
            'excel_paths': excel_paths   # List of Excel paths for downloads
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
    @jwt_required()
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
        Dynamically handles table-based and other extractions.

        :param results: List of results from concurrent extraction tasks
        :return: Processed response data, lines data, CSV paths, text paths, and a list of excel paths
        """
        response_data = {}
        lines_data = {}
        csv_paths = {}
        text_paths = {}
        excel_paths = {}

        for result in results:
            filename = result.get('filename')
            extracted_data = result.get('extracted_data', {})
            
            # Initialize storage for the file's data
            file_data = {
                "json_data": None,
                "csv_data": None,
                "excel_path": None,
                "text_data": None,
            }

            # Store paths for JSON, CSV, and Excel files
            file_data["json_data"] = extracted_data.get('json')
            file_data["csv_data"] = extracted_data.get('csv')
            if 'excel' in extracted_data:  # Table-based extraction 
                file_data["excel_path"] = extracted_data.get('excel')
            file_data["text_data"] = extracted_data.get('text')

            # Append paths to respective lists
            if file_data["csv_data"]:
                csv_paths[filename] = file_data["csv_data"]
            if file_data["excel_path"]:
                excel_paths[filename] = file_data["excel_path"]
            if file_data["text_data"]:
                text_paths[filename] = file_data["text_data"]

            # Store extracted data and set lines data
            response_data[filename] = file_data["json_data"]
            lines_data[filename] = extracted_data.get('text_data')  # No original lines for tables

        # elif isinstance(extracted_data, dict):  # Field-based extraction result
        #     # Handle field-based results directly
        #     response_data[filename] = extracted_data
        #     logger.info(extracted_data)
        #     if extract_data["csv_data"]:
        #         csv_paths[filename] = extract_data["csv_data"]
        #     if extract_data["excel_path"]:
        #         excel_paths[filename] = extract_data["excel_path"]
        #     if extract_data["text_data"]:
        #         text_paths[filename] = extract_data["text_data"]
        #     lines_data[filename] = extracted_data.get('text_data')

        return response_data, lines_data, csv_paths, text_paths, excel_paths

    def perform_extraction(filenames, template_name, template_folder, upload_folder, total_pages, progress_file, extraction_model, azure_endpoint, azure_key, progress_tracker):
        """
        Performs extraction concurrently using Azure or template-based logic.
        """
        results = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            for filename in filenames:
                futures.append(
                    executor.submit(
                        extract_with_azure, filename, upload_folder, upload_folder, total_pages, progress_file, progress_tracker, extraction_model, azure_endpoint, azure_key
                    )
                )

            for future in as_completed(futures):
                results.append(future.result())

        return results

