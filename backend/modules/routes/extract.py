from flask import request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyPDF2 import PdfReader
from modules.services.user_service import reduce_credits_for_user
from modules.logging_util import setup_logger
from modules.azure_extraction import extract_with_azure, upload_extraction_results_to_azure
from modules.progress_tracker import ProgressTracker
from modules.services.credit_service import validate_credits, reduce_credits
from modules.services.page_service import calculate_pages_to_process, calculate_file_pages_to_process
from modules.services.azure_blob_service import AzureBlobService
import os

logger = setup_logger(__name__)


def register_extract_routes(app):
    @app.route('/extract', methods=['POST'])
    @jwt_required()
    def extract_data():
        """
        Handles data extraction from PDF files using Azure Form Recognizer
        and uploads results to Azure Blob Storage.
        """
        data = request.json
        user_id = get_jwt_identity()
        progress_tracker = ProgressTracker()
        page_config = data.get("page_config", {})
        logger.info(f"Page Config: {page_config}")

        # Validate input data
        # Azure-specific configurations
        azure_container = app.config["AZURE_STORAGE_CONTAINER"]
        azure_connection_string = app.config["AZURE_STORAGE_CONNECTION_STRING"]
        azure_blob_service = AzureBlobService(azure_connection_string, azure_container)
        is_valid, error_response, status_code = validate_input(data, user_id, azure_blob_service)
        if not is_valid:
            return error_response, status_code


        # Create a temporary folder for file operations
        upload_folder = app.config["UPLOAD_FOLDER"]
        progress_file = os.path.join(upload_folder, f"progress_{user_id}.txt")
        filenames = data["filenames"]
        extraction_model = data.get('extraction_model', 'NIRA AI - Printed Text (PB)').strip()
        azure_endpoint = app.config['AZURE_ENDPOINT']
        azure_key = app.config['AZURE_KEY']

        # Download files from Azure
        file_paths = {}
        try:
            for filename in filenames:
                # Download file locally
                # local_path =  filename.split("/")
                exact_file_name = filename.split("/")[-1]
                local_path = os.path.join(upload_folder, exact_file_name)
                logger.info(f"Attempting to download file {filename}")
                with open(local_path, "wb") as local_file:
                    local_file.write(azure_blob_service.download_file(user_id, filename))
                file_paths[exact_file_name] = local_path
                logger.info(f"Downloaded {exact_file_name} to {local_path}")

        except Exception as e:
            logger.error(f"Failed to download files from Azure: {e}")
            return jsonify({"message": "Error downloading files from Azure"}), 500

        # Perform extraction
        results = []
        try:
            results, file_page_counts = perform_extraction(
                filenames, file_paths, user_id, upload_folder, progress_file, extraction_model,
                azure_endpoint, azure_key, azure_blob_service, progress_tracker, page_config
            )
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return jsonify({"message": "Extraction process failed. Please try again later."}), 500

        # Upload extraction results to Azure
        response = {"extracted_files": {}, "failed_files": []}
        file_upload_data = {}
        successful_results = []
        try:
            for result in results:
                filename = result["filename"]
                if "error" in result:
                    logger.error(f"Extraction failed for {filename}: {result['error']}")
                    response["failed_files"].append(filename)
                    continue
                successful_results.append(result)
            for result in successful_results:
                filename = result["filename"]
                logger.info("Inside the expected successful results files..")
                # Upload processed files to Azure
                for file_type, local_file_path in result["extracted_data"].items():
                    if file_type in ["text_data", "original_lines"]:
                        continue
                    logger.info(f"Inside the {file_type} for expected successful result file {local_file_path}..")
                    if not local_file_path or not os.path.exists(local_file_path):
                        logger.info(f"Path {local_file_path} not exists")
                        continue
                    upload_extraction_results_to_azure(result["extracted_data"], filename, azure_blob_service, user_id)
                    azure_file_path = azure_blob_service.generate_blob_name(user_id, filename.split("/")[-1], 'user_extract')
                    logger.info(f"Got the azure file path as {azure_file_path}")
                    # response["extracted_files"].setdefault(filename, {})[file_type] = local_file_path
            response_data, lines_data, csv_data, text_data, excel_paths = process_results(successful_results)
             # Log failed files
            if len(response["failed_files"]) > 0:
                logger.warning(f"The following files failed during extraction: {response['failed_files']}")
            # Deduct credits for successfully processed files only
            successful_pages = 0
            for result in successful_results:
                filename = result['filename']
                if filename in file_page_counts:
                    logger.info("-=-=-=-=-==")
                    logger.info(file_page_counts[filename])
                    logger.info("-=-=-=-=-==")
                    pages_to_process = calculate_file_pages_to_process(page_config.get(filename, None), file_page_counts[filename])
                    successful_pages += pages_to_process
            if successful_pages > 0:
                try:
                    reduce_credits(user_id, successful_pages)
                    logger.info(f"Deducted {successful_pages} credits for user {user_id}.")
                except ValueError as e:
                    logger.error(f"Credit deduction failed: {e}")
                    return jsonify({'message': 'Credit deduction failed after successful extraction.'}), 500

        except Exception as e:
            logger.error(f"Failed to upload extracted results to Azure: {e}")
            return jsonify({"message": "Error uploading extraction results to Azure"}), 500

        # Prepare response
        if response["failed_files"]:
            logger.warning(f"Some files failed during extraction: {response['failed_files']}")

        response = {
            'json_data': response_data,
            'lines_data': lines_data,
            'csv_data': csv_data,
            'text_data': text_data,
            'excel_paths': excel_paths,
        }
        logger.info(f"Final extracted data: {response}")

        return jsonify(response), 200 if successful_results else 500


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
    def validate_input(data, user_id, azure_blob_service):
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
            blob_name = azure_blob_service.generate_blob_name(user_id, filename, 'user_upload')
            try:
                total_pages = azure_blob_service.get_total_pages_from_azure(blob_name)
                logger.info(f"Total Pages: {total_pages}")
                if total_pages > 10 and filename not in page_config:
                    logger.error(f"Page configuration is mandatory for files with more than 10 pages. Missing for {filename}")
                    return False, jsonify({'message': f'Page configuration is mandatory for {filename} with more than 10 pages'}), 400
            except Exception as e:
                logger.error(f"Failed to validate {filename}: {e}")
                return False, jsonify({'message': f'Failed to validate {filename}: {e}'}), 500

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

    def perform_extraction(
        filenames, file_paths, user_id, upload_folder, progress_file, extraction_model,
        azure_endpoint, azure_key, azure_blob_service, progress_tracker, page_config=None
    ):
        """
        Orchestrates the extraction process for multiple files using Azure Form Recognizer.
        :param filenames: List of filenames to process
        :param file_paths: Dictionary mapping filenames to their local file paths
        :param user_id: ID of the user performing the extraction
        :param upload_folder: Local folder containing uploaded files
        :param progress_file: Path to the progress tracking file
        :param extraction_model: Model to use for extraction
        :param azure_endpoint: Azure Form Recognizer endpoint
        :param azure_key: Azure Form Recognizer key
        :param azure_blob_service: Azure Blob service instance
        :param progress_tracker: Instance of ProgressTracker for updating progress
        :param page_config: Optional page configurations for each file
        :return: Results and page counts for each file
        """
        results = []
        file_page_counts = {}  # Track page count for each file

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []

            for filename in filenames:
                # Get local file path for the current file
                pdf_path = file_paths.get(filename)
                if not pdf_path:
                    logger.error(f"File path for {filename} not found.")
                    results.append({"filename": filename, "error": "File path not found."})
                    continue

                # Calculate total pages for the current file
                try:
                    reader = PdfReader(pdf_path)
                    total_pages = len(reader.pages)
                    logger.info(f"Total pages for {filename}: {total_pages}")
                    file_page_counts[filename] = total_pages
                except Exception as e:
                    logger.error(f"Error calculating total pages for {filename}: {e}")
                    results.append({"filename": filename, "error": f"Failed to calculate total pages: {e}"})
                    continue

                # Get page config for the current file
                specified_pages = page_config.get(filename) if page_config else None
                logger.info(f"Specified pages for {filename}: {specified_pages}")

                # Submit extraction task
                futures.append(
                    executor.submit(
                        extract_with_azure, filename, user_id, pdf_path, azure_blob_service, upload_folder,
                        total_pages, progress_file, progress_tracker, extraction_model, azure_endpoint, azure_key, specified_pages
                    )
                )

            # Collect results as tasks complete
            for future in as_completed(futures):
                results.append(future.result())

        return results, file_page_counts
