import pandas as pd
from modules.logging_util import setup_logger
import re
logger = setup_logger(__name__)

def convert_parentheses_to_negative(df):
    """
    Converts values in parentheses (e.g., "(10)") to negative numbers (e.g., -10).
    Handles values with commas like "(3,140)" as well.
    Restores commas for thousands separators after conversion for readability.
    Ensures integers are stored without decimals.

    Args:
        df (pd.DataFrame): Input DataFrame to process.

    Returns:
        pd.DataFrame: DataFrame with converted values and formatted numbers.
    """
    logger.info("Attempting to convert parentheses to negative numbers..")
    try:
        # Apply conversion with error handling
        def safe_convert(value):
            if isinstance(value, str) and value.startswith('(') and value.endswith(')'):
                try:
                    # Remove commas, strip parentheses, and convert to negative float
                    converted_value = -float(value.replace(',', '').strip('()'))
                    return format_number_with_commas(converted_value)
                except ValueError as e:
                    logger.error(f"Failed to convert value: {value} with error: {e}")
                    return value  # Return original value if conversion fails
            elif isinstance(value, (int, float)):
                # Format numeric values with commas
                return format_number_with_commas(value)
            return value

        def format_number_with_commas(number):
            """
            Formats a number with commas for thousands separators.
            Retains numeric type for compatibility with Excel storage.
            """
            if isinstance(number, (int, float)):
                # Check if the number is effectively an integer
                if isinstance(number, float) and number.is_integer():
                    return "{:,}".format(int(number))  # Format as integer with commas
                elif isinstance(number, float):
                    return "{:,.2f}".format(number)  # Format float with two decimal places
                return "{:,}".format(number)  # Format integer with commas
            return number

        # Apply the conversion safely to the DataFrame
        return df.applymap(safe_convert)
    except Exception as e:
        logger.error(f"Unexpected error in convert_parentheses_to_negative: {e}")
        raise  # Propagate exception for visibility

def remove_columns(df, texts_to_match):
    """
    Removes columns from the DataFrame that match any of the specified texts in the first row.

    Args:
        df (pd.DataFrame): Input DataFrame to process.
        texts_to_match (list): List of texts to match in the first row.

    Returns:
        pd.DataFrame: Processed DataFrame with the matching columns removed.
    """
    try:
        logger.info(f"Attempting to remove columns with any of the texts {texts_to_match} in the first row.")

        # Normalize column names
        df.columns = df.columns.map(str).str.strip().str.lower()

        # Normalize first-row values
        first_row_normalized = df.iloc[0].astype(str).str.strip().str.lower()

        # Normalize texts_to_match
        texts_to_match = [text.strip().lower() for text in texts_to_match if text.strip()]

        # Find matching columns
        matching_columns = first_row_normalized[first_row_normalized.isin(texts_to_match)].index.tolist()
        
        if matching_columns:
            logger.info(f"Found matching columns {matching_columns}. Removing them.")
            df = df.drop(columns=matching_columns, errors='ignore')
        else:
            logger.warning(f"No matching texts {texts_to_match} found in the first row.")

        logger.info(f"DataFrame after column removal:\n{df.head()}")
        return df
    except Exception as e:
        logger.error(f"Error in remove_columns_by_row_values: {e}")
        raise

def remove_rows(df, identity_to_remove_row):
    """
    Removes rows from the DataFrame based on specific identifiers.

    Args:
        df (pd.DataFrame): Input DataFrame to process.
        identity_to_remove_row (list): List of identifiers to remove from the DataFrame.
                                       These identifiers can be present in any column.

    Returns:
        pd.DataFrame: The DataFrame after removing the specified rows.
    """
    if not identity_to_remove_row:
        logger.info("No identifiers provided to remove rows. Returning the original DataFrame.")
        return df

    logger.info(f"Attempting to remove rows with identifiers: {identity_to_remove_row}")
    
    # Normalize identifiers for case-insensitive matching
    identity_to_remove_row = {identifier.strip().lower() for identifier in identity_to_remove_row if identifier.strip()}
    
    def row_contains_identifier(row):
        # Normalize row values and check if any identifier is in the row
        normalized_row = row.astype(str).str.strip().str.lower()
        return any(value in identity_to_remove_row for value in normalized_row)
    
    # Filter rows
    original_shape = df.shape
    filtered_df = df[~df.apply(row_contains_identifier, axis=1)]
    logger.info(f"Removed rows. Original shape: {original_shape}, New shape: {filtered_df.shape}")
    return filtered_df

def sort_headers_chronologically(df):
    """
    Sorts the DataFrame columns in chronological order while preserving the positions of non-time-related columns.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with headers sorted chronologically.
    """
    def extract_year(value):
        # Match years or dates (e.g., "2021", "December 2021")
        match = re.search(r'(\d{4})', str(value))
        if match:
            return int(match.group(1))
        return float('inf')  # Non-date columns will come last during sorting
    
    def is_non_time_column(column):
        # Identify non-time-related columns (e.g., "Notes", "Notes_other")
        return not re.search(r'\d{4}', str(column))
    
    # Separate non-time columns and time-related columns
    non_time_columns = [col for col in df.columns if is_non_time_column(col)]
    time_columns = [col for col in df.columns if not is_non_time_column(col)]
    
    # Sort time-related columns based on extracted year
    time_columns_sorted = sorted(time_columns, key=extract_year)
    
    # Merge back non-time columns and sorted time-related columns
    sorted_columns = []
    time_col_idx = 0
    
    for col in df.columns:
        if col in non_time_columns:
            sorted_columns.append(col)
        elif col in time_columns:
            sorted_columns.append(time_columns_sorted[time_col_idx])
            time_col_idx += 1
    
    return df[sorted_columns]


def process_table_data(df, config):
    """
    Processes table data by applying transformations like:
    - Removing numeric headers
    - Removing specific columns
    - Converting parentheses to negatives
    """

    logger.info(f"Data Frame : {df}")
    df = convert_parentheses_to_negative(df)
    logger.info("Crossed the paranthesis update function")
    logger.info(f"Current config: {config}")

    if columns := config.get("columnsToRemove", []):
        df = remove_columns(df, columns)
    
    if len(config.get("rowsToRemove", [])) > 0:
        rowsToRemove = config.get("rowsToRemove", [])
        df = remove_rows(df, rowsToRemove)
    logger.info(f"Data Frame after processing: {df}")
    return df