from flask import request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules.services.user_service import reduce_credits_for_user
from modules.logging_util import setup_logger
from modules.azure_extraction import extract_with_azure
from modules.progress_tracker import ProgressTracker
from modules.services.credit_service import validate_credits, reduce_credits
from modules.services.page_service import calculate_pages_to_process
import os

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
        user_id = get_jwt_identity()
        progress_tracker = ProgressTracker()
        page_config = data.get('page_config', {})
        logger.info(f"Page Config: {page_config}")

        # Validate input data
        is_valid, error_response, status_code = validate_input(data)
        if not is_valid:
            return error_response, status_code

        upload_folder = app.config['UPLOAD_FOLDER']
        # Create a user-specific progress file
        progress_file = os.path.join(upload_folder, f'progress_{user_id}.txt')

        filenames = data['filenames']
        extraction_model = data.get('extraction_model', 'NIRA AI - Printed Text (PB)').strip()
        azure_endpoint = app.config['AZURE_ENDPOINT']
        azure_key = app.config['AZURE_KEY']

        # Calculate total pages in the PDF
        total_pages = progress_tracker.calculate_total_pages(filenames, upload_folder)
        logger.info(f"Total Pages in PDF: {total_pages}")

        # Calculate pages to process
        pages_to_process = calculate_pages_to_process(page_config, total_pages)
        logger.info(f"Pages to Process: {pages_to_process}")

        if pages_to_process == 0:
            return jsonify({'message': 'No pages to process based on the configuration.'}), 400

        # Validate credit availability
        try:
            validate_credits(user_id, pages_to_process)
        except ValueError as e:
            logger.error(f"Credit validation failed: {e}")
            return jsonify({'message': str(e)}), 400

        # Initialize progress tracking
        progress_tracker.initialize_progress(progress_file)

        # Perform extraction
        try:
            results = perform_extraction(
                filenames, upload_folder, pages_to_process,
                progress_file, extraction_model, azure_endpoint, azure_key, progress_tracker, page_config
            )
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return jsonify({'message': 'Extraction process failed. Please try again later.'}), 500

        # Deduct credits after successful extraction
        try:
            reduce_credits(user_id, pages_to_process)
        except ValueError as e:
            logger.error(f"Credit deduction failed: {e}")
            return jsonify({'message': 'Credit deduction failed after successful extraction.'}), 500

        # Process results
        response_data, lines_data, csv_data, text_data, excel_paths = process_results(results)

        # Mark progress as 100%
        with open(progress_file, 'w') as pf:
            pf.write('100')

        return jsonify({
            'json_data': response_data,
            'lines_data': lines_data,
            'csv_data': csv_data,
            'text_data': text_data,
            'excel_paths': excel_paths
        }), 200

    @app.route('/progress', methods=['GET'])
    @jwt_required()
    def get_progress():
        """
        Fetches the progress of ongoing extractions.
        """
        user_id = get_jwt_identity()
        upload_folder = app.config['UPLOAD_FOLDER']
        progress_file = os.path.join(upload_folder, f'progress_{user_id}.txt')
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
        Ensures page_config is present for files with more than 10 pages.
        """
        if 'filenames' not in data:
            logger.error('Filenames are required')
            return False, jsonify({'message': 'Filenames are required'}), 400

        page_config = data.get('page_config', {})
        filenames = data['filenames']

        for filename in filenames:
            progress_tracker = ProgressTracker()
            total_pages = progress_tracker.get_total_pages(filename, app.config['UPLOAD_FOLDER'])
            if total_pages > 10 and filename not in page_config:
                logger.error(f"Page configuration is mandatory for files with more than 10 pages. Missing for {filename}")
                return False, jsonify({'message': f'Page configuration is mandatory for {filename} with more than 10 pages'}), 400

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
            original_lines = extracted_data.get('original_lines')  # Use original lines for lines_data

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
            file_data["excel_path"] = extracted_data.get('excel')
            file_data["text_data"] = extracted_data.get('text')

            # Append paths to respective lists
            if file_data["csv_data"]:
                csv_paths[filename] = file_data["csv_data"]
            if file_data["excel_path"]:
                excel_paths[filename] = file_data["excel_path"]
            if file_data["text_data"]:
                text_paths[filename] = file_data["text_data"]

            # Store extracted data and lines data
            response_data[filename] = file_data["json_data"]
            lines_data[filename] = original_lines  # Set lines_data using original lines
        return response_data, lines_data, csv_paths, text_paths, excel_paths

    def perform_extraction(filenames, upload_folder, total_pages, progress_file, extraction_model, azure_endpoint, azure_key, progress_tracker, page_config=None):
        """
        Performs extraction concurrently using Azure or template-based logic.
        Handles page-specific extraction based on page_config.
        """
        results = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            for filename in filenames:
                specified_pages = page_config.get(filename) if page_config else None
                logger.info(specified_pages)
                futures.append(
                    executor.submit(
                        extract_with_azure, filename, upload_folder, upload_folder, total_pages, progress_file, progress_tracker,
                        extraction_model, azure_endpoint, azure_key, specified_pages
                    )
                )

            for future in as_completed(futures):
                results.append(future.result())

        return results


