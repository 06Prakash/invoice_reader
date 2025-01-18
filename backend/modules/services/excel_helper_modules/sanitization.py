import re

def sanitize_sheet_name(sheet_name):
    """Sanitizes sheet names to meet Excel restrictions."""
    return re.sub(r'[\\/*?:\[\]]', '', sheet_name)[:31]