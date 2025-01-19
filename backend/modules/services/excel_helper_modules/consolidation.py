import pandas as pd
from modules.logging_util import setup_logger
from modules.services.excel_helper_modules.excel_operations import (
    beautify_excel,
    sanitize_sheet_name,
    save_sheet,
    remove_gridlines
)
from modules.services.excel_helper_modules.data_processing import sort_headers_chronologically

logger = setup_logger(__name__)

def consolidate_dataframes(dataframes):
    """
    Consolidates a list of DataFrames by matching rows based on the first column.
    Ensures unique column names (except the first column) with suffixes (_1, _2, etc.) for duplicates.
    Preserves all data without overwriting existing values.

    Args:
        dataframes (list): List of DataFrames to consolidate.

    Returns:
        pd.DataFrame: Consolidated DataFrame with all rows and columns preserved.
    """
    try:
        if not dataframes:
            logger.warning("No DataFrames to consolidate.")
            return pd.DataFrame()

        # Ensure all DataFrames have the same first column name
        first_column = None
        for df in dataframes:
            if df.empty or df.columns.empty:
                logger.warning("One of the DataFrames is empty or has no columns.")
                continue
            if first_column is None:
                first_column = df.columns[0]
            elif first_column != df.columns[0]:
                logger.warning(
                    f"First column mismatch detected. Expected: '{first_column}', Found: '{df.columns[0]}'"
                )
                # Standardize the first column name
                df.rename(columns={df.columns[0]: first_column}, inplace=True)

        if first_column is None:
            logger.error("No valid first column found in the provided DataFrames.")
            return pd.DataFrame()

        # Collect all unique columns across DataFrames
        all_columns = set()
        for df in dataframes:
            all_columns.update(df.columns)
        all_columns = list(all_columns)

        # Align all DataFrames to ensure consistent columns
        aligned_dataframes = []
        for df in dataframes:
            aligned_df = pd.DataFrame(columns=all_columns)
            for col in df.columns:
                aligned_df[col] = df[col]
            aligned_dataframes.append(aligned_df)

        # Initialize the consolidated DataFrame with all columns
        consolidated_df = pd.DataFrame(columns=all_columns)

        # Consolidate rows based on the first column
        for df in aligned_dataframes:
            for _, row in df.iterrows():
                key = row[first_column]  # First column value (key)
                if key in consolidated_df[first_column].values:
                    # Update existing row with non-empty values only
                    idx = consolidated_df[consolidated_df[first_column] == key].index[0]
                    for col in df.columns:
                        if pd.notna(row[col]) and (pd.isna(consolidated_df.at[idx, col]) or consolidated_df.at[idx, col] == ""):
                            consolidated_df.at[idx, col] = row[col]
                else:
                    # Add new row if key is not already in the DataFrame
                    consolidated_df = pd.concat([consolidated_df, pd.DataFrame([row])], ignore_index=True)

        # Ensure consistent column ordering
        consolidated_df = consolidated_df[sorted(consolidated_df.columns)]

        # Convert numeric columns to proper data types, if applicable
        for col in consolidated_df.columns[1:]:  # Skip the first column
            try:
                consolidated_df[col] = pd.to_numeric(consolidated_df[col], errors="coerce")
            except Exception as e:
                logger.warning(f"Failed to convert column {col} to numeric: {e}")

        return consolidated_df.reset_index(drop=True)

    except Exception as e:
        logger.error(f"Error during DataFrame consolidation: {e}")
        return pd.DataFrame()

def consolidate_dataframes(dataframes):
    """
    Consolidates a list of DataFrames by matching rows based on the first column.
    Ensures all columns are preserved, appending suffixes (_1, _2, etc.) for duplicate column names.

    Args:
        dataframes (list): List of DataFrames to consolidate.

    Returns:
        pd.DataFrame: Consolidated DataFrame with all rows and unique column names preserved.
    """
    try:
        if not dataframes:
            logger.warning("No DataFrames to consolidate.")
            return pd.DataFrame()

        # Ensure all DataFrames have the same first column name
        first_column = None
        for df in dataframes:
            if df.empty or df.columns.empty:
                logger.warning("One of the DataFrames is empty or has no columns.")
                continue
            if first_column is None:
                first_column = df.columns[0]
            elif first_column != df.columns[0]:
                logger.warning(
                    f"First column mismatch detected. Expected: '{first_column}', Found: '{df.columns[0]}'"
                )
                # Standardize the first column name
                df.rename(columns={df.columns[0]: first_column}, inplace=True)

        if first_column is None:
            logger.error("No valid first column found in the provided DataFrames.")
            return pd.DataFrame()

        # Collect all unique columns across DataFrames
        all_columns = [first_column]  # Start with the first column
        column_suffixes = {}  # Track column suffixes for duplicate names

        for df in dataframes:
            for col in df.columns[1:]:  # Skip the first column
                if col not in column_suffixes:
                    column_suffixes[col] = 1
                    all_columns.append(col)
                else:
                    column_suffixes[col] += 1
                    all_columns.append(f"{col}_{column_suffixes[col]}")

        # Deduplicate the column list while preserving order
        all_columns = list(dict.fromkeys(all_columns))

        # Align all DataFrames to ensure consistent columns
        aligned_dataframes = []
        for df in dataframes:
            # Add suffixes to duplicate columns
            renamed_columns = {}
            for col in df.columns[1:]:
                if col in column_suffixes and column_suffixes[col] > 1:
                    suffix = column_suffixes[col]
                    renamed_columns[col] = f"{col}_{suffix}"
                    column_suffixes[col] -= 1  # Decrement to assign the right suffix for this DataFrame

            df = df.rename(columns=renamed_columns)

            # Align DataFrame with all columns
            aligned_df = pd.DataFrame(columns=all_columns)
            for col in df.columns:
                aligned_df[col] = df[col]
            aligned_dataframes.append(aligned_df)

        # Initialize the consolidated DataFrame with all columns
        consolidated_df = pd.DataFrame(columns=all_columns)

        # Consolidate rows based on the first column
        for df in aligned_dataframes:
            for _, row in df.iterrows():
                key = row[first_column]  # First column value (key)
                if key in consolidated_df[first_column].values:
                    # Update existing row with non-empty values only
                    idx = consolidated_df[consolidated_df[first_column] == key].index[0]
                    for col in df.columns[1:]:
                        if pd.notna(row[col]) and (pd.isna(consolidated_df.at[idx, col]) or consolidated_df.at[idx, col] == ""):
                            consolidated_df.at[idx, col] = row[col]
                else:
                    # Add new row if key is not already in the DataFrame
                    consolidated_df = pd.concat([consolidated_df, pd.DataFrame([row])], ignore_index=True)

        # Ensure consistent column ordering
        consolidated_df = consolidated_df[all_columns]

        # Convert numeric columns to proper data types, if applicable
        for col in consolidated_df.columns[1:]:  # Skip the first column
            try:
                consolidated_df[col] = pd.to_numeric(consolidated_df[col], errors="ignore")
            except Exception as e:
                logger.warning(f"Failed to convert column {col} to numeric: {e}")

        return consolidated_df.reset_index(drop=True)

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
            logger.info(f"File: {file}, Sheets: {workbook.sheet_names}")
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
                
                if not consolidated_df.empty:
                    # Identify empty columns
                    empty_columns = consolidated_df.columns[consolidated_df.isnull().all()]
                    if not empty_columns.empty:
                        logger.warning(f"Removing empty columns from the consolidated DataFrame: {empty_columns}")
                        consolidated_df.drop(columns=empty_columns, inplace=True)

                    # Ensure chronological ordering (optional)
                    logger.info(f"Data Frame before chronological ordering: {consolidated_df}")
                    consolidated_df = sort_headers_chronologically(consolidated_df)
                    logger.info(f"Data Frame after chronological ordering: {consolidated_df}")

                    # Write the consolidated data to Excel
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
