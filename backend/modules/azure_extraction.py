import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from .data_processing import process_field, flatten_nested_field
from .logging_util import setup_logger

logger = setup_logger()

# Mapping function for user-friendly model names to Azure-recognized model names
def extraction_model_mapping(model_name):
    """
    Maps user-friendly model names to Azure-recognized model names.
    """
    model_mapping = {
        "NIRA standard": "Standard",
        "NIRA AI - handwritten": "MutualFundModelSundaramFinance",
        "NIRA AI - Invoice": "prebuilt-invoice",
        "NIRA AI - Printed Text": "prebuilt-read",
        "NIRA AI - Printed Tables": "prebuilt-layout",
        "NIRA AI - Printed business card": "prebuilt-businessCard",
        "NIRA AI - Printed receipt": "prebuilt-receipt",
    }
    return model_mapping.get(model_name, "prebuilt-read")  # Default to "prebuilt-read"

def extract_with_azure(filename, upload_folder, total_pages, progress_file, progress_tracker, extraction_model, azure_endpoint, azure_key):
    """
    Extracts data from a PDF using Azure Form Recognizer and writes progress.

    :param filename: Name of the PDF file to process
    :param upload_folder: Folder containing the file
    :param total_pages: Total number of pages to process across all files
    :param progress_file: Path to the progress file to update progress
    :param extraction_model: User-provided model name
    :param azure_endpoint: Azure Form Recognizer endpoint
    :param azure_key: Azure Form Recognizer key
    :return: Tuple of (filename, extracted_data, original_lines)
    """
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

        extracted_data = {}
        original_lines = []

        # Extract fields and process the data
        logger.info(f"Processing extracted fields for {filename}")
        for doc in result.documents:
            for name, field in doc.fields.items():
                field_value = process_field(field)
                if isinstance(field_value, (dict, list)):
                    extracted_data[name] = flatten_nested_field(field_value)
                else:
                    extracted_data[name] = field_value

        # Extract lines from pages
        logger.info(f"Extracting lines from pages for {filename}")
        for page in result.pages:
            for line in page.lines:
                original_lines.append(line.content)

        # Update progress
        progress_tracker.update_progress(progress_file, len(result.pages), total_pages)
        logger.info(f"Progress updated after Azure extraction. Processed {len(result.pages)} pages.")
        logger.info(f"Azure extraction completed for {filename}")

        return filename, extracted_data, original_lines

    except Exception as e:
        logger.error(f"Azure extraction failed for {filename}: {e}")
        return filename, {'error': str(e)}, []
