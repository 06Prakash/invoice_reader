import os
import json
from pdf2image import convert_from_path
from pytesseract import image_to_string
from .preprocessing import preprocess_image
from .extraction import extract_value
from .logging_util import setup_logger

logger = setup_logger()

DEFAULT_TEMPLATE_PATH = "resources/json_templates/default_template.json"  # Adjust this path if needed

def load_template(template_name, template_folder):
    """
    Loads the specified template or falls back to the default template.

    :param template_name: Name of the template file to load
    :param template_folder: Folder containing the templates
    :return: Parsed JSON template
    """
    if template_name == "Default Template":
        logger.info("Loading default template...")
        template_path = DEFAULT_TEMPLATE_PATH
    else:
        template_path = os.path.join(template_folder, f"{template_name}.json")

    if not os.path.exists(template_path):
        logger.error(f"Template file not found: {template_path}")
        raise FileNotFoundError(f"Template file not found: {template_path}")

    with open(template_path, "r") as template_file:
        logger.info(f"Loading template from: {template_path}")
        return json.load(template_file)


def extract_from_pdf(filename, template, upload_folder, total_pages, progress_file, progress_tracker):
    """
    Extracts data from a PDF file using template-based logic.

    :param filename: Name of the PDF file to process
    :param template: Template with field configurations
    :param upload_folder: Folder containing the file
    :param total_pages: Total number of pages to process for progress tracking
    :param progress_file: Path to the progress file for writing progress updates
    :param progress_tracker: Instance of progress tracker
    :return: Tuple of (filename, extracted_data, original_lines)
    """
    pdf_path = os.path.join(upload_folder, filename)
    logger.info(f"Starting template-based extraction for {filename} using template {template.get('name', 'Unnamed')}.")

    try:
        # Convert PDF to images
        pages = convert_from_path(pdf_path, 300)
        extracted_data = {}
        original_lines = []
        page_count = len(pages)

        for page_number, page_data in enumerate(pages):
            try:
                # Save the page as an image and preprocess it
                image_path = f"{filename}_page_{page_number}.jpg"
                logger.info(f"Processing page {page_number + 1} of {page_count} out of total pages {total_pages}.")
                page_data.save(image_path, 'JPEG')

                # Preprocess the image
                preprocessed_image_path = preprocess_image(image_path)

                # Perform OCR to extract text
                page_text = image_to_string(preprocessed_image_path)

                # Store original lines for reference
                original_lines.extend(page_text.split('\n'))

                # Extract fields based on the template
                for field in template['fields']:
                    name = field['name']
                    keyword = field['keyword']
                    separator = field.get('separator', ':')
                    index = field.get('index', '1')
                    indices = [int(i) for i in index.split(',')]
                    boundaries = field.get('boundaries', {'left': '', 'right': '', 'up': '', 'down': ''})
                    data_type = field.get('data_type', 'text')
                    multiline = field.get('multiline', False)
                    capture_mode = field.get('capture_mode', 'between')

                    # Extract value using field configuration
                    value = extract_value(
                        text=page_text,
                        keyword=keyword,
                        separator=separator,
                        boundaries=boundaries,
                        capture_mode=capture_mode,
                        data_type=data_type,
                        indices=indices,
                        multiline=multiline,
                        logger=logger
                    )

                    extracted_data[name] = value

                # Update progress after processing each page
                progress_tracker.update_progress(progress_file, page_number + 1, total_pages)
                logger.info(f"Progress updated for page {page_number + 1} of {total_pages}.")

            except Exception as e:
                logger.error(f"Error processing page {page_number + 1} of {filename}: {e}")
                continue

        logger.info(f"Template-based extraction completed for {filename}.")
        return filename, extracted_data, original_lines

    except Exception as e:
        logger.error(f"Template-based extraction failed for {filename}: {e}")
        return filename, {'error': str(e)}, []


def extract_with_template_logic(filename, template_name, template_folder, upload_folder, total_pages, progress_file, progress_tracker):
    """
    Handles the overall template loading and extraction logic.

    :param filename: PDF file name
    :param template_name: Template name
    :param template_folder: Folder containing templates
    :param upload_folder: Folder containing uploaded PDFs
    :param total_pages: Total number of pages for progress tracking
    :param progress_file: File to track progress
    :param progress_tracker: Instance of progress tracker
    :return: Tuple of extracted data
    """
    try:
        # Load the appropriate template
        template = load_template(template_name, template_folder)

        # Perform extraction
        return extract_from_pdf(filename, template, upload_folder, total_pages, progress_file, progress_tracker)

    except FileNotFoundError as e:
        logger.error(f"Failed to load template: {e}")
        return filename, {'error': 'Template not found'}, []

    except Exception as e:
        logger.error(f"Unexpected error during template extraction: {e}")
        return filename, {'error': str(e)}, []
