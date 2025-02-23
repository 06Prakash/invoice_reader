import re
import pandas as pd
from modules.logging_util import setup_logger

logger = setup_logger(__name__)

def sanitize_sheet_name(sheet_name):
    """Sanitizes sheet names to meet Excel restrictions."""
    return re.sub(r'[\\/*?:\[\]]', '', sheet_name)[:31]

def sanitize_text(text):
    """
    Removes content inside superscript brackets ⁽...⁾ along with the brackets themselves.
    Also removes Roman numerals and numeric values inside simple brackets while keeping text values intact.

    Args:
        text (str): Input text.

    Returns:
        str: Sanitized text without superscript brackets and selective content inside simple brackets.
    """
    logger.info(f"Original Text: '{text}'")

    if isinstance(text, str):
        # Remove superscript brackets and their contents
        sanitized_text = re.sub(r"⁽.*?⁾", "", text).strip()

        # Remove only Roman numerals and numbers inside simple brackets but retain text
        sanitized_text = re.sub(r"\(\s*(?:\b[IVXLCDM]+\b|\d+)\s*\)", "", sanitized_text).strip()

        logger.info(f"Sanitized Text: '{sanitized_text}'")
        return sanitized_text

    return text

def consolidate_related_rows_with_order(df):
    """
    Consolidates rows with the same value in the first column while preserving the original order,
    ensuring case-insensitive comparisons.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: Consolidated DataFrame with rows merged based on the first column,
                      maintaining the original order.
    """
    if df.empty:
        logger.warning("Received empty DataFrame for consolidation.")
        return df

    first_column = df.columns[0]
    logger.info(f"Before Sanitization: {df[first_column].tolist()}")
    logger.info(f"Before Sanitization length: {len(df[first_column].tolist())}")

    # Apply text sanitization
    df[first_column] = df[first_column].astype(str).apply(sanitize_text)

    logger.info(f"After Sanitization: {df[first_column].tolist()}")
    logger.info(f"After Sanitization length: {len(df[first_column].tolist())}")

    # Create a temporary lowercase key column for case-insensitive comparison
    df["_temp_lowercase_key"] = df[first_column].str.lower()

    # Preserve original order of unique case-insensitive values
    unique_order = df["_temp_lowercase_key"].drop_duplicates().tolist()
    consolidated_rows = []

    for lowercase_name in unique_order:
        # Select group using case-insensitive match, drop temp column immediately
        group = df[df["_temp_lowercase_key"] == lowercase_name].drop(columns=["_temp_lowercase_key"], errors='ignore')

        # Ensure _temp_lowercase_key does not get added to column headers
        group_headers = [col for col in group.columns if col != "_temp_lowercase_key"]

        original_name = group[first_column].iloc[0]  # Keep the first case format
        consolidated_row = {first_column: original_name}

        for col in group_headers[1:]:  # Ignore the first column
            unique_values = group[col].dropna().unique()
            if len(unique_values) > 1:
                for i, value in enumerate(unique_values):
                    consolidated_row[f"{col} ({i + 1})" if i > 0 else col] = value
            else:
                consolidated_row[col] = unique_values[0] if unique_values.size > 0 else ""

        consolidated_rows.append(consolidated_row)

    # Create DataFrame without _temp_lowercase_key
    consolidated_df = pd.DataFrame(consolidated_rows)

    # **Ensure `_temp_lowercase_key` is removed from final DataFrame**
    if "_temp_lowercase_key" in consolidated_df.columns:
        consolidated_df.drop(columns=["_temp_lowercase_key"], errors='ignore', inplace=True)

    # **Drop empty columns after merging**
    consolidated_df = drop_nan_text_columns(consolidated_df)

    logger.info(f"Final Consolidated DataFrame Shape: {consolidated_df.shape}")
    logger.info(f"Final Consolidated DataFrame Columns: {consolidated_df.columns.tolist()}")
    logger.info(f"Final Consolidated DataFrame: {consolidated_df}")
    return consolidated_df


def drop_nan_text_columns(df):
    """
    Drops columns where all rows are either:
    - "nan" (as string, case insensitive),
    - empty strings (""), or
    - numpy.nan (true NaN values).

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: Cleaned DataFrame with unnecessary columns removed.
    """
    def is_column_empty(col):
        col_as_str = col.astype(str).str.lower()
        return col_as_str.isin(["nan", ""]).all() or col.isna().all()
    
    initial_shape = df.shape
    df = df.loc[:, ~df.apply(is_column_empty)]
    logger.info(f"Dropped empty columns. Shape before: {initial_shape}, after: {df.shape}")
    return df
