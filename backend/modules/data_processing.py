def process_field(field):
    if field is None:
        return None

    field_value = getattr(field, "value", None) or getattr(field, "content", None)
    if isinstance(field_value, (str, int, float)):
        return field_value
    elif isinstance(field_value, dict):
        return {k: process_field(v) for k, v in field_value.items()}
    elif isinstance(field_value, list):
        return [process_field(item) for item in field_value]
    else:
        return str(field_value)

def flatten_nested_field(data, delimiter=" | "):
    if isinstance(data, dict):
        return delimiter.join(f"{k}: {flatten_nested_field(v, delimiter)}" for k, v in data.items())
    elif isinstance(data, list):
        return delimiter.join(flatten_nested_field(item, delimiter) for item in data)
    return str(data).strip()
