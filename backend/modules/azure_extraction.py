import os
import pandas as pd
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from .data_processing import process_field, flatten_nested_field
from .logging_util import setup_logger
import csv
import json
from concurrent.futures import ThreadPoolExecutor
from azure.core.exceptions import HttpResponseError
from modules.services.excel_service import process_excel, save_sections_to_excel

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
    Processes the Azure Form Recognizer result for table extraction and generates outputs.
    Includes raw table data and original lines in the return value.
    """
    tables = []
    original_lines = ''  # Collect raw lines for separate use
    outputs = {}

    # Collect original lines from result.pages (if available)
    if hasattr(result, 'pages'):
        original_lines = extract_original_lines(result)

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
    :return: Outputs dictionary including JSON, text, CSV, and Excel paths, and original lines
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
    outputs['original_lines'] = "\n".join(original_lines)

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

    # Add original lines separately to the output
    outputs['original_lines'] = text_data

    return outputs



def extract_original_lines(result):
    original_lines = []
    # Extract original lines
    for page in result.pages:
        for line in page.lines:
            original_lines.append(line.content)

    return "\n".join(original_lines)

def extract_with_azure(
    filename, upload_folder, output_folder, total_pages, progress_file, progress_tracker,
    extraction_model, azure_endpoint, azure_key, page_config=None
):
    """
    Extracts data from a PDF using Azure Form Recognizer and processes it based on the extraction type.
    Handles section-specific page configurations and supports chunked page processing.
    """
    # Retrieve chunk size from environment variables (default to 2 if not set)
    chunk_size = int(os.getenv("AZURE_CHUNK_SIZE", 2))
    
    document_analysis_client = DocumentAnalysisClient(
        endpoint=azure_endpoint,
        credential=AzureKeyCredential(azure_key)
    )
    pdf_path = os.path.join(upload_folder, filename)
    logger.info(f"Starting Azure extraction for {filename} at {pdf_path} with model {extraction_model}")

    # Ensure extra_requirements is not None
    extra_requirements = page_config or {}

    try:
        mapped_model = extraction_model_mapping(extraction_model)
        logger.info(f"Using Azure model: {mapped_model} for extraction")

        # Initialize a dictionary to store section-specific data and outputs
        section_data = {}
        outputs = {"json": None, "csv": None, "text": None, "excel": None, "text_data": "", "original_lines": ""}
        logger.info(f"Page Config: {page_config}")

        def split_pages(pages, chunk_size):
            """Splits a list of pages into chunks of a given size."""
            for i in range(0, len(pages), chunk_size):
                yield pages[i:i + chunk_size]

        if page_config:
            # Process each section's page range
            for section, config in page_config.items():
                try:
                    logger.info(f"Extracting section: {section} with config: {config}")

                    # Extract pageRange from the section's configuration
                    page_range = config.get("pageRange")
                    if not page_range:
                        raise ValueError(f"Missing pageRange for section {section}")

                    # Ensure the pageRange is properly formatted for Azure
                    if isinstance(page_range, list):
                        page_list = page_range
                    elif isinstance(page_range, str):
                        page_list = list(parse_page_ranges(page_range.replace(" ", "").strip()))
                    else:
                        raise ValueError(f"Invalid page_range format for section {section}: {page_range}")

                    for chunk in split_pages(page_list, chunk_size):
                        pages = ",".join(map(str, chunk))
                        logger.info(f"Processing chunk for section {section}: {pages}")
                        
                        with open(pdf_path, "rb") as document:
                            poller = document_analysis_client.begin_analyze_document(mapped_model, document, pages=pages)
                            result = poller.result()

                        # Handle different model types
                        if mapped_model == "prebuilt-layout":
                            section_outputs = process_table_extraction(
                                result, f"{filename}_{section}", output_folder, progress_tracker, progress_file,
                                total_pages
                            )
                            # section_data["csv"] = section_outputs.get("csv")
                            # section_data["text_data"] = section_outputs.get("text_data", "No original text")
                            section_data.setdefault(section, []).extend(section_outputs.get("raw_tables", []))
                        elif mapped_model == 'MutualFundModelSundaramFinance':
                            section_outputs = process_field_extraction(
                                result, f"{filename}_{section}", output_folder, progress_tracker, progress_file,
                                total_pages
                            )
                            section_data.setdefault(section, {}).update(section_outputs.get("json_data", {}))
                            # section_data["csv"] = section_outputs.get("csv", "NO CSV Data")
                            # section_data["text_data"] = section_outputs.get("text_data", "No original text")
                        else:
                            section_outputs = process_text_extraction(
                                result, f"{filename}_{section}", output_folder, progress_tracker, progress_file,
                                total_pages
                            )
                            section_data.setdefault(section, {"text_data": ""})["text_data"] += section_outputs.get("text_data", "")
                            # section_data["csv"] = section_outputs.get("csv", "No CSV DATA")
                            # section_data["text_data"] = section_outputs.get("text_data", "No original text")

                        # Aggregate outputs
                        outputs["text_data"] += f"\n{section_outputs.get('text_data', '')}"
                        outputs["original_lines"] += f"\n{section_outputs.get('original_lines', '')}"
                        for key in ["json", "csv", "excel", "text"]:
                            if section_outputs.get(key):
                                outputs[key] = section_outputs[key]

                except HttpResponseError as e:
                    logger.error(f"Error processing section {section}: {e}")
                except Exception as section_error:
                    logger.error(f"Unexpected error processing section {section}: {section_error}")

        else:
            # Process the entire document if no page config is provided
            all_pages = list(range(1, total_pages + 1))
            for chunk in split_pages(all_pages, chunk_size):
                pages = ",".join(map(str, chunk))
                logger.info(f"Processing chunk: {pages}")

                with open(pdf_path, "rb") as document:
                    poller = document_analysis_client.begin_analyze_document(mapped_model, document, pages=pages)
                    result = poller.result()

                if mapped_model == "prebuilt-layout":
                    full_outputs = process_table_extraction(
                        result, filename, output_folder, progress_tracker, progress_file, total_pages
                    )
                    logger.info(full_outputs)
                    outputs["csv"] = full_outputs.get("csv")
                    outputs["original_lines"] += full_outputs.get("original_lines", "")
                    outputs["text_data"] += full_outputs.get("text_data", "")
                    logger.info("-=-=-=-=-=-=-=")
                    logger.info(f"Raw Tables Before Adding: {full_outputs.get('raw_tables', [])}")
                    logger.info("-=-=-=-=-=-=-=")
                    section_data.setdefault("Full Document", []).extend(full_outputs.get("raw_tables", []))
                    logger.info(f"SECTION TABLE DATA: {section_data}")  # Safe log statement

                elif mapped_model == 'MutualFundModelSundaramFinance':
                    full_outputs = process_field_extraction(
                        result, filename, output_folder, progress_tracker, progress_file, total_pages
                    )
                    section_data.setdefault("Full Document", {}).update(full_outputs.get("json_data", {}))
                    outputs["csv"] = full_outputs.get("csv", "No CSV Data")
                    outputs["original_lines"] += full_outputs.get("original_lines", "No Original Lines")
                    outputs["text_data"] += full_outputs.get("text_data", "No text Data")
                else:
                    full_outputs = process_text_extraction(
                        result, filename, output_folder, progress_tracker, progress_file, total_pages
                    )
                    section_data.setdefault("Full Document", {"text_data": ""})["text_data"] += full_outputs.get("text_data", "")
                    outputs["csv"] = full_outputs.get("csv", "No CSV Data")
                    outputs["original_lines"] += full_outputs.get("original_lines", "No Original Lines")
                    outputs["text_data"] += full_outputs.get("text_data", "No text Data")

            # Ensure Full Document has at least placeholder content
            if not section_data.get("Full Document"):
                logger.warning("Full Document is empty, adding placeholder.")
                section_data["Full Document"] = [{"Field": "No Data", "Value": "No content extracted"}]


        # Save the processed Excel file
        logger.info(f"extra_requirements: {extra_requirements}")
        excel_save_result = save_sections_to_excel(section_data, filename, output_folder, extra_requirements)
        if excel_save_result['result'] == 'success':
            logger.info("Got the excel path successfully..")
            outputs["excel"] = excel_save_result['excel_path']
        else:
            outputs["excel"] = None

        # Save JSON data
        json_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_sections.json")
        serializable_section_data = {}
        for section, content in section_data.items():
            if isinstance(content, list):  # Handle lists of DataFrames (e.g., tables)
                serializable_section_data[section] = [
                    table.to_dict(orient="records") for table in content if isinstance(table, pd.DataFrame)
                ]
            elif isinstance(content, pd.DataFrame):  # Handle single DataFrame
                serializable_section_data[section] = content.to_dict(orient="records")
            else:
                serializable_section_data[section] = content  # Include non-DataFrame content as is

        with open(json_path, "w") as json_file:
            json.dump(serializable_section_data, json_file, indent=2)
        logger.info(f"Section data saved as JSON at {json_path}")
        outputs["json"] = json_path

        # Save text output
        text_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_text.txt")
        with open(text_path, "w", encoding="utf-8") as text_file:
            text_file.write(outputs["text_data"].strip())
        logger.info(f"Text data saved as Text at {text_path}")
        outputs["text"] = text_path
        logger.info(f"CSV data: {outputs}")

        return {"filename": filename, "extracted_data": outputs}

    except Exception as e:
        logger.error(f"Azure extraction failed for {filename}: {e}")
        return {"filename": filename, "error": str(e)}

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

# def save_sections_to_excel(section_data, filename, output_folder):
#     """
#     Saves section-specific data to separate sheets in an Excel file.
#     Ensures at least one visible sheet exists, even if no data is extracted.
#     """
#     excel_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_sections.xlsx")

#     try:
#         with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
#             logger.info(section_data)
#             if not section_data:
#                 logger.warning("No section data available. Adding default sheet.")
#                 # Create a default placeholder sheet
#                 pd.DataFrame(["No data extracted"]).to_excel(writer, sheet_name="No_Data", index=False)
#             else:
#                 has_data = False  # Track if any valid sheet is added
#                 for section, content in section_data.items():
#                     if isinstance(content, list):  # Handle tables (list of DataFrames)
#                         for idx, table in enumerate(content):
#                             if isinstance(table, pd.DataFrame) and not table.empty:
#                                 sheet_name = f"{section}_Table_{idx + 1}"
#                                 logger.info(f"Writing table to sheet: {sheet_name}")
#                                 table.to_excel(writer, sheet_name=sheet_name, index=False, header=False).drop(['unnamed 0'],axis=1)
#                                 has_data = True
#                             else:
#                                 logger.warning(f"Empty or invalid table in section: {section}, Table {idx + 1}. Skipping.")
#                     elif isinstance(content, dict):  # Handle field-based extractions
#                         pd.DataFrame(content.items(), columns=["Field", "Value"]).to_excel(
#                             writer, sheet_name=section, index=False, header=False
#                         ).drop(['unnamed 0'],axis=1)
#                         has_data = True
#                     elif isinstance(content, str):  # Handle raw text data
#                         rows = content.split("\n")
#                         structured_rows = [row.split() for row in rows if row.strip()]  # Split rows into columns
#                         pd.DataFrame(structured_rows).to_excel(writer, sheet_name=section, index=False, header=False).drop(['unnamed 0'],axis=1)
#                         has_data = True
#                     else:
#                         logger.warning(f"Unsupported content type for section: {section}. Skipping.")

#                 # Add a placeholder sheet if no valid data was found
#                 if not has_data:
#                     logger.warning("No valid data found. Adding default placeholder sheet.")
#                     pd.DataFrame(["No data available"]).to_excel(writer, sheet_name="Placeholder", index=False)

#         logger.info(f"Section data saved to Excel at {excel_path}")
#     except Exception as e:
#         logger.error(f"Failed to save sections to Excel: {e}")
#         raise
#     return excel_path

