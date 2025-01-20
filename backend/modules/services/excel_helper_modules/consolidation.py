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
    Ensures all columns are preserved, appending suffixes (_1, _2, etc.) for duplicate column names.
    Groups context-based rows and ensures non-context values are preserved in order.

    Args:
        dataframes (list): List of DataFrames to consolidate.

    Returns:
        pd.DataFrame: Consolidated DataFrame with all rows and unique column names preserved.
    """
    try:
        if not dataframes:
            logger.warning("No DataFrames to consolidate.")
            return pd.DataFrame()

        # Step 1: Validate and standardize the first column
        first_column = validate_and_standardize_first_column(dataframes)
        if first_column is None:
            logger.error("No valid first column found in the provided DataFrames.")
            return pd.DataFrame()
        
        # Step 2: Collect and apply unique column names
        all_columns, dataframes = collect_and_apply_unique_columns(dataframes, first_column)


        # Step 3: Align all DataFrames to the collected columns
        aligned_dataframes = align_dataframes(dataframes, all_columns)

        # Step 4: Consolidate rows into a single DataFrame
        consolidated_df = pd.DataFrame(columns=all_columns)
        seen_keys = {}
        for df in aligned_dataframes:
            consolidated_df = consolidate_rows(df, consolidated_df, first_column, seen_keys)

        # # Step 5: Update column suffixes for duplicates
        consolidated_df = update_column_suffixes(consolidated_df, first_column)


        return consolidated_df.reset_index(drop=True)

    except Exception as e:
        logger.error(f"Error during DataFrame consolidation: {e}")
        return pd.DataFrame()
def collect_and_apply_unique_columns(dataframes, first_column):
    all_columns = [first_column]
    column_suffixes = {}

    for df in dataframes:
        updated_columns = []
        for col in df.columns:
            if col == first_column:
                updated_columns.append(col)
                continue
            if col not in column_suffixes:
                column_suffixes[col] = 1
                unique_col_name = col
            else:
                column_suffixes[col] += 1
                unique_col_name = f"{col}_{column_suffixes[col]}"
            updated_columns.append(unique_col_name)
            all_columns.append(unique_col_name)
        df.columns = updated_columns  # Apply unique column names to the DataFrame

    # Deduplicate the column list while preserving order
    all_columns = list(dict.fromkeys(all_columns))
    return all_columns, dataframes

def validate_and_standardize_first_column(dataframes):
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
            df.rename(columns={df.columns[0]: first_column}, inplace=True)
    return first_column

def collect_unique_columns(dataframes, first_column):
    all_columns = [first_column]
    column_suffixes = {}

    for df in dataframes:
        for col in df.columns[1:]:
            if col not in column_suffixes:
                column_suffixes[col] = 1
                all_columns.append(col)
            else:
                column_suffixes[col] += 1
                unique_col_name = f"{col}_{column_suffixes[col]}"
                all_columns.append(unique_col_name)

    return list(dict.fromkeys(all_columns))

def align_dataframes(dataframes, all_columns):
    aligned_dataframes = []
    for df in dataframes:
        aligned_df = pd.DataFrame(columns=all_columns)
        for col in df.columns:
            if col in all_columns:
                aligned_df[col] = df[col]
        aligned_df.fillna("", inplace=True)
        logger.debug(f"Aligned DataFrame:\n{aligned_df.head()}")
        aligned_dataframes.append(aligned_df)
    return aligned_dataframes


def add_unique_suffix(key, seen_keys):
    if key in seen_keys:
        count = seen_keys[key]
        new_key = f"{key} (Uniq: {count})"
        seen_keys[key] += 1
        return new_key
    else:
        seen_keys[key] = 1
        return key

def consolidate_rows(df, consolidated_df, first_column, seen_keys):
    context_group = None
    for _, row in df.iterrows():
        key = row[first_column]

        # Identify context group based on empty/non-empty values
        if pd.isna(row.drop(first_column).dropna().iloc[0]):
            context_group = key

        # Consolidate data into existing or new rows
        if key in consolidated_df[first_column].values:
            idx_existing = consolidated_df[consolidated_df[first_column] == key].index[0]
            for col in df.columns[1:]:
                if pd.notna(row[col]) and (pd.isna(consolidated_df.at[idx_existing, col]) or consolidated_df.at[idx_existing, col] == ""):
                    consolidated_df.at[idx_existing, col] = row[col]
        else:
            if context_group and key != context_group:
                key = f"{context_group} | {key}"
            unique_key = add_unique_suffix(key, seen_keys)
            row[first_column] = unique_key
            new_row = {col: "" for col in consolidated_df.columns}
            for col in row.index:
                new_row[col] = row[col]
            consolidated_df = pd.concat([consolidated_df, pd.DataFrame([new_row])], ignore_index=True)
    return consolidated_df

def update_column_suffixes(consolidated_df, first_column):
    """
    Updates column names with suffixes (_1, _2, etc.) for duplicate columns
    to ensure unique column names while preserving the data.

    Args:
        consolidated_df (pd.DataFrame): The DataFrame to process.
        first_column (str): The name of the first column (context column) to exclude from renaming.

    Returns:
        pd.DataFrame: The DataFrame with updated column names.
    """
    column_counts = {}
    renamed_columns = {}  # Track original to new column names

    # Iterate over columns to identify duplicates and assign unique suffixes
    for col in list(consolidated_df.columns):
        if col == first_column:
            continue  # Skip the first column

        if col in column_counts:
            column_counts[col] += 1
            new_col_name = f"{col}_{column_counts[col]}"
            renamed_columns[col] = new_col_name
        else:
            column_counts[col] = 1
            renamed_columns[col] = col

    # Apply the renaming while preserving data integrity
    for original_col, new_col in renamed_columns.items():
        if original_col != new_col:
            # Debug to ensure data is preserved before renaming
            logger.info(f"Renaming column '{original_col}' to '{new_col}'")
            consolidated_df.rename(columns={original_col: new_col}, inplace=True)

    # Verify that all renamed columns exist and contain the original data
    for original_col, new_col in renamed_columns.items():
        if original_col != new_col:
            if new_col not in consolidated_df.columns:
                logger.info(f"Renamed column '{new_col}' is missing after renaming.")
            else:
                logger.info(f"Column '{original_col}' successfully renamed to '{new_col}'.")

    return consolidated_df

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
