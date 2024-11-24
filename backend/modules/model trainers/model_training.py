import os
import json
import numpy as np
import re
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import easyocr
import logging
import cv2
import json

pytesseract.pytesseract.tesseract_cmd = r"F:\Program Files (x86)\tesseract\tesseract.exe"
# Initialize EasyOCR reader and transformers NER model
ocr_reader = easyocr.Reader(['en'])
model_name = "dbmdz/bert-large-cased-finetuned-conll03-english"
local_cache = "huggingface_cache/transformers"
tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=local_cache)
model = AutoModelForTokenClassification.from_pretrained(model_name, cache_dir=local_cache)
ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer)

# Logger setup
logging.basicConfig(filename='extraction_log.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get the base directory
base_dir = os.path.dirname(__file__)

# Use a raw string for the file path or forward slashes
validation_pattern_file_path = os.path.join(base_dir, "validation_patterns.json")

# Load validation patterns from JSON file
with open(validation_pattern_file_path, 'r') as f:
    validation_patterns = json.load(f)


def postprocess_text(text):
    """Clean up OCR text output to handle common OCR errors."""
    replacements = {
        "amount of in words": "Amount in Words",
        "Amount of in words": "Amount in Words",
        "An amount of in words": "Amount in Words",
        "Bank A/c No": "Bank Account Number",
        "IFSC": "IFSC Code",
        "Amount in words": "Amount in Words",  # Extra variations for common OCR errors
    }
    for wrong, correct in replacements.items():
        text = re.sub(rf"\b{wrong}\b", correct, text, flags=re.IGNORECASE)
    text = re.sub(r"[^\w\s@./:-]", "", text)  # Remove non-alphanumeric symbols
    text = re.sub(r"\s{2,}", " ", text)  # Reduce multiple spaces
    return text

def preprocess_image(image):
    """Preprocess image for better OCR accuracy."""
    # Resize to improve OCR accuracy on low-resolution scans
    image = image.resize((int(image.width * 1.2), int(image.height * 1.2)))
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 3)  # Reduce noise
    processed_image = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return Image.fromarray(processed_image)


def ocr_extract_text_from_pdf(pdf_path):
    """Extract and preprocess text from each PDF page."""
    try:
        pages = convert_from_path(pdf_path, 300)
    except Exception as e:
        logger.error(f"Error converting PDF: {str(e)}")
        return None

    ocr_text = ""
    for page_number, page in enumerate(pages):
        logger.info(f"Processing page {page_number + 1}")
        processed_page = preprocess_image(page)
        page_text = pytesseract.image_to_string(processed_page, config='--psm 11')  # Assume uniform block of text
        # Experiment with other modes like --psm 4 or --psm 11 if text is misaligned.
        ocr_text += page_text + "\n"
        ocr_text = postprocess_text(ocr_text)
    return ocr_text

def extract_entities_with_ner(text):
    """Extract entities using the NER model."""
    entities = ner_pipeline(text)
    ner_data = {}

    for entity in entities:
        word = entity['word']
        label = entity['entity']

        if label not in ner_data:
            ner_data[label] = word
        else:
            ner_data[label] += " " + word  # Append words for multi-word entities

    return ner_data

def validate_and_correct_entities(ocr_text, ner_data):
    """Validate and correct extracted entities using regex patterns."""
    extracted_data = {}
    print("="*100)
    print(ocr_text)
    print("="*100)
    extracted_data = extract_data_with_context(ocr_text)
    return extracted_data

def extract_data_with_context(ocr_text):
    """Extract data by looking for keywords and handling text on the next line if needed."""
    extracted_data = {}
    ocr_lines = ocr_text.splitlines()

    for i, line in enumerate(ocr_lines):
        # Process each pattern individually and capture multiple fields per line
        for field_name, pattern in validation_patterns.items():
            match = re.search(pattern, line, re.IGNORECASE)

            if match:
                if field_name == "Applicant Name":
                    # Extract name if available on the same line
                    name = match.group(1).strip()

                    # If name is empty, look at the next line for the name
                    if not name and i + 1 < len(ocr_lines):
                        next_line = ocr_lines[i + 1]
                        # Capture only alphabetic part up to "Mobile", "Movies", or similar
                        name_match = re.match(r"([A-Za-z\s]+?)(?=\s*(?:Mobile|Movie|Mobi|\d|$))", next_line)
                        if name_match:
                            name = name_match.group(1).strip()

                    # Save the extracted name if found
                    if name:
                        extracted_data[field_name] = name

                elif field_name == "Email ID":
                    extracted_data[field_name] = match.group(2)  # Direct match for email
                elif field_name == "Amount in Words":
                    # Special handling for "Amount in Words" to capture both words and digits
                    extracted_data["Amount in Words"] = match.group(1)
                    extracted_data["Amount in Digits"] = match.group(2)
                else:
                    extracted_data[field_name] = match.group(1)
                # Continue to check other patterns in the same line

    return extracted_data

def extract_data_from_pdf(pdf_path):
    """Full extraction pipeline for PDF using OCR, NER, and regex validation."""
    ocr_text = ocr_extract_text_from_pdf(pdf_path)
    if not ocr_text:
        logger.error("Failed to extract text from PDF.")
        return {}

    # Step 1: Use NER model to identify entities
    logger.info("Extracting entities using NER...")
    ner_data = extract_entities_with_ner(ocr_text)
    
    # Step 2: Validate and correct data using regex patterns
    logger.info("Validating and correcting extracted data...")
    extracted_data = validate_and_correct_entities(ocr_text, ner_data)

    return extracted_data

# Example usage
if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    pdf_path = r'.\..\template_pdf_generators\mnt\generated\filled_sip_form_15.pdf'
    # pdf_path = r'.\..\..\..\test_pdfs\107813(1100).pdf'
    test_pdf_path = os.path.join(base_dir, pdf_path)

    logger.info("Starting extraction process...")
    extracted_data = extract_data_from_pdf(test_pdf_path)

    # Display extracted data
    print("Extracted Data:")
    for field, value in extracted_data.items():
        print(f"{field}: {value}")
