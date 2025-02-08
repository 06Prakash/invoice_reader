from flask import request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyPDF2 import PdfReader, PdfWriter
from werkzeug.utils import secure_filename
from modules.services.user_service import reduce_credits_for_user
from modules.logging_util import setup_logger
from modules.azure_extraction import extract_with_azure, upload_extraction_results_to_azure, delete_extracted_local_files,parse_page_ranges
from modules.progress_tracker import ProgressTracker
from modules.services.credit_service import validate_credits, reduce_credits
from modules.services.page_service import calculate_pages_to_process, calculate_file_pages_to_process
from modules.services.azure_blob_service import AzureBlobService
from modules.services.excel_service import consolidate_excel_sheets
from modules.services.upload_service import upload_files
from tempfile import NamedTemporaryFile
from io import BytesIO
import copy
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

        # Step 1: Validate Input and Initialize
        azure_blob_service, progress_tracker, page_config, filenames, extraction_model, upload_folder, azure_endpoint, azure_key, progress_file = initialize_extraction(data, user_id)
        saved_config = copy.deepcopy(page_config)

        # Step 2: Download Files from Azure
        file_paths, local_file_paths = download_files_from_azure(filenames, azure_blob_service, user_id, upload_folder)

        # step 3: Creating new pdfs with the provided page configs alone.
        logger.info(f"file_paths: {file_paths}")
        file_paths, page_config = create_small_pdf_with_config(file_paths, page_config, user_id, azure_blob_service)
        logger.info(f"file_paths: {file_paths}")
        logger.info(f"updated page_config: {page_config}")
        saved_config = copy.deepcopy(page_config)

        # Step 3: Calculate Pages to Process
        total_pages, pages_to_process = calculate_pages_and_validate_credits(file_paths, page_config, progress_tracker, user_id, upload_folder)

        # Step 4: Perform Extraction
        results, file_page_counts = perform_extraction_with_error_handling(
            filenames, file_paths, user_id, upload_folder, extraction_model,
            azure_endpoint, azure_key, azure_blob_service, progress_tracker, page_config, pages_to_process
        )

        # Retrieve Excel files to combine
        excel_files_to_combine = get_excel_files_to_combine(upload_folder, filenames, saved_config)
        logger.info(f"Excel files to combine: {excel_files_to_combine}")
        consolidated_file_path = None
        # Perform combining logic (if needed)
        if excel_files_to_combine:
            consolidated_file_path = os.path.join(upload_folder, f"{filenames[0].split('.')[0]}_Combined_Sections.xlsx")
            consolidate_excel_sheets(excel_files_to_combine, consolidated_file_path, saved_config)
            logger.info("Excel combining process completed.")
            try:
                uploaded_files = azure_blob_service.upload_file(user_id, consolidated_file_path, 'user_extract')
                logger.info(f"Uploaded consolidated file to Azure: {uploaded_files}")
            except Exception as e:
                logger.error(f"Failed to upload consolidated file to Azure: {e}")
            

        # Step 5: Upload Results to Azure
        response, successful_results = upload_results_to_azure(results, file_page_counts, page_config, azure_blob_service, user_id, consolidated_file_path)

        # Step 6: Deduct Credits for Successful Pages
        deduct_credits_for_successful_pages(successful_results, file_page_counts, page_config, user_id)

        progress_tracker.update_progress(progress_file, 0, pages_to_process, True)

        # Step 7: Clean Up Local Files
        cleanup_local_files(upload_folder, filenames)

        return jsonify(response), 200 if successful_results else 500

    def create_small_pdf_with_config(file_paths, page_config, user_id, azure_blob_service):
        """
        Updates the content of the files in file_paths based on the page configuration.
        The modified files overwrite the originals and are uploaded to Azure Blob Storage.

        Args:
            file_paths (dict): Dictionary where keys are file names and values are input PDF file paths.
            page_config (dict): Configuration containing page ranges for each PDF.
            user_id (str): User ID for organizing uploaded files in Azure Blob Storage.
            azure_blob_service (AzureBlobService): Instance of AzureBlobService to handle uploads.

        Returns:
            tuple: (file_paths, updated_page_config)
                - file_paths: The same dictionary passed as input, ensuring no changes.
                - updated_page_config: Updated page configuration reflecting new page numbers and preserving other attributes.
        """
        updated_page_config = {}

        try:
            for file_name, file_path in file_paths.items():
                if file_name in page_config:
                    logger.info(f"Processing file: {file_path}")
                    pdf_reader = PdfReader(file_path)
                    pdf_writer = PdfWriter()

                    config = page_config[file_name]
                    new_page_config = {}
                    current_page_number = 1  # Start numbering from 1 for the new PDF

                    # Generate new content based on page ranges
                    for section, details in config.items():
                        page_range = details['pageRange']
                        ranges = parse_page_ranges(page_range)
                        
                        page_numbers = [int(p) - 1 for p in ranges]

                        new_page_numbers = []
                        for page_num in page_numbers:
                            if 0 <= page_num < len(pdf_reader.pages):
                                pdf_writer.add_page(pdf_reader.pages[page_num])
                                new_page_numbers.append(current_page_number)
                                current_page_number += 1
                            else:
                                logger.warning(f"Page {page_num + 1} out of range for {file_name}")

                        if new_page_numbers:
                            updated_section = details.copy()  # Copy all existing keys in section
                            updated_section['pageRange'] = ",".join(map(str, new_page_numbers))
                            new_page_config[section] = updated_section
                        else:
                            logger.warning(f"No valid pages for section {section} in file {file_name}. Preserving original config.")
                            new_page_config[section] = details  # Preserve original config if no pages are valid

                    # Overwrite the original file with the modified PDF
                    with open(file_path, "wb") as output_file:
                        pdf_writer.write(output_file)

                    # Update the page configuration
                    updated_page_config[file_name] = new_page_config

                    # Upload the modified file to Azure Blob Storage
                    logger.info(f"Uploading modified file {file_path} for user {user_id}.")
                    azure_blob_service.upload_file(
                        user_id=user_id,
                        local_file_path=file_path,
                        folder_type="user_upload",  # Adjust folder type as needed
                        destination_filename=file_name
                    )

            return file_paths, updated_page_config

        except Exception as e:
            logger.error(f"Error in processing files: {str(e)}")
            raise


    def get_excel_files_to_combine(user_folder, filenames, page_config):
        """
        Retrieves the list of Excel files to combine. These files:
        - Have names prefixed with the filenames in the `filenames` list.
        - Have the extension `.xlsx`.
        - Contain the postfix `_sections_processed`.
        - Have the 'combine' flag set to True in the page_config.

        Args:
            user_folder (str): The user's folder.
            filenames (list): List of filenames (e.g., `file1.pdf`, `file2.pdf`).
            page_config (dict): Configuration dictionary with combine flags.

        Returns:
            list: List of file paths for Excel files matching the criteria.
        """
        try:
            if not os.path.exists(user_folder):
                logger.warning(f"User folder {user_folder} does not exist. Returning empty list.")
                return []

            # Base names from filenames (strip paths and extensions)
            base_filenames_with_ext = [os.path.basename(filename) for filename in filenames]  # Includes extension
            base_filenames = [os.path.splitext(os.path.basename(filename))[0] for filename in filenames]  # Without extension
            logger.info(f"File names base: {base_filenames}")
            logger.info(f"Page Config as needed for combining excel: {page_config}")

            # Check if the file's combine flag is True in the page_config
            combine_enabled_files = {
                base: section
                for base_with_ext, base in zip(base_filenames_with_ext, base_filenames)
                if base_with_ext in page_config  # Match with full filename in page_config
                for section, config in page_config[base_with_ext].items()
                if config.get("excel", {}).get("combine", False)
            }

            logger.info(f"Files eligible for combining based on page_config: {combine_enabled_files}")

            # Filter Excel files matching the criteria
            matching_files = []
            for file in os.listdir(user_folder):
                file_path = os.path.join(user_folder, file)
                if os.path.isfile(file_path) and file.endswith(".xlsx"):
                    # Check if the file starts with any base filename and ends with "_sections_processed.xlsx"
                    if any(file.startswith(base) and file.endswith("_sections_processed.xlsx") for base in combine_enabled_files):
                        matching_files.append(file_path)

            logger.info(f"Found matching Excel files for combining: {matching_files}")
            return matching_files

        except Exception as e:
            logger.error(f"Error while retrieving Excel files to combine: {e}")
            return []



    def cleanup_local_files(user_folder, filenames):
        """
        Cleans up only the files listed in the filenames variable and their related extracted files
        from the user-specific folder.

        Args:
            user_folder (str): The path to the user's folder.
            filenames (list): List of filenames (e.g., PDF files) to delete.
        """
        try:
            if not os.path.exists(user_folder):
                logger.warning(f"User folder {user_folder} does not exist. Skipping cleanup.")
                return

            # Extract base names without extensions from filenames
            base_filenames = [os.path.splitext(os.path.basename(filename))[0] for filename in filenames]

            # Define relevant extensions to match extracted files
            extracted_file_extensions = ['.json', '.csv', '.xlsx', '.txt', 'pdf']

            for file in os.listdir(user_folder):
                file_path = os.path.join(user_folder, file)

                # Check if the file matches any base filename with an extracted extension
                if any(file.startswith(base) and file.endswith(ext) for base in base_filenames for ext in extracted_file_extensions):
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        logger.info(f"Removed file: {file_path}")

        except Exception as e:
            logger.error(f"Error while cleaning up user-specific files: {e}")



    # Step 1: Initialize Extraction
    def initialize_extraction(data, user_id):
        logger.info(f"Initializing extraction for user {user_id}")
        page_config = data.get("page_config", {})
        filenames = data["filenames"]
        extraction_model = data.get('extraction_model', 'NIRA AI - Printed Text (PB)').strip()

        azure_blob_service = app.config["AZURE_BLOB_SERVICE"]
        azure_endpoint = app.config['AZURE_ENDPOINT']
        azure_key = app.config['AZURE_KEY']
        upload_folder = create_or_get_user_folder(user_id)
        progress_tracker = ProgressTracker()

        # Create progress file
        progress_file = os.path.join(upload_folder, f"progress_{user_id}.txt")
        progress_tracker.initialize_progress(progress_file)
        logger.info(f"Progress file initialized: {progress_file}")

        is_valid, error_response, status_code = validate_input(data, user_id, azure_blob_service)
        if not is_valid:
            logger.error("Input validation failed.")
            return error_response, status_code

        logger.info(f"Page Config: {page_config}")
        return azure_blob_service, progress_tracker, page_config, filenames, extraction_model, upload_folder, azure_endpoint, azure_key, progress_file

    # Step 2: Download Files from Azure
    def download_files_from_azure(filenames, azure_blob_service, user_id, upload_folder):
        """
        Downloads files from Azure and stores them in the user-specific folder.
        """
        logger.info("Downloading files from Azure.")
        file_paths = {}
        local_file_paths = []

        for filename in filenames:
            try:
                exact_file_name = filename.split("/")[-1]
                local_path = os.path.join(upload_folder, exact_file_name)
                with open(local_path, "wb") as local_file:
                    local_file.write(azure_blob_service.download_file(user_id, filename))
                file_paths[exact_file_name] = local_path
                local_file_paths.append(local_path)
                logger.info(f"Downloaded {exact_file_name} to {local_path}")
            except Exception as e:
                logger.error(f"Failed to download file {filename}: {e}")
                raise Exception("Error downloading files from Azure")

        return file_paths, local_file_paths



    # Step 3: Calculate Pages and Validate Credits
    def calculate_pages_and_validate_credits(file_paths, page_config, progress_tracker, user_id, upload_folder):
        total_pages = progress_tracker.calculate_total_pages(list(file_paths.keys()), upload_folder)
        logger.info(f"Total Pages in PDF: {total_pages}")

        pages_to_process = calculate_pages_to_process(page_config, total_pages)
        logger.info(f"Pages to Process: {pages_to_process}")
        if pages_to_process == 0:
            raise ValueError("No pages to process based on the configuration.")

        validate_credits(user_id, pages_to_process)
        return total_pages, pages_to_process

    # Step 4: Perform Extraction with Error Handling
    def perform_extraction_with_error_handling(filenames, file_paths, user_id, upload_folder, extraction_model, azure_endpoint, azure_key, azure_blob_service, progress_tracker, page_config, pages_to_process):
        try:
            progress_file = os.path.join(upload_folder, f"progress_{user_id}.txt")
            results, file_page_counts = perform_extraction(
                filenames, file_paths, user_id, upload_folder, progress_file, extraction_model,
                azure_endpoint, azure_key, azure_blob_service, progress_tracker, page_config, pages_to_process
            )
            logger.info(f"Extraction progress updated in {progress_file}")
            return results, file_page_counts
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise Exception("Extraction process failed. Please try again later.")



    # Step 5: Upload Results to Azure
    def upload_results_to_azure(results, file_page_counts, page_config, azure_blob_service, user_id, consolidated_file_path=None):
        """
        Uploads extraction results to Azure Blob Storage and updates the response.

        Args:
            results (list): List of extraction results.
            file_page_counts (dict): File page counts for credit calculation.
            page_config (dict): Configuration for page extraction.
            azure_blob_service (AzureBlobService): Azure blob service instance.
            user_id (str): User ID for organizing files.
            consolidated_file_path (str, optional): Path to the consolidated Excel file.

        Returns:
            tuple: Response dictionary and list of successful results.
        """
        response = {"extracted_files": {}, "failed_files": []}
        successful_results = []

        # Process individual extraction results
        for result in results:
            filename = result["filename"]
            if "error" in result:
                logger.error(f"Extraction failed for {filename}: {result['error']}")
                response["failed_files"].append(filename)
                continue
            if result['use_credit']:
                successful_results.append(result)

        # Upload successful extracted results
        for result in successful_results:
            filename = result["filename"]
            upload_extraction_results_to_azure(result["extracted_data"], filename, azure_blob_service, user_id)

        # Process successful results into response components
        # Handle consolidated Excel upload
        if consolidated_file_path:
            try:
                # Use the prefix from one of the file names in the results
                prefix = successful_results[0]["filename"].split(".")[0] if successful_results else "Consolidated"
                consolidated_filename = f"{prefix}_Combined_Sections.xlsx"
                consolidated_blob_path = azure_blob_service.upload_file(
                    user_id, consolidated_file_path, folder_type='user_extract', destination_filename=consolidated_filename
                )[0]  # Upload returns a list, take the first item
                logger.info(f"Uploaded consolidated Excel file to Azure: {consolidated_blob_path}")
            except Exception as e:
                logger.error(f"Failed to upload consolidated Excel file to Azure: {e}")
                combined_excel_paths = None
        response_data, lines_data, csv_data, text_data, excel_paths, combined_excel_paths = process_results(successful_results, consolidated_file_path)
        response.update({
            'json_data': response_data,
            'lines_data': lines_data,
            'csv_data': csv_data,
            'text_data': text_data,
            'excel_paths': excel_paths,
            'combined_excel_paths': combined_excel_paths
        })


        return response, successful_results



    # Step 6: Deduct Credits for Successful Pages
    def deduct_credits_for_successful_pages(successful_results, file_page_counts, page_config, user_id):
        successful_pages = 0

        for result in successful_results:
            filename = result['filename']
            if filename in file_page_counts:
                pages_to_process = calculate_file_pages_to_process(page_config.get(filename, None), file_page_counts[filename])
                successful_pages += pages_to_process

        if successful_pages > 0:
            reduce_credits(user_id, successful_pages)
            logger.info(f"Deducted {successful_pages} credits for user {user_id}.")
        else:
            raise ValueError("Extraction failed due to page config error.")

    def create_or_get_user_folder(user_id):
        """
        Creates a user-specific subfolder under the UPLOAD_FOLDER.
        """
        upload_folder = app.config["UPLOAD_FOLDER"]
        user_folder = os.path.join(upload_folder, user_id)
        os.makedirs(user_folder, exist_ok=True)
        logger.info(f"User-specific folder created: {user_folder}")
        return user_folder

    @app.route('/progress', methods=['GET'])
    @jwt_required()
    def get_progress():
        """
        Fetches the progress of ongoing extractions.
        """
        user_id = get_jwt_identity()
        upload_folder = create_or_get_user_folder(user_id)
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
        Serves the file for download directly from Azure Blob Storage.
        """
        user_id = get_jwt_identity()  # Assuming JWT token contains user_id
        azure_blob_service = app.config["AZURE_BLOB_SERVICE"]
        folder_type = 'user_extract'  # Adjust folder_type as needed

        try:
            # Call the Azure Blob download method
            content = azure_blob_service.download_file(user_id, filename, folder_type)

            # Prepare the response for file download
            response = Response(content, mimetype='application/octet-stream')
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            return response

        except Exception as e:
            logger.error(f"Error while downloading file {filename} for user {user_id}: {e}")
            return {"error": f"Failed to download the file: {e}"}, 500
    
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

    def process_results(results, consolidated_file_path = None):
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
        combined_excel_paths = {}

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
                "combined_excel_paths": None
            }

            # Store paths for JSON, CSV, and Excel files
            file_data["json_data"] = extracted_data.get('json')
            file_data["csv_data"] = extracted_data.get('csv')
            file_data["excel_path"] = extracted_data.get('excel')
            file_data["text_data"] = extracted_data.get('text')
            file_data["combined_excel_paths"] = consolidated_file_path

            # Append paths to respective lists
            if file_data["csv_data"]:
                csv_paths[filename] = file_data["csv_data"]
            if file_data["excel_path"]:
                excel_paths[filename] = file_data["excel_path"]
            if file_data["text_data"]:
                text_paths[filename] = file_data["text_data"]
            if file_data["combined_excel_paths"]:
                combined_excel_paths[filename] = file_data["combined_excel_paths"]

            # Store extracted data and lines data
            response_data[filename] = file_data["json_data"]
            lines_data[filename] = original_lines  # Set lines_data using original lines
        return response_data, lines_data, csv_paths, text_paths, excel_paths, combined_excel_paths

    def perform_extraction(
        filenames, file_paths, user_id, upload_folder, progress_file, extraction_model,
        azure_endpoint, azure_key, azure_blob_service, progress_tracker, page_config=None, pages_to_process = 0
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
                        extract_with_azure, filename, user_id, azure_blob_service, upload_folder, pages_to_process,
                        total_pages, progress_file, progress_tracker, extraction_model, azure_endpoint, azure_key, specified_pages
                    )
                )

            # Collect results as tasks complete
            for future in as_completed(futures):
                results.append(future.result())

        return results, file_page_counts
