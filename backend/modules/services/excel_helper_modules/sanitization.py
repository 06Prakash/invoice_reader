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

    Args:
        text (str): Input text.

    Returns:
        str: Sanitized text without superscript brackets and their contents.
    """
    logger.info(f"Original Text: '{text}'")
    if isinstance(text, str):
        # Remove all content inside superscript brackets and the brackets themselves
        sanitized_text = re.sub(r"⁽.*?⁾", "", text).strip()
        logger.info(f"Sanitized Text: '{sanitized_text}'")
        return sanitized_text
    return text

def consolidate_related_rows_with_order(df):
        """
        Consolidates rows with the same value in the first column while preserving the original order.

        Args:
            df (pd.DataFrame): The input DataFrame.

        Returns:
            pd.DataFrame: Consolidated DataFrame with rows merged based on the first column,
                          maintaining the original order.
        """
        first_column = df.columns[0]

        # Sanitize the first column while preserving order
        logger.info(f"Before Sanitization: {df[first_column].tolist()}")
        df[first_column] = df[first_column].astype(str).apply(sanitize_text)
        logger.info(f"After Sanitization: {df[first_column].tolist()}")


        # Track the order of first-column values
        unique_order = df[first_column].drop_duplicates().tolist()

        # Group rows by the first column and consolidate
        consolidated_rows = []
        for name in unique_order:
            group = df[df[first_column] == name]
            consolidated_row = {first_column: name}
            for col in group.columns[1:]:
                for i, value in enumerate(group[col].values):
                    consolidated_row[f"{col} ({i + 1})" if i > 0 else col] = value
            consolidated_rows.append(consolidated_row)

        return pd.DataFrame(consolidated_rows)