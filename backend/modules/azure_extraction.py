import os
import pandas as pd
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient
import tempfile
from .data_processing import process_field, flatten_nested_field
from .logging_util import setup_logger
from modules.services.excel_service import save_sections_to_excel_and_csv
from modules.services.azure_blob_service import AzureBlobService  # Import the AzureBlobService
import csv
import json
from concurrent.futures import ThreadPoolExecutor
from azure.core.exceptions import HttpResponseError

logger = setup_logger(__name__)

# Mapping function for user-friendly model names to Azure-recognized model names
def extraction_model_mapping(model_name):
    """
    Maps user-friendly model names to Azure-recognized model names.
    """
    # Remove trailing "(text)" dynamically if present
    clean_model_name = model_name.split(" (")[0]

    model_mapping = {
        "NIRA AI - handwritten": "MutualFundModelSundaramFinance",
        "NIRA AI - Invoice": "prebuilt-invoice",
        "NIRA AI - Printed Text": "prebuilt-read",
        "NIRA AI - Printed Tables": "prebuilt-layout",
        "NIRA AI - Printed business card": "prebuilt-businessCard",
        "NIRA AI - Printed receipt": "prebuilt-receipt",
    }
    return model_mapping.get(clean_model_name, "prebuilt-read")  # Default to "prebuilt-read"

def process_table_extraction(result, filename, output_folder, progress_tracker, progress_file, total_pages):
    """
    Processes the Azure Form Recognizer result for table extraction and generates outputs.
    Includes raw table data and original lines in the return value.
    """
    tables = []
    outputs = {}

    # Extract tables directly from result.tables
    if hasattr(result, 'tables') and result.tables:
        for table in result.tables:
            rows = []
            for row_index in range(table.row_count):
                row = []
                for cell in table.cells:
                    if cell.row_index == row_index:
                        row.append(cell.content)
                rows.append(row)
            tables.append(pd.DataFrame(rows))
            progress_tracker.update_progress(progress_file, 1, total_pages)
    else:
        logger.warning(f"No tables found in {filename}")
        outputs['error'] = f"No tables found in {filename}"

    # Save CSV output
    try:
        csv_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_tables.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            if tables:
                for idx, table in enumerate(tables):
                    table.to_csv(csv_file, index=False)
                    csv_file.write("\n")  # Separate tables with a newline
            else:
                csv_file.write("No data extracted\n")  # Placeholder if no tables
        logger.info(f"Tables saved as CSV at {csv_path}")
        outputs['csv'] = csv_path
    except Exception as e:
        logger.error(f"Failed to save tables to CSV for {filename}: {e}")
        outputs['csv_error'] = str(e)

    # Save Text output (structured data only)
    try:
        text_data = ""
        if tables:
            for idx, table in enumerate(tables):
                text_data += f"Table {idx + 1}:\n"
                text_data += table.to_string(index=False, header=False)
                text_data += "\n\n"
        else:
            text_data = "No data extracted\n"  # Placeholder if no tables
        text_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_tables.txt")
        with open(text_path, "w", encoding="utf-8") as text_file:
            text_file.write(text_data)
        logger.info(f"Tables saved as Text at {text_path}")
        outputs['text'] = text_path
        outputs['text_data'] = text_data
    except Exception as e:
        logger.error(f"Failed to save tables to Text for {filename}: {e}")
        outputs['text_error'] = str(e)

    # Always include raw tables and original lines
    outputs['raw_tables'] = tables if tables else [pd.DataFrame([["No Data Extracted"]])]
    outputs['original_lines'] = outputs.get('text_data', '')

    return outputs



def process_text_extraction(result, filename, output_folder, progress_tracker, progress_file, total_pages, extra_requirements = None):
    """
    Processes text-based extraction results and updates progress.

    :param result: The result object from Azure Form Recognizer
    :param filename: The name of the file being processed
    :param output_folder: The folder to save extracted outputs
    :param progress_tracker: Progress tracker instance
    :param progress_file: Path to track extraction progress
    :param total_pages: Total number of pages to process
    :return: Outputs dictionary including text file path and original lines
    """
    text_data = ""
    original_lines = []

    # Extract text and original lines from pages
    if hasattr(result, 'pages'):
        for page in result.pages:
            for line in page.lines:
                original_lines.append(line.content)  # Store original lines
                text_data += line.content + "\n"  # Append lines to create a text block

    # Update progress
    progress_tracker.update_progress(progress_file, 1, total_pages)

    # Initialize output paths
    outputs = {}

    # Save Text output (structured text)
    text_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_text.txt")
    with open(text_path, "w", encoding="utf-8") as text_file:
        text_file.write(text_data.strip())
    outputs['text'] = text_path
    outputs['text_data'] = text_data

    # Add original lines as a separate field
    outputs['original_lines'] = "\n".join(original_lines)

    return outputs

def process_field_extraction(result, filename, output_folder, progress_tracker, progress_file, total_pages):
    """
    Processes field-based extraction results and updates progress.

    :param result: The result object from Azure Form Recognizer
    :param filename: The name of the file being processed
    :param output_folder: The folder to save extracted outputs
    :param progress_tracker: Progress tracker instance
    :param progress_file: Path to track extraction progress
    :param total_pages: Total number of pages to process
    :return: Outputs dictionary including JSON, text, CSV, Excel paths, original lines, and raw_tables key
    """
    extracted_data = {}
    original_lines = []

    # Extract fields from documents
    if hasattr(result, 'documents'):
        for doc in result.documents:
            for name, field in doc.fields.items():
                field_value = process_field(field)
                if isinstance(field_value, (dict, list)):
                    extracted_data[name] = flatten_nested_field(field_value)
                else:
                    extracted_data[name] = field_value

    # Create original lines from extracted data
    if extracted_data:
        for key, value in extracted_data.items():
            original_lines.append(f"{key}: {value}")

    # Update progress after processing fields
    progress_tracker.update_progress(progress_file, 1, total_pages)

    # Initialize output paths
    outputs = {}

    # Save JSON output
    json_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_fields.json")
    with open(json_path, "w") as json_file:
        json.dump(extracted_data, json_file, indent=2)
    outputs['json'] = json_path

    # Save Text output (original lines)
    text_data = "\n".join(original_lines) if original_lines else "No text found"
    text_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_fields.txt")
    with open(text_path, "w", encoding="utf-8") as text_file:
        text_file.write(text_data)
    outputs['text'] = text_path
    outputs['original_lines'] = text_data

    outputs['text_data'] = text_data

    # Save CSV output
    csv_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_fields.csv")
    csv_data = [{"Field": k, "Value": v} for k, v in extracted_data.items()]
    if csv_data:
        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=["Field", "Value"])
            writer.writeheader()
            writer.writerows(csv_data)
        outputs['csv'] = csv_path

    # Save Excel output
    excel_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_fields.xlsx")
    if csv_data:
        df = pd.DataFrame(csv_data)
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Fields", index=False)
        outputs['excel'] = excel_path

    # Add raw_tables key for further processing
    outputs['raw_tables'] = csv_data

    return outputs


def extract_original_lines(result):
    original_lines = []
    # Extract original lines
    for page in result.pages:
        for line in page.lines:
            original_lines.append(line.content)

    return "\n".join(original_lines)

def process_based_on_model(result, filename, section, output_folder, progress_tracker, progress_file, total_pages, mapped_model):
    if mapped_model == "prebuilt-layout":
        return process_table_extraction(result, f"{filename}_{section}", output_folder, progress_tracker, progress_file, total_pages)
    elif mapped_model == "MutualFundModelSundaramFinance":
        return process_field_extraction(result, f"{filename}_{section}", output_folder, progress_tracker, progress_file, total_pages)
    else:
        return process_text_extraction(result, f"{filename}_{section}", output_folder, progress_tracker, progress_file, total_pages)

def extract_with_azure(
    filename, user_id, pdf_path, azure_blob_service, output_folder, total_pages, progress_file, progress_tracker,
    extraction_model, azure_endpoint, azure_key, page_config=None
):
    """
    Extracts data from a PDF using Azure Form Recognizer and processes it based on the extraction type.
    Handles section-specific page configurations and supports chunked page processing.
    Also integrates with Azure Blob Storage for file download and upload.
    """
    # Retrieve chunk size from environment variables or use default
    chunk_size = int(os.getenv("AZURE_CHUNK_SIZE", 2))

    # Generate user-specific file path for Azure Blob
    user_file_path = f"{user_id}/{filename}"

    # Initialize Azure clients
    document_analysis_client = DocumentAnalysisClient(
        endpoint=azure_endpoint,
        credential=AzureKeyCredential(azure_key)
    )

    temp_pdf_path = ""
    try:
        # Download the file from Azure Blob Storage
        logger.info(f"Downloading file {user_file_path} from Azure Blob Storage")
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(azure_blob_service.download_file(user_id, filename.split("/")[-1]))
            temp_pdf_path = temp_file.name
        logger.info(f"File downloaded to temporary path: {temp_pdf_path}")
    except Exception as e:
        logger.error(f"Failed to download file {filename} from Azure: {e}")
        return {"filename": filename, "error": f"Failed to download file from Azure: {e}"}

    # Ensure extra_requirements is not None
    extra_requirements = page_config or {}

    try:
        mapped_model = extraction_model_mapping(extraction_model)
        logger.info(f"Using Azure model: {mapped_model} for extraction")

        section_data = {}
        outputs = {"json": None, "csv": None, "text": None, "excel": None, "text_data": "", "original_lines": ""}

        def split_pages(pages, chunk_size):
            """Splits a list of pages into valid chunks."""
            for i in range(0, len(pages), chunk_size):
                chunk = pages[i:i + chunk_size]
                if max(chunk) <= total_pages:
                    yield chunk
                else:
                    logger.warning(f"Skipping invalid chunk: {chunk}")

        if page_config:
            for section, config in page_config.items():
                try:
                    logger.info(f"Extracting section: {section} with config: {config}")
                    page_range = config.get("pageRange")
                    if not page_range:
                        raise ValueError(f"Missing pageRange for section {section}")

                    if isinstance(page_range, list):
                        page_list = page_range
                    elif isinstance(page_range, str):
                        page_list = list(parse_page_ranges(page_range.replace(" ", "").strip()))
                    else:
                        raise ValueError(f"Invalid page_range format for section {section}: {page_range}")

                    for chunk in split_pages(page_list, chunk_size):
                        pages = ",".join(map(str, chunk))
                        logger.info(f"Processing chunk for section {section}: {pages}")

                        with open(temp_pdf_path, "rb") as document:
                            poller = document_analysis_client.begin_analyze_document(mapped_model, document, pages=pages)
                            result = poller.result()

                        section_outputs = process_based_on_model(
                            result, filename, section, output_folder, progress_tracker, progress_file, total_pages, mapped_model
                        )

                        # Process outputs and aggregate them
                        if "raw_tables" in section_outputs:
                            section_data.setdefault(section, {}).setdefault("raw_tables", []).extend(
                                section_outputs["raw_tables"]
                            )

                        if "json" in section_outputs:
                            section_data.setdefault(section, {}).update(section_outputs["json"])

                        outputs["text_data"] += f"\n{section_outputs.get('text_data', '')}"
                        outputs["original_lines"] += f"\n{section_outputs.get('original_lines', '')}"

                        if "csv" in section_outputs:
                            outputs["csv"] = section_outputs["csv"]
                        
                        if "json" in section_outputs:
                            outputs['json'] = section_outputs[""]

                except HttpResponseError as e:
                    logger.error(f"Error processing section {section}: {e}")
                except Exception as section_error:
                    logger.error(f"Unexpected error processing section {section}: {section_error}")

        else:
            all_pages = list(range(1, total_pages + 1))
            for chunk in split_pages(all_pages, chunk_size):
                pages = ",".join(map(str, chunk))
                logger.info(f"Processing chunk: {pages}")

                with open(temp_pdf_path, "rb") as document:
                    poller = document_analysis_client.begin_analyze_document(mapped_model, document, pages=pages)
                    result = poller.result()

                full_outputs = process_based_on_model(
                    result, filename, "Full Document", output_folder, progress_tracker, progress_file, total_pages, mapped_model
                )

                section_data.setdefault("Full Document", {}).setdefault("raw_tables", []).extend(
                    full_outputs.get("raw_tables", [])
                )
                if "json" in full_outputs:
                    outputs['json'] = full_outputs.get("json")

                outputs["text_data"] += full_outputs.get("text_data", "")
                outputs["original_lines"] += full_outputs.get("original_lines", "")
                if full_outputs.get("csv"):
                    outputs["csv"] = full_outputs.get("csv", "No CSV Data")

        # Save results locally
        outputs = save_extraction_results(section_data, filename, output_folder, outputs, extra_requirements)

        logger.info(f"Extraction completed successfully for {filename}")
        return {"filename": filename, "extracted_data": outputs}

    except Exception as e:
        logger.error(f"Azure extraction failed for {filename}: {e}")
        return {"filename": filename, "error": str(e)}

    finally:
        if os.path.exists(temp_pdf_path):
            os.unlink(temp_pdf_path)
            logger.info(f"Temporary file {temp_pdf_path} has been deleted.")

def parse_page_ranges(page_ranges):
    """
    Converts a page range string like "1,3-4" to a list of individual page numbers.
    """
    pages = set()
    ranges = page_ranges.split(",")
    for r in ranges:
        if "-" in r:
            start, end = map(int, r.split("-"))
            pages.update(range(start, end + 1))
        else:
            pages.add(int(r))
    return sorted(pages)

def process_table_section(result, section_name):
    """
    Extracts table data for a specific section from the Azure Form Recognizer result.
    """
    tables = []
    for table in result.tables:  # Assuming tables attribute is correct
        rows = []
        for row_index in range(table.row_count):
            row = []
            for cell in table.cells:
                if cell.row_index == row_index:
                    row.append(cell.content)
            rows.append(row)
        tables.append(pd.DataFrame(rows))
    return tables
def upload_extraction_results_to_azure(section_data, filename, azure_blob_service, user_id):
    """
    Uploads extracted results to Azure Blob Storage using AzureBlobService.

    :param section_data: The extracted section data.
    :param filename: The name of the file being processed.
    :param azure_blob_service: Instance of AzureBlobService.
    :param user_id: User ID to organize files in their specific folder.
    """
    for file_type, file_path in section_data.items():
        if file_type in ['text_data', 'original_lines']:
            continue
        logger.info(f"File path: {file_path} for type {file_type}")
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"File {file_path} does not exist and will not be uploaded.")
            continue

        folder_type = "user_extract"
        logger.info(f"Uploading the file type: {file_type} to cloud using {file_path} with file name: {filename}..")
        try:
            azure_blob_service.upload_file(user_id, file_path, folder_type)
            logger.info(f"Uploaded {file_path} to Azure under folder type {folder_type}")
        except Exception as e:
            logger.error(f"Failed to upload {file_path} to Azure: {e}")

def save_extraction_results(section_data, filename, output_folder, outputs, extra_requirements = None):
    """
    Saves the extracted results locally in JSON, CSV, Excel, and Text formats.

    :param section_data: The extracted section data.
    :param filename: The name of the file being processed.
    :param output_folder: The folder to save extracted outputs.
    :param outputs: The dictionary to update with output paths.
    """
    # Save JSON data
    logger.info("Inside the save extraction results function..")
    logger.info(f"filename: {filename}, output folder: {output_folder}")
    # Save JSON data
    json_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_sections.json")
    serializable_section_data = {}

    for section, content in section_data.items():
        try:
            if "raw_tables" in content and isinstance(content["raw_tables"], list):
                serializable_section_data[section] = [
                    table.to_dict(orient="records") for table in content["raw_tables"]
                    if isinstance(table, pd.DataFrame) and not table.empty
                ]
            elif isinstance(content, pd.DataFrame):
                if not content.empty:
                    serializable_section_data[section] = content.to_dict(orient="records")
                else:
                    logger.warning(f"Skipping empty DataFrame in section: {section}")
            else:
                serializable_section_data[section] = content
        except Exception as e:
            logger.error(f"Error processing section '{section}': {e}")
            serializable_section_data[section] = f"Error processing content: {str(e)}"

    try:
        logger.info(f"JSON data: {outputs['json']}")
        if not(outputs['json'] and len(outputs['json']) > 0):
            with open(json_path, "w") as json_file:
                json.dump(serializable_section_data, json_file, indent=2)
            logger.info(f"Section data saved as JSON at {json_path}")
            outputs["json"] = json_path
    except Exception as e:
        logger.error(f"Failed to save JSON file: {e}")

    # Save text output
    text_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_text.txt")
    try:
        if not(outputs['text'] and len(outputs['text']) > 0):
            with open(text_path, "w", encoding="utf-8") as text_file:
                text_file.write(outputs["text_data"].strip())
            logger.info(f"Text data saved as Text at {text_path}")
            outputs["text"] = text_path
    except Exception as e:
        logger.error(f"Failed to save text file: {e}")
    if not(outputs['excel'] and len(outputs['excel']) > 0) or not(outputs['csv'] and len(outputs['csv']) > 0):
        excel_save_result = save_sections_to_excel_and_csv(section_data, filename, output_folder, extra_requirements)
        if excel_save_result['result'] == 'success':
            logger.info("Got the excel path successfully..")
            if not(outputs['excel'] and len(outputs['excel']) > 0):
                outputs["excel"] = excel_save_result['excel_path']
            if not(outputs['csv'] and len(outputs['csv']) > 0):
                outputs["csv"] = excel_save_result['csv_path']
        else:
            outputs["excel"] = None
    # Save Excel data
    logger.info(f"Output data : {outputs}")
    return outputs