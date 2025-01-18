import os
import pandas as pd
from modules.logging_util import setup_logger
logger = setup_logger(__name__)
from modules.services.excel_helper_modules.excel_operations import (
    save_sheet,
    sanitize_sheet_name
)
from modules.services.excel_helper_modules.data_processing import (
    process_table_data
)

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
                if table_content == None:
                    table_content = content
                section_dfs = process_and_save_section(table_content, section, base_filename, output_folder, writer, config)
                combined_dataframes.extend(section_dfs)
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

def process_and_save_section(content, section, base_filename, output_folder, writer, config):
    """
    Processes a single section and saves its data to both Excel and returns the DataFrame for CSV combination.

    Args:
        content (any): Section content (list, dict, or str).
        section (str): Name of the section.
        base_filename (str): Base name for files.
        output_folder (str): Path to save files.
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

    logger.info(f"Processing section: {section} with config: {section_config}, Content Type: {type(content)}")

    if isinstance(content, list):  # Process tables
        for idx, table in enumerate(content):
            if isinstance(table, pd.DataFrame) and not table.empty:
                logger.info(f"Writing table {idx + 1} for section {section}, shape: {table.shape}")
                safe_sheet_name = sanitize_sheet_name(f"{section}_Table_{idx + 1}")
                logger.info(f"Sheet name: {safe_sheet_name}")

                # Process table data with section-specific configuration
                table = process_table_data(
                    table,
                    {"columnsToRemove": columns_to_remove, "gridLinesRemoval": grid_lines_removal, 'rowsToRemove': rows_to_remove}
                )
                save_sheet(
                    writer,
                    table,
                    safe_sheet_name,
                    {"gridLinesRemoval": grid_lines_removal}
                )
                table["Section"] = section
                section_dataframes.append(table)
            else:
                logger.warning(f"Skipping empty or invalid table for section: {section}")

    elif isinstance(content, dict):  # Process field-based data
        logger.info(f"Dictionary content: {content}")
        df = pd.DataFrame(content.items(), columns=["Field", "Value"])
        if not df.empty:
            safe_sheet_name = sanitize_sheet_name(section)
            df = process_table_data(
                df,
                {"columnsToRemove": columns_to_remove, "gridLinesRemoval": grid_lines_removal}
            )
            save_sheet(
                writer,
                df,
                safe_sheet_name,
                {"gridLinesRemoval": grid_lines_removal}
            )
            df["Section"] = section
            section_dataframes.append(df)
        else:
            logger.warning(f"Generated empty DataFrame for section: {section}")

    elif isinstance(content, str):  # Process text data
        rows = [row.split() for row in content.split("\n") if row.strip()]
        df = pd.DataFrame(rows)
        if not df.empty:
            safe_sheet_name = sanitize_sheet_name(section)
            df = process_table_data(
                df,
                {"columnsToRemove": columns_to_remove, "gridLinesRemoval": grid_lines_removal}
            )
            save_sheet(
                writer,
                df,
                safe_sheet_name,
                {"gridLinesRemoval": grid_lines_removal}
            )
            df["Section"] = section
            section_dataframes.append(df)
        else:
            logger.warning(f"Generated empty DataFrame for section: {section}")

    else:
        logger.warning(f"Unsupported content type for section: {section}. Skipping.")

    return section_dataframes
