import os
import pandas as pd
from modules.logging_util import setup_logger
from modules.services.excel_helper_modules.sanitization import consolidate_related_rows_with_order
logger = setup_logger(__name__)
from modules.services.excel_helper_modules.excel_operations import (
    save_sheet,
    sanitize_sheet_name
)
from modules.services.excel_helper_modules.data_processing import (
    process_table_data
)

def add_unique_suffix_to_duplicates(df, column_name):
    """
    Appends '(Uniq:1)', '(Uniq:2)', etc., to duplicate entries in the specified column,
    while skipping empty or NaN values.

    Args:
        df (pd.DataFrame): Input DataFrame.
        column_name (str): Name of the column to handle duplicates.

    Returns:
        pd.DataFrame: Updated DataFrame with unique values in the specified column.
    """
    # Track counts of each value to generate unique suffixes
    value_counts = {}
    
    def generate_unique_name(value):
        # Skip empty or NaN values
        if pd.isna(value) or str(value).strip() == "":
            return value
        # If this value has not been seen before, keep it as is
        if value not in value_counts:
            value_counts[value] = 1
            return value
        else:
            # Add a unique suffix for duplicates
            value_counts[value] += 1
            return f"{value} (Uniq:{value_counts[value]})"

    # Apply uniqueness logic to the specified column
    df[column_name] = df[column_name].apply(generate_unique_name)
    return df



def save_sections_to_excel_and_csv(section_data, filename, output_folder, config=None):
    """
    Saves processed section-specific data to both Excel and a single combined CSV file.
    Incorporates section-specific configurations.

    Args:
        section_data (dict): Section data containing tables or other information.
        filename (str): Name of the input file.
        output_folder (str): Path to save the processed Excel and CSV files.
        config (dict, optional): Configuration dictionary containing per-section settings. 

    Returns:
        dict: Result dictionary with 'success' or 'failure' status and relevant paths.
    """
    config = config or {}
    base_filename = os.path.splitext(filename)[0]
    excel_path = os.path.join(output_folder, f"{base_filename}_sections_processed.xlsx")
    combined_csv_path = os.path.join(output_folder, f"{base_filename}_combined.csv")
    logger.info(f"====section_data====={section_data}")

    try:
        has_data = False
        combined_dataframes = []

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            for section, content in section_data.items():
                table_content = content.get("raw_tables", None)
                logger.info(f"Table content for section '{section}': {table_content}")
                if table_content == None:
                    table_content = content
                section_dfs = process_and_save_section(table_content, section, writer, config)
                combined_dataframes.extend(section_dfs)
                # Log the combined DataFrames for each section
                for idx, df in enumerate(section_dfs):
                    logger.info(f"Combined DataFrame {idx + 1} for section {section}:\n{df}")
                has_data = True

        if not has_data:
            logger.warning("No valid data found. Adding default placeholder sheet.")
            pd.DataFrame(["No data available"]).to_excel(writer, sheet_name="Placeholder", index=False)

        # Combine all DataFrames into a single CSV
        if combined_dataframes:
            combined_df = pd.concat(combined_dataframes, ignore_index=True)
            combined_df.to_csv(combined_csv_path, index=False)
            logger.info(f"Saved combined CSV at {combined_csv_path}")

        logger.info(f"Processed section data saved to Excel at {excel_path}")
        return {"result": "success", "excel_path": excel_path, "csv_path": combined_csv_path}
    except Exception as e:
        logger.error(f"Failed to save sections to Excel and combined CSV: {e}")
        if excel_path and os.path.exists(excel_path):
            os.remove(excel_path)
        if combined_csv_path and os.path.exists(combined_csv_path):
            os.remove(combined_csv_path)
        return {"result": "failure", "error": str(e)}

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
        # Convert column to string to handle "nan" as text
        col_as_str = col.astype(str).str.lower()
        # Check if all values are "nan", empty strings, or NaN
        return col_as_str.isin(["nan", ""]).all() or col.isna().all()

    # Apply the check to each column and drop the empty ones
    return df.loc[:, ~df.apply(is_column_empty)]

def process_and_save_section(content, section, writer, config):
    """
    Processes a single section and saves its data to Excel by stacking tables vertically without merging columns.

    Args:
        content (any): Section content (list, dict, or str).
        section (str): Name of the section.
        writer (ExcelWriter): Excel writer object.
        config (dict): Configuration dictionary.

    Returns:
        list: List of DataFrames to be combined into a single CSV.
    """
    section_dataframes = []
    section_config = config.get(section, {}).get('excel', {})
    columns_to_remove = section_config.get('columnsToRemove', [])
    grid_lines_removal = section_config.get('gridLinesRemoval', False)
    rows_to_remove = section_config.get('rowsToRemove', [])

    logger.info(f"Processing section: {section}")

    # List to accumulate raw table data without aligning columns
    raw_tables = []

    if isinstance(content, list):  # Process tables
        for idx, table in enumerate(content):
            if isinstance(table, pd.DataFrame) and not table.empty:
                logger.info(f"Processing table {idx + 1} for section {section}, shape: {table.shape}")

                # Handle duplicate rows and consolidate rows
                first_column_name = table.columns[0]
                table = add_unique_suffix_to_duplicates(table, first_column_name)
                table = consolidate_related_rows_with_order(table)

                # Convert table to raw data (array) and append
                raw_tables.append(table.to_numpy())

                # Add a simple separator row of dashes
                separator = [["---"] * table.shape[1]]
                raw_tables.append(separator)

            else:
                logger.warning(f"Skipping empty or invalid table for section: {section}")

        if raw_tables:
            # Combine tables vertically without column alignment
            combined_data = [row for table in raw_tables for row in table]
            combined_df = pd.DataFrame(combined_data)

            logger.info(f"Combined DataFrame for section {section} shape: {combined_df.shape}")
            logger.info(f"Combined DataFrame content:\n{combined_df}")

            # Apply transformations
            combined_df = process_table_data(
                combined_df,
                {
                    "columnsToRemove": columns_to_remove,
                    "gridLinesRemoval": grid_lines_removal,
                    "rowsToRemove": rows_to_remove,
                }
            )
            combined_df = drop_nan_text_columns(combined_df)

            # Save the sheet
            safe_sheet_name = sanitize_sheet_name(section)
            save_sheet(
                writer,
                combined_df,
                safe_sheet_name,
                {"gridLinesRemoval": grid_lines_removal}
            )

            combined_df["Section"] = section
            section_dataframes.append(combined_df)
        else:
            logger.warning(f"No valid tables to combine for section: {section}")

    elif isinstance(content, dict):  # Process field-based data
        df = pd.DataFrame(content.items(), columns=["Field", "Value"])
        if not df.empty:
            df = process_table_data(
                df,
                {"columnsToRemove": columns_to_remove, "gridLinesRemoval": grid_lines_removal}
            )
            df = drop_nan_text_columns(df)

            safe_sheet_name = sanitize_sheet_name(section)
            save_sheet(writer, df, safe_sheet_name, {"gridLinesRemoval": grid_lines_removal})

            df["Section"] = section
            section_dataframes.append(df)
        else:
            logger.warning(f"Generated empty DataFrame for section: {section}")

    elif isinstance(content, str):  # Process text data
        rows = [row.split() for row in content.split("\n") if row.strip()]
        df = pd.DataFrame(rows)
        if not df.empty:
            df = process_table_data(
                df,
                {"columnsToRemove": columns_to_remove, "gridLinesRemoval": grid_lines_removal}
            )
            df = drop_nan_text_columns(df)

            safe_sheet_name = sanitize_sheet_name(section)
            save_sheet(writer, df, safe_sheet_name, {"gridLinesRemoval": grid_lines_removal})

            df["Section"] = section
            section_dataframes.append(df)
        else:
            logger.warning(f"Generated empty DataFrame for section: {section}")

    else:
        logger.warning(f"Unsupported content type for section: {section}. Skipping.")

    return section_dataframes
