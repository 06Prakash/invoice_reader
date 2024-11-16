import logging
import re
from datetime import datetime
from .validation import validate_date, validate_time, validate_number, extract_number, validate_text_only

def extract_value(text, keyword, separator, boundaries, capture_mode, data_type, indices, multiline, logger, default=""):
    lines = text.split('\n')
    value = ""
    capturing = False
    multiline_started = False

    for i, line in enumerate(lines):
        if keyword in line:
            capturing = True
            parts = line.split(separator)

            # Handle multiple indices with fallback
            for index in indices:
                if len(parts) > index:
                    extracted_value = parts[index].strip()
                    value += extracted_value
                    break  # Use the first valid index
            else:
                return default  # Return default if no valid index is found

            # Handle boundary matching
            if not multiline:
                extract_with_boundaries(value, boundaries['left'], boundaries['right'], capture_mode, logger)
                if boundaries['left'] and boundaries['right']:
                    match = re.search(f"{re.escape(boundaries['left'])}(.*?){re.escape(boundaries['right'])}", value)
                    value = match.group(1).strip() if match else value

                # Validate and process value based on data_type
                value = validate_data_type(value, data_type)
                if not value:
                    return default  # Return default if validation fails
                return value
        elif capturing and multiline:
            if not multiline_started:
                value += " " + line.strip()
                multiline_started = True
            else:
                value += " " + line.strip()
            if boundaries['down'] and boundaries['down'] in line:
                break

    # Final validation for multiline or extracted values
    if boundaries['multiline-left'] and boundaries['multiline-right']:
        match = re.search(f"{re.escape(boundaries['multiline-left'])}(.*?){re.escape(boundaries['multiline-right'])}", value)
        value = match.group(1).strip() if match else value
    value = validate_data_type(value.strip(), data_type)
    return value if value else default

def validate_data_type(value, data_type):
    if data_type == 'number':
        value = extract_number(value)
        return value if validate_number(value) else None
    elif data_type == 'date':
        return validate_date(value)
    elif data_type == 'time':
        return validate_time(value)
    elif data_type == 'text-only':
        return validate_text_only(value)
    return value

def extract_with_boundaries(text, left_boundary, right_boundary, capture_mode, logger):
    """
    Extracts text based on the given boundaries and capture mode.

    Args:
        text (str): The input text.
        left_boundary (str): The left boundary marker.
        right_boundary (str): The right boundary marker.
        capture_mode (str): The mode to capture text (after_left, before_right, between, all).

    Returns:
        str: Extracted text based on the mode, or the original text if no boundaries match.
    """
    text = text.strip()
    logger.info("*"*50)
    logger.info(f"Capture mode: {capture_mode}")
    logger.info(f"Left Boundary: {left_boundary}")
    logger.info(f"Right Boundary: {right_boundary}")
    logger.info(f"text: {text}")
    logger.info("*"*50)

    # Capture everything based on the mode
    if capture_mode == "after_left":
        if left_boundary in text:
            logger.info("="*100)
            logger.info(text)
            logger.info("="*100)
            return text.split(left_boundary, 1)[1].strip()
    elif capture_mode == "before_right":
        if right_boundary in text:
            return text.split(right_boundary, 1)[0].strip()
    elif capture_mode == "between":
        if left_boundary in text and right_boundary in text:
            # Extract between left and right boundaries
            start = text.find(left_boundary) + len(left_boundary)
            end = text.find(right_boundary)
            return text[start:end].strip()
    elif capture_mode == "all":
        return text  # Ignore boundaries and return the entire string

    # If no matching boundary is found, return the original text
    return text
