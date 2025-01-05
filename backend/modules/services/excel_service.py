import pandas as pd
import os
from openpyxl import load_workbook
from modules.logging_util import setup_logger
logger = setup_logger()

def convert_parentheses_to_negative(df):
    """
    Converts values in parentheses (e.g., "(10)") to negative numbers (e.g., -10).
    Handles values with commas like "(3,140)" as well.
    """
    logger.info("Attempting to convert parentheses to negative numbers..")
    return df.applymap(lambda x: 
        -float(str(x).replace(',', '').strip('()')) if isinstance(x, str) and x.startswith('(') and x.endswith(')') 
        else x)

def remove_columns(df, columns_to_remove):
    """
    Removes specified columns from the DataFrame.
    """
    logger.info(f"Attempting to remove columns {', '.join(columns_to_remove)}")
    df.columns = df.columns.str.strip()  # Strip spaces from column names
    df.columns = df.columns.str.lower()  # Normalize column names to lowercase
    columns_to_remove = [col.lower() for col in columns_to_remove]  # Normalize target columns
    return df.drop(columns=[col for col in columns_to_remove if col in df.columns], errors='ignore')

def consolidate_tables(tables):
    """
    Consolidates a list of DataFrames into a single DataFrame.
    """
    logger.info(f"Attempting to consolidate tables {', '.join(tables)}")
    return pd.concat(tables, ignore_index=True) if tables else pd.DataFrame()


def remove_gridlines(writer, sheet_name):
    """
    Removes gridlines from the specified sheet in the Excel writer.
    """
    logger.info(f"Attempting to remove gridlines from sheet {sheet_name}..")
    worksheet = writer.sheets[sheet_name]
    worksheet.sheet_view.showGridLines = False


def process_excel(input_excel_path, output_excel_path, config=None):
    """
    Processes an Excel file based on the provided configuration.

    Args:
        input_excel_path (str): Path to the input Excel file.
        output_excel_path (str): Path to save the processed Excel file.
        config (dict, optional): Configuration dictionary with processing options.

    Returns:
        dict: Status and path to the processed file.
    """
    try:
        # Load the Excel file
        workbook = pd.ExcelFile(input_excel_path)
        processed_sheets = {}

        # Default configuration
        config = config or {}
        logger.info(f"Configuration provided: {config}")
        columns_to_remove = config.get("columnsToRemove", [])
        grid_lines_removal = config.get("gridLinesRemoval", False)
        merge_to_one_sheet = config.get("Merge tables to one sheet", False)

        consolidated_data = []

        # Process each sheet in the workbook
        with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:
            for sheet_name in workbook.sheet_names:
                # Load sheet into DataFrame
                logger.info(f"Processing excel data frame for sheet name {sheet_name}")
                df = workbook.parse(sheet_name)

                # Step 1: Convert parentheses to negative numbers
                df = convert_parentheses_to_negative(df)

                # Step 2: Remove specified columns
                if columns_to_remove:
                    df = remove_columns(df, columns_to_remove)
                logger.info(f"After removing columns {','.join(columns_to_remove)} header {str(df)}")

                # Step 3: Remove gridlines if required
                if merge_to_one_sheet:
                    consolidated_data.append(df)
                else:
                    # Save processed sheet to individual sheet
                    df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                    if grid_lines_removal:
                        remove_gridlines(writer, sheet_name)

                processed_sheets[sheet_name] = df.shape

            # Step 5: Merge all tables into one sheet if enabled
            if merge_to_one_sheet and consolidated_data:
                merged_df = consolidate_tables(consolidated_data)
                merged_df.to_excel(writer, sheet_name="Consolidated", index=False, header=False)
                if grid_lines_removal:
                    remove_gridlines(writer, "Consolidated")

        return {
            "status": "success",
            "message": f"Processed Excel file saved at {output_excel_path}",
            "processed_sheets": processed_sheets,
            "output_path": output_excel_path
        }

    except Exception as e:
        logger.error(f"Error during Excel processing: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def save_sheet(writer, df, sheet_name, config):
    """
    Saves a DataFrame to a specific sheet in the Excel writer.
    Applies configurations like gridline removal.
    """
    df.to_excel(writer, sheet_name=sheet_name[:31], index=False, header=False)
    if config.get("gridLinesRemoval", False):
        remove_gridlines(writer, sheet_name)

def process_table_data(df, config):
    """
    Processes table data by applying transformations like:
    - Removing numeric headers
    - Removing specific columns
    - Converting parentheses to negatives
    """
    if config.get("numericHeaderRemoval", False):
        df = remove_numeric_headers(df)

    df = convert_parentheses_to_negative(df)

    if columns := config.get("columnsToRemove", []):
        df = remove_columns(df, columns)
    logger.info(f"Data Frame after processing: {df}")
    return df

def consolidate_and_save(writer, consolidated_data, config):
    """
    Consolidates multiple DataFrames and saves them to a single sheet.
    """
    if consolidated_data:
        merged_df = consolidate_tables(consolidated_data)
        save_sheet(writer, merged_df, "Consolidated", config)

def save_sections_to_excel(section_data, filename, output_folder, config=None):
    """
    Saves processed section-specific data to an Excel file.
    Ensures at least one visible sheet exists, even if no data is extracted.

    Args:
        section_data (dict): Data for each section.
        filename (str): Name of the file being processed.
        output_folder (str): Folder to save the output file.
        config (dict): Configuration options for processing.

    Returns:
        dict: A dictionary with the result ('success' or 'failure') and either the Excel path or an error message.
    """
    config = config or {}
    excel_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_sections_processed.xlsx")
    consolidated_data = []
    logger.info(f"====section_data====={section_data}")

    try:
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            has_data = False

            for section, content in section_data.items():
                logger.info(f"Processing section: {section}, Content Type: {type(content)}")
                if isinstance(content, list):  # Process tables
                    for idx, table in enumerate(content):
                        if isinstance(table, pd.DataFrame) and not table.empty:
                            logger.info(f"Writing table {idx + 1} for section {section}, shape: {table.shape}")
                            table = process_table_data(table, config)
                            if config.get("Merge tables to one sheet", False):
                                consolidated_data.append(table)
                            else:
                                save_sheet(writer, table, f"{section}_Table_{idx + 1}", config)
                            has_data = True
                        else:
                            logger.warning(f"Skipping empty or invalid table for section: {section}")
                elif isinstance(content, dict):  # Process field-based data
                    df = pd.DataFrame(content.items(), columns=["Field", "Value"])
                    if not df.empty:
                        df = process_table_data(df, config)
                        save_sheet(writer, df, section, config)
                        has_data = True
                    else:
                        logger.warning(f"Generated empty DataFrame for section: {section}")
                elif isinstance(content, str):  # Process text data
                    rows = [row.split() for row in content.split("\n") if row.strip()]
                    df = pd.DataFrame(rows)
                    if not df.empty:
                        df = process_table_data(df, config)
                        save_sheet(writer, df, section, config)
                        has_data = True
                    else:
                        logger.warning(f"Generated empty DataFrame for section: {section}")
                else:
                    logger.warning(f"Unsupported content type for section: {section}. Skipping.")

            if config.get("Merge tables to one sheet", False) and consolidated_data:
                consolidate_and_save(writer, consolidated_data, config)
            elif config.get("Merge tables to one sheet", False):
                logger.warning("No consolidated data available to save.")

            if not has_data:
                logger.warning("No valid data found. Adding default placeholder sheet.")
                pd.DataFrame(["No data available"]).to_excel(writer, sheet_name="Placeholder", index=False)

        logger.info(f"Processed section data saved to Excel at {excel_path}")
        return {"result": "success", "excel_path": excel_path}
    except Exception as e:
        logger.error(f"Failed to save sections to Excel: {e}")
        return {"result": "failure", "error": str(e)}

 