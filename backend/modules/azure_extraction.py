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
    Processes the Azure Form Recognizer result for table extraction and generates JSON, CSV, Excel, and text outputs.

    :param result: The result object from Azure Form Recognizer
    :param filename: The name of the file being processed
    :param output_folder: The folder to save the extracted outputs
    :param progress_tracker: Progress tracker instance
    :param progress_file: Path to track extraction progress
    :param total_pages: Total number of pages to process
    :return: A dictionary containing paths to JSON, CSV, Excel, and text outputs
    """
    tables = []
    for table in result.tables:  # Adjust this based on the correct attribute
        rows = []
        for row_index in range(table.row_count):
            row = []
            for cell in table.cells:
                if cell.row_index == row_index:
                    row.append(cell.content)
            rows.append(row)
        tables.append(pd.DataFrame(rows))
        # Update progress for each table processed
        progress_tracker.update_progress(progress_file, 1, total_pages)

    outputs = {}

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
        outputs['json'] = json_path

        # Save CSV output
        csv_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_tables.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            for idx, table in enumerate(tables):
                table.to_csv(csv_file, index=False)
                csv_file.write("\n")  # Separate tables with a newline
        logger.info(f"Tables saved as CSV at {csv_path}")
        outputs['csv'] = csv_path

        # Save Text output
        text_data = ""
        for idx, table in enumerate(tables):
            text_data += f"Table {idx + 1}:\n"
            text_data += table.to_string(index=False, header=False)
            text_data += "\n\n"

        text_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_tables.txt")
        with open(text_path, "w", encoding="utf-8") as text_file:
            text_file.write(text_data)
        logger.info(f"Tables saved as Text at {text_path}")
        outputs['text'] = text_path
        outputs['text_data'] = text_data

    else:
        logger.warning(f"No tables found in {filename}")
        outputs['error'] = f"No tables found in {filename}"

    return outputs

def process_field_extraction(result, progress_tracker, progress_file, total_pages):
    """
    Processes field-based extraction results and updates progress.

    :param result: The result object from Azure Form Recognizer
    :param progress_tracker: Progress tracker instance
    :param progress_file: Path to track extraction progress
    :param total_pages: Total number of pages to process
    :return: Extracted data and original lines
    """
    extracted_data = {}
    original_lines = []

    for doc in result.documents:
        for name, field in doc.fields.items():
            field_value = process_field(field)
            if isinstance(field_value, (dict, list)):
                extracted_data[name] = flatten_nested_field(field_value)
            else:
                extracted_data[name] = field_value

    original_lines = extract_original_lines(result)
    progress_tracker.update_progress(progress_file, 1, total_pages)

    return extracted_data, original_lines

def extract_original_lines(result):
    original_lines = []
    # Extract original lines
    for page in result.pages:
        for line in page.lines:
            original_lines.append(line.content)

    return original_lines

def extract_with_azure(filename, upload_folder, output_folder, total_pages, progress_file, progress_tracker, extraction_model, azure_endpoint, azure_key):
    """
    Extracts data from a PDF using Azure Form Recognizer and processes it based on the extraction type.

    :param filename: Name of the PDF file to process
    :param upload_folder: Folder containing the file
    :param output_folder: Folder to save output files
    :param total_pages: Total number of pages to process
    :param progress_file: Path to track extraction progress
    :param progress_tracker: Progress tracker instance
    :param extraction_model: User-provided model name
    :param azure_endpoint: Azure Form Recognizer endpoint
    :param azure_key: Azure Form Recognizer key
    :return: Paths to extracted JSON, CSV, text, or Excel files
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

        if mapped_model == "prebuilt-layout":
            # Process table-based extraction
            outputs = process_table_extraction(result, filename, output_folder, progress_tracker, progress_file, total_pages)
            # outputs['download_url'] = f"/downloads/{os.path.basename(outputs['excel'])}"  # Add valid download URL
            return {'filename': filename, 'extracted_data': outputs}
        else:
            # Process field-based extraction
            extracted_data, original_lines = process_field_extraction(result, progress_tracker, progress_file, total_pages)

            # Save outputs in different formats
            json_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_fields.json")
            with open(json_path, "w") as json_file:
                json.dump(extracted_data, json_file, indent=2)
            logger.info(f"Field data saved as JSON at {json_path}")

            csv_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_fields.csv")
            df = pd.DataFrame(list(extracted_data.items()), columns=["Field", "Value"])
            df.to_csv(csv_path, index=False)
            logger.info(f"Field data saved as CSV at {csv_path}")

            excel_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_fields.xlsx")
            with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Fields", index=False)
            logger.info(f"Field data saved as Excel at {excel_path}")

            text_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_fields.txt")
            text_data = "\n".join(original_lines) if original_lines else "No text found"
            with open(text_path, "w", encoding="utf-8") as text_file:
                text_file.write(text_data)
            logger.info(f"Field data saved as Text at {text_path}")

            return {
                'filename': filename,
                'extracted_data': {
                    'json': json_path,
                    'csv': csv_path,
                    'excel': excel_path,
                    'text': text_path,
                    'text_data': text_data,
                }
            }

    except Exception as e:
        logger.error(f"Azure extraction failed for {filename}: {e}")
        return {'filename': filename, 'error': str(e)}
