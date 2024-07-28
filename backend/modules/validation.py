import re
from datetime import datetime

def validate_date(date_str):
    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def validate_time(time_str):
    try:
        return datetime.strptime(time_str, "%H:%M:%S").strftime("%H:%M:%S")
    except ValueError:
        return None

def validate_number(number_str):
    return re.fullmatch(r'\d+', number_str) is not None

def extract_number(value):
    return re.sub(r'\D', '', value)
