import pandas as pd
from modules.logging_util import setup_logger
from modules.services.excel_helper_modules.excel_operations import (
    beautify_excel,
    sanitize_sheet_name,
    save_sheet
)
from modules.services.excel_helper_modules.data_processing import sort_headers_chronologically

logger = setup_logger(__name__)

def consolidate_tables(tables):
    """
    Consolidates a list of DataFrames into a single DataFrame.
    """
    logger.info(f"Attempting to consolidate tables {', '.join(tables)}")
    return pd.concat(tables, ignore_index=True) if tables else pd.DataFrame()

def consolidate_dataframes(dataframes):
    """
    Consolidates a list of DataFrames by matching rows based on the first column.

    Args:
        dataframes (list): List of DataFrames to consolidate.

    Returns:
        pd.DataFrame: Consolidated DataFrame.
    """
    try:
        if not dataframes:
            logger.warning("No DataFrames to consolidate.")
            return pd.DataFrame()

        # Use the first DataFrame as the base
        consolidated_df = dataframes[0].copy()
        key_column = consolidated_df.columns[0]  # Assume the first column is the key

        for df in dataframes[1:]:
            # Merge DataFrames on the key column
            df = df.copy()
            consolidated_df = pd.merge(
                consolidated_df,
                df,
                on=key_column,
                how="outer",
                suffixes=("", "_other")
            )

            # Sum numeric columns for matching rows
            numeric_cols = consolidated_df.select_dtypes(include="number").columns
            for col in numeric_cols:
                if col.endswith("_other"):
                    base_col = col.replace("_other", "")
                    if base_col in consolidated_df:
                        consolidated_df[base_col] += consolidated_df[col]
                        consolidated_df.drop(columns=[col], inplace=True)

            # Fill NaN with 0 for numeric columns
            consolidated_df[numeric_cols] = consolidated_df[numeric_cols].fillna(0)

        return consolidated_df

    except Exception as e:
        logger.error(f"Error during DataFrame consolidation: {e}")
        return pd.DataFrame()

def consolidate_excel_sheets(input_files, output_excel_path, saved_config):
    """
    Consolidates multiple Excel files by matching rows in specified sheets
    and creating a new consolidated Excel file with beautification.

    Args:
        input_files (list): List of input Excel file paths.
        output_excel_path (str): Path to save the consolidated Excel file.

    Returns:
        dict: Status and path to the consolidated file.
    """
    try:
        logger.info(f"Starting consolidation for files: {input_files}")
        sheet_data = {}  # Dictionary to hold data for each sheet across files

        # Read all input files and load the data for each sheet
        for file in input_files:
            workbook = pd.ExcelFile(file)
            for sheet_name in workbook.sheet_names:
                sanitized_name = sanitize_sheet_name(sheet_name)
                if sanitized_name not in sheet_data:
                    sheet_data[sanitized_name] = []
                # Read the sheet and append its DataFrame to the list
                df = workbook.parse(sheet_name)
                logger.info(f"Loaded data for sheet {sanitized_name} from file {file}, shape: {df.shape}")
                sheet_data[sanitized_name].append(df)

        # Consolidate data for each sheet
        with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:
            for sheet_name, dataframes in sheet_data.items():
                logger.info(f"Consolidating sheet: {sheet_name}")
                consolidated_df = consolidate_dataframes(dataframes)
                # remove_gridlines(writer, sheet_name)
                if not consolidated_df.empty:
                    logger.info(f"Data Frame before chronological ordering: {consolidated_df}")
                    consolidated_df = sort_headers_chronologically(consolidated_df)
                    logger.info(f"Data Frame after chronological ordering: {consolidated_df}")
                    consolidated_df.to_excel(writer, sheet_name=sheet_name, index=False, header=True)
                    logger.info(f"Consolidated data written to sheet: {sheet_name}")
                    # Apply beautification to the sheet
                    beautify_excel(writer, sheet_name)
                else:
                    logger.warning(f"No data to consolidate for sheet: {sheet_name}")

        logger.info(f"Consolidated Excel file saved at {output_excel_path}")
        return {
            "status": "success",
            "message": f"Consolidated Excel file saved at {output_excel_path}",
            "output_path": output_excel_path,
        }

    except Exception as e:
        logger.error(f"Error during consolidation: {e}")
        return {"status": "error", "message": str(e)}
    
def consolidate_and_save(writer, consolidated_data, config):
    """
    Consolidates multiple DataFrames and saves them to a single sheet with beautification.

    Args:
        writer (ExcelWriter): Excel writer object.
        consolidated_data (list): List of DataFrames to consolidate.
        config (dict): Configuration dictionary.
    """
    if consolidated_data:
        merged_df = consolidate_tables(consolidated_data)
        sheet_name = "Consolidated"
        save_sheet(writer, merged_df, sheet_name, config)
        beautify_excel(writer, sheet_name)  # Beautify the consolidated sheet