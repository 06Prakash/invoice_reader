import os
import pandas as pd
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from .data_processing import process_field, flatten_nested_field
from .logging_util import setup_logger
import json

logger = setup_logger()

# Mapping function for user-friendly model names to Azure-recognized model names
def extraction_model_mapping(model_name):
    """
    Maps user-friendly model names to Azure-recognized model names.
    """
    # Remove trailing "(text)" dynamically if present
    clean_model_name = model_name.split(" (")[0]

    model_mapping = {
        "NIRA standard": "Standard",
        "NIRA AI - handwritten": "MutualFundModelSundaramFinance",
        "NIRA AI - Invoice": "prebuilt-invoice",
        "NIRA AI - Printed Text": "prebuilt-read",
        "NIRA AI - Printed Tables": "prebuilt-layout",
        "NIRA AI - Printed business card": "prebuilt-businessCard",
        "NIRA AI - Printed receipt": "prebuilt-receipt",
    }
    return model_mapping.get(clean_model_name, "prebuilt-read")  # Default to "prebuilt-read"

def process_table_extraction(result, filename, output_folder):
    """
    Processes table extraction results and saves data to JSON, CSV, and Excel formats.

    :param result: Azure Form Recognizer analysis result
    :param filename: Original filename of the document
    :param output_folder: Folder to save the extracted files
    :return: Dictionary containing paths to JSON, CSV, and Excel outputs
    """
    tables = []
    for table in result.tables:
    # for table in page.tables:
        rows = []
        for row_index in range(table.row_count):
            row = []
            for cell in table.cells:
                if cell.row_index == row_index:
                    row.append(cell.content)
            rows.append(row)
        tables.append(pd.DataFrame(rows))

    outputs = {}
    extracted_data = None

    if tables:
        # Save each table in separate sheets of an Excel file
        excel_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_tables.xlsx")
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            for idx, table in enumerate(tables):
                table.to_excel(writer, sheet_name=f"Table_{idx + 1}", index=False)
        logger.info(f"Tables extracted and saved to {excel_path}")
        outputs['excel'] = excel_path

        # Save JSON output
        json_data = [table.to_dict(orient="records") for table in tables]
        json_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_tables.json")
        with open(json_path, "w") as json_file:
            json.dump(json_data, json_file, indent=2)
        logger.info(f"Tables saved as JSON at {json_path}")
        outputs['json_data'] = json_data
        extracted_data = json_data

        # Save CSV output
        csv_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_tables.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            for idx, table in enumerate(tables):
                table.to_csv(csv_file, index=False)
                csv_file.write("\n")  # Separate tables with a newline
        logger.info(f"Tables saved as CSV at {csv_path}")
        outputs['csv_data'] = csv_path

    else:
        logger.warning(f"No tables found in {filename}")
        outputs['error'] = f"No tables found in {filename}"
    original_lines = extract_original_lines(result)

    return extracted_data, original_lines

def process_field_extraction(result):
    """
    Processes field extraction results into structured data.

    :param result: Azure Form Recognizer analysis result
    :return: Tuple of extracted data and original lines
    """
    extracted_data = {}

    # Extract fields
    for doc in result.documents:
        for name, field in doc.fields.items():
            field_value = process_field(field)
            if isinstance(field_value, (dict, list)):
                extracted_data[name] = flatten_nested_field(field_value)
            else:
                extracted_data[name] = field_value
    
    original_lines = extract_original_lines(result)
    return extracted_data, original_lines

def extract_original_lines(result):
    original_lines = []
    # Extract original lines
    for page in result.pages:
        for line in page.lines:
            original_lines.append(line.content)

    return original_lines

def extract_with_azure(filename, upload_folder, total_pages, progress_file, progress_tracker, extraction_model, azure_endpoint, azure_key, output_folder = ""):
    """
    Extracts data from a PDF using Azure Form Recognizer and processes it based on the extraction type.

    :param filename: Name of the PDF file to process
    :param upload_folder: Folder containing the file
    :param total_pages: Total number of pages to process
    :param progress_file: Path to the progress file to update progress
    :param progress_tracker: Current progress tracker instance object
    :param extraction_model: User-provided model name
    :param azure_endpoint: Azure Form Recognizer endpoint
    :param azure_key: Azure Form Recognizer key
    :param output_folder: Folder to save output files
    :return: Dictionary containing paths to extracted outputs or structured data
    """
    if output_folder == "":
        output_folder = upload_folder
    document_analysis_client = DocumentAnalysisClient(
        endpoint=azure_endpoint,
        credential=AzureKeyCredential(azure_key)
    )
    pdf_path = os.path.join(upload_folder, filename)
    logger.info(f"Starting Azure extraction for {filename} at {pdf_path} with model {extraction_model}")

    try:
        # Map user-provided model name to Azure-recognized model
        mapped_model = extraction_model_mapping(extraction_model)
        logger.info(f"Using Azure model: {mapped_model} for extraction")

        # Start document analysis
        with open(pdf_path, "rb") as document:
            poller = document_analysis_client.begin_analyze_document(mapped_model, document)
            result = poller.result()

        if mapped_model == "prebuilt-layout":
            # Process table-based extraction
            extracted_data, original_lines = process_table_extraction(result, filename, output_folder)
            # extracted_data['download_url'] = f"/downloads/{os.path.basename(extracted_data['excel'])}"
            return filename, extracted_data, original_lines
        else:
            # Process field-based extraction
            extracted_data, original_lines = process_field_extraction(result)
            return filename, extracted_data, original_lines

    except Exception as e:
        logger.error(f"Azure extraction failed for {filename}: {e}")
        return {'filename': filename, 'error': str(e)}

