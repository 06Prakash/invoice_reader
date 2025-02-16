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
from pdf2image import convert_from_path
import re  # To detect Roman numerals

current_file = os.path.basename(__file__)
logger = setup_logger(current_file.split(".")[0])

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
        "NIRA AI - Printed Tables": "prebuilt-document",
        "NIRA AI - Printed business card": "prebuilt-businessCard",
        "NIRA AI - Printed receipt": "prebuilt-receipt",
    }
    return model_mapping.get(clean_model_name, "prebuilt-read")  # Default to "prebuilt-read"

def is_roman_numeral(value):
    """Helper function to check if a string is a Roman numeral (I, II, III, IV, etc.)"""
    roman_pattern = r"^(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX)$"
    return bool(re.match(roman_pattern, str(value).strip()))

def should_remove_first_column(df):
    """Determines whether the first column should be removed."""
    first_column_values = df[df.columns[0]].dropna().astype(str)
    logger.info(f"First column values: {first_column_values.tolist()}")
    
    # Count values that are Roman numerals, numbers, empty, or very short (≤5 chars)
    short_values = first_column_values.apply(lambda x: len(x.strip()) <= 5 or is_roman_numeral(x) or x.strip().isdigit()).sum()
    logger.info(f"Short values count in first column: {short_values}")
    # Percentage of such values
    threshold = short_values / len(first_column_values) if len(first_column_values) > 0 else 0
    logger.info(f"First column threshold: {threshold}")
    
    # Check if the first column is fully empty or contains only NaN/None/null values
    is_fully_empty = first_column_values.empty or first_column_values.isin(["", "nan", "none", "null"]).all()
    logger.info(f"Is first column fully empty: {is_fully_empty}")
    
    # If more than 90% of first column values match this pattern or it is fully empty, consider removing
    return threshold > 0.9 or is_fully_empty

def extract_structured_rows(table):
    """Extracts structured rows from Azure Form Recognizer table cells."""
    structured_rows = {}
    max_columns = table.column_count

    for cell in table.cells:
        row_index = getattr(cell, "row_index", getattr(cell, "rowIndex", None))
        col_index = getattr(cell, "column_index", getattr(cell, "columnIndex", None))
        column_span = getattr(cell, "column_span", getattr(cell, "columnSpan", 1))

        if row_index is None or col_index is None:
            continue

        if row_index not in structured_rows:
            structured_rows[row_index] = [""] * max_columns

        structured_rows[row_index][col_index] = cell.content

        for span_offset in range(1, column_span):
            if col_index + span_offset < max_columns:
                structured_rows[row_index][col_index + span_offset] = (
                    cell.content if row_index != 0 else ""  # Keep headers clean
                )

    logger.info(f"Structured Rows: {structured_rows}")
    return [structured_rows[row] for row in sorted(structured_rows.keys())]


def extract_headers(table, max_columns):
    """Extracts headers from Azure Form Recognizer table cells."""
    headers = [" "] * max_columns
    for cell in table.cells:
        if getattr(cell, "kind", "") == "columnHeader":
            col_index = getattr(cell, "column_index", getattr(cell, "columnIndex", None))
            column_span = getattr(cell, "column_span", getattr(cell, "columnSpan", 1))
            if col_index is not None:
                if column_span > 1:
                    target_index = col_index + column_span - 1
                    if target_index < max_columns:
                        headers[target_index] = cell.content.strip() if isinstance(cell.content, str) else ""
                else:
                    headers[col_index] = cell.content.strip() if isinstance(cell.content, str) else ""

    logger.info(f"Extracted Headers Before Cleaning: {headers}")
    return headers


def clean_table(df_table):
    """Cleans the extracted table by removing duplicates, empty columns, and adjusting headers."""
    # Remove duplicate columns
    df_table = df_table.loc[:, ~df_table.columns.duplicated()]
    logger.info(f"Table Shape After Removing Duplicates: {df_table.shape}")

    # Remove duplicate headers if the first row matches column names
    if df_table.iloc[0].equals(df_table.columns):
        logger.info("Detected duplicate column headers in the first row. Removing...")
        df_table = df_table[1:].reset_index(drop=True)

    # Drop fully empty columns
    df_table = df_table.dropna(axis=1, how="all")
    logger.info(f"Table Shape After Dropping Empty Columns: {df_table.shape}")

    # Drop fully empty rows
    df_table = df_table.dropna(how="all")
    logger.info(f"Final Processed Table Shape: {df_table.shape}")

    return df_table


def handle_first_column_removal(df_table):
    """Handles removal of the first column and adjusts headers if needed."""
    first_column_name = df_table.columns[0]
    logger.info(f"First column name: {first_column_name}")

    if should_remove_first_column(df_table):
        logger.info(f"Removing first column: {first_column_name} and shifting headers")

        second_column_name = df_table.columns[1]
        if second_column_name.strip() == "":
            df_table.columns = [df_table.iloc[0, 0]] + df_table.columns[2:].tolist()
            df_table = df_table[1:].reset_index(drop=True)

        df_table = df_table.drop(columns=[first_column_name])

    logger.info(f"Table Columns After First Column Removal: {list(df_table.columns)}")
    return df_table


def save_to_csv(tables, output_folder, filename):
    """Saves extracted tables to a CSV file."""
    csv_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_tables.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
        if tables:
            for table in tables:
                logger.info(f"First 3 rows of the table:\n{table.head(3)}")
                table.to_csv(csv_file, index=False, header=False)
                csv_file.write("\n")
        else:
            csv_file.write("No data extracted\n")

    logger.info(f"CSV file saved: {csv_path}")
    return csv_path


def save_to_text(tables, output_folder, filename):
    """Saves extracted tables to a text file."""
    text_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_tables.txt")
    with open(text_path, "w", encoding="utf-8") as text_file:
        text_data = "\n\n".join([table.to_string(index=False, header=False) for table in tables])
        text_file.write(text_data if text_data else "No data extracted\n")

    logger.info(f"Text file saved: {text_path}")
    return text_path, text_data

def process_table(table, total_pages, table_idx, progress_tracker, progress_file):
    """Processes an individual table extracted from Azure Form Recognizer."""
    logger.info(f"Processing table {table_idx + 1}/{total_pages}")
    
    structured_rows = extract_structured_rows(table)
    df_table = pd.DataFrame(structured_rows)
    logger.info(f"Raw extracted table shape: {df_table.shape}")
    logger.debug(f"Raw extracted table data: {df_table}")

    headers = extract_headers(table, df_table.shape[1])
    logger.info(f"Extracted headers: {headers}")
    if any(headers):
        df_table.columns = headers
    else:
        df_table.columns = df_table.iloc[0]
        df_table = df_table[1:].reset_index(drop=True)
    logger.info(f"Table shape after setting headers: {df_table.shape}")
    logger.debug(f"Table data after setting headers: {df_table}")

    df_table = handle_first_column_removal(df_table)
    logger.info(f"Table shape after handling first column removal: {df_table.shape}")
    logger.debug(f"Table data after handling first column removal: {df_table}")

    df_table = clean_table(df_table)
    logger.info(f"Final cleaned table shape: {df_table.shape}")
    logger.info(f"Final cleaned table data: {df_table}")

    progress_tracker.update_progress(progress_file, table_idx + 1, total_pages)
    logger.info(f"Updated progress for table {table_idx + 1}/{total_pages}")

    return df_table

def is_financial_table(structured_rows):
    """Determine if a table is a financial table based on keywords only."""
    financial_keywords = [
        'revenue', 'income', 'expenses', 'profit', 'loss', 
        'tax', 'earnings', 'depreciation', 'amortization', 
        'comprehensive', 'share', 'equity', 'cash', 'liabilities', 'assets'
    ]

    text = " ".join([" ".join(row).lower() for row in structured_rows])
    logger.info(f"Text from structured rows: {text}")
    
    # Count how many financial keywords appear
    keyword_hits = sum(keyword in text for keyword in financial_keywords)

    # If at least 3 financial keywords are found, consider it a financial table
    return keyword_hits >= 3

def process_table_extraction(result, filename, output_folder, progress_tracker, progress_file, total_pages, model='financial'):
    """Main function to process table extraction from Azure Form Recognizer results."""
    tables = []

    if hasattr(result, 'tables') and result.tables:
        for table_idx, table in enumerate(result.tables):
            logger.info(f"Processing Table {table_idx + 1}/{len(result.tables)}")
            
            if model == 'financial':
                structured_rows = extract_structured_rows(table)
                if not is_financial_table(structured_rows):
                    logger.info(f"Skipping non-financial table {table_idx + 1}")
                    # Log details about the skipped table for future analysis
                    logger.info(f"Skipped Table {table_idx + 1}/{len(result.tables)}: {structured_rows}")
                    continue  # Skip the table
                
            df_table = process_table(table, total_pages, table_idx, progress_tracker, progress_file)
            tables.append(df_table)

    csv_path = save_to_csv(tables, output_folder, filename)
    text_path, text_data = save_to_text(tables, output_folder, filename)

    outputs = {
        'csv': csv_path,
        'text': text_path,
        'raw_tables': tables if tables else [pd.DataFrame(["No Data Extracted"])],
        'original_lines': text_data if text_data else "",
    }

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
    if mapped_model == "prebuilt-document":
        return process_table_extraction(result, f"{filename}_{section}", output_folder, progress_tracker, progress_file, total_pages)
    elif mapped_model == "MutualFundModelSundaramFinance":
        return process_field_extraction(result, f"{filename}_{section}", output_folder, progress_tracker, progress_file, total_pages)
    else:
        return process_text_extraction(result, f"{filename}_{section}", output_folder, progress_tracker, progress_file, total_pages)

def extract_with_azure(
    filename, user_id, azure_blob_service, output_folder, pages_to_process, total_pages, progress_file, progress_tracker,
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
    use_credit = False

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
                        use_credit = True
                        pages = ",".join(map(str, chunk))
                        logger.info(f"Processing chunk for section {section}: {pages}")

                        # Convert the specified pages to images
                        images = convert_from_path(temp_pdf_path, first_page=min(chunk), last_page=max(chunk))

                        # Convert images to bytes and send to Azure Form Recognizer in parallel
                        def analyze_image(image):
                            # Convert image to black and white
                            bw_image = image.convert("L")
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_image_file:
                                bw_image.save(temp_image_file, format="PNG")
                                temp_image_file.seek(0)
                                image_bytes = temp_image_file.read()
                            try:
                                poller = document_analysis_client.begin_analyze_document(mapped_model, image_bytes)
                                result = poller.result()
                                return result
                            except HttpResponseError as e:
                                logger.error(f"Error analyzing image: {e}")
                                return None

                        with ThreadPoolExecutor() as executor:
                            results = list(executor.map(analyze_image, images))

                        # Combine results
                        for result in results:
                            section_outputs = process_based_on_model(
                                result, filename, section, output_folder, progress_tracker, progress_file, pages_to_process, mapped_model
                            )

                            # Process outputs and aggregate them
                            if "raw_tables" in section_outputs:
                                section_data.setdefault(section, {}).setdefault("raw_tables", []).extend(
                                    section_outputs["raw_tables"]
                                )

                            if "json" in section_outputs:
                                section_data.setdefault(section, {}).update(section_outputs["json"])
                                outputs['json'] = section_outputs["json"]

                            outputs["text_data"] += f"\n{section_outputs.get('text_data', '')}"
                            outputs["original_lines"] += f"\n{section_outputs.get('original_lines', '')}"

                            if "csv" in section_outputs:
                                outputs["csv"] = section_outputs["csv"]

                except HttpResponseError as e:
                    logger.error(f"Error processing section {section}: {e}")
                except Exception as section_error:
                    logger.error(f"Unexpected error processing section {section}: {section_error}")

        else:
            all_pages = list(range(1, total_pages + 1))
            for chunk in split_pages(all_pages, chunk_size):
                use_credit = True
                pages = ",".join(map(str, chunk))
                logger.info(f"Processing chunk: {pages}")

                with open(temp_pdf_path, "rb") as document:
                    poller = document_analysis_client.begin_analyze_document(mapped_model, document, pages=pages)
                    result = poller.result()

                full_outputs = process_based_on_model(
                    result, filename, "Full Document", output_folder, progress_tracker, progress_file, pages_to_process, mapped_model
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
        return {"filename": filename, "extracted_data": outputs, "use_credit": use_credit}

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

def delete_extracted_local_files(section_data):
    """
    Deletes local files listed in the section_data.

    :param section_data: Dictionary containing file paths to delete.
    """
    for file_type, file_path in section_data.items():
        if file_type in ['text_data', 'original_lines']:
            continue
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted local file: {file_path}")
            except Exception as e:
                logger.error(f"Error while deleting file {file_path}: {e}")