import re
from datetime import datetime
from .validation import validate_date, validate_time, validate_number, extract_number

def extract_value(text, keyword, separator, boundaries, data_type, indices, multiline):
    lines = text.split('\n')
    value = ""
    capturing = False
    multiline_started = False

    for i, line in enumerate(lines):
        if keyword in line:
            capturing = True
            parts = line.split(separator)
            if len(parts) > max(indices):
                extracted_value = " ".join([parts[i].strip() for i in indices])
                value += extracted_value

                if boundaries['left'] and boundaries['right']:
                    match = re.search(f"{re.escape(boundaries['left'])}(.*?){re.escape(boundaries['right'])}", value)
                    value = match.group(1).strip() if match else ""

                if data_type == "date":
                    value = validate_date(value.strip())
                    if not value:
                        return ''
                elif data_type == "time":
                    value = validate_time(value.strip())
                    if not value:
                        return ''
                elif data_type == "number":
                    value = extract_number(value)
                    if not validate_number(value.strip()):
                        return ''
                if not multiline:
                    return value
        elif capturing and multiline:
            if (boundaries['up'] and boundaries['up'] in lines[i-1]) or (boundaries['down'] and boundaries['down'] in line):
                break
            if not multiline_started:
                value += " " + line.strip()
                multiline_started = True
            else:
                value += "\n" + line.strip()

    if data_type == 'number':
        value = extract_number(value)
        if not validate_number(value.strip()):
            return ''
    elif data_type == 'date':
        value = validate_date(value.strip())
        if not value:
            return ''
    elif data_type == 'time':
        value = validate_time(value.strip())
        if not value:
            return ''

    return value
