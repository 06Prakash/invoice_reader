import re
from datetime import datetime

def validate_date(input_str):
    """
    Extracts and validates a date from the input string.

    Args:
        input_str (str): The input string containing a possible date.
    
    Returns:
        str: The date in "YYYY-MM-DD" format if valid, otherwise None.
    """
    # Use a regex to extract potential date patterns
    date_patterns = [
        r"\b\d{2}/\d{2}/\d{4}\b",  # Matches "21/09/2023"
        r"\b\d{4}-\d{2}-\d{2}\b",  # Matches "2023-09-21"
        r"\b\d{2}-\d{2}-\d{4}\b"   # Matches "21-09-2023" (if needed)
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, input_str)
        if match:
            date_str = match.group()
            # Try different formats to validate and reformat the date
            for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                try:
                    return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
    
    return None


def validate_time(input_str):
    """
    Extracts and validates a time from the input string.

    Args:
        input_str (str): The input string containing a possible time.
    
    Returns:
        str: The time in "HH:MM:SS" format if valid, otherwise None.
    """
    # Regular expression to find valid time in "HH:MM:SS" format
    time_pattern = r"\b\d{2}:\d{2}:\d{2}\b"
    match = re.search(time_pattern, input_str)
    if match:
        time_str = match.group()
        try:
            # Validate and format the extracted time
            return datetime.strptime(time_str, "%H:%M:%S").strftime("%H:%M:%S")
        except ValueError:
            return None
    return None

def validate_number(number_str):
    return re.fullmatch(r'\d+', number_str) is not None

def extract_number(value):
    return re.sub(r'\D', '', value)

def validate_text_only(value):
    return re.sub(r'[^a-zA-Z0-9\s]', '', value)
