import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import pandas as pd
import os
import re

# Path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'F:\Program Files (x86)\tesseract\tesseract.exe'  # Update this path to your Tesseract executable

def pdf_to_images(pdf_path):
    return convert_from_path(pdf_path, 300)

def extract_text_from_image(image):
    return pytesseract.image_to_string(image)

def get_total(values):
    # Filter out empty strings and spaces
    filtered_values = [value for value in values if value.strip()]
    # Return the last non-empty value
    return filtered_values[-1] if filtered_values else None

def extract_billed_to(data):
    parts = [part.strip() for part in data.split('|') if part.strip()]
    
    # Find the first non-empty value before any "DC.NO" part
    first_non_empty_before_dc = []
    for part in parts:
        if part not in ("Billed To,", "Billed To"):
            if "DC.NO" in part:
                part = part.split('DC.NO')[0]
            first_non_empty_before_dc.append(part)
    
    # Find the last non-empty value
    last_non_empty = parts[-1] if parts else None

    # Combine the first values before DC.NO and the last non-empty value into a string
    if last_non_empty:
        combined_string = ', '.join(first_non_empty_before_dc + [last_non_empty])
    else:
        combined_string = ', '.join(first_non_empty_before_dc)
    return first_non_empty_before_dc[0] + ', '+ first_non_empty_before_dc[-1]

def parse_invoice_text(text):
    # Initialize dictionary to hold extracted data
    invoice_data = {
        "VAT REG NO": None,
        "Sales Invoice No": None,
        "Invoice Time": None,
        "Date of Invoice": None,
        "Sales Person": None,
        "Sales Type": None,
        "Comptroller": None,
        "Billed To": None,
        "Telephone": None,
        "TRN": None,
        "Total": None,
        "Items": []
    }

    lines = text.split('\n')
    item_section = False
    billed_to_section = False
    telephone_and_trn_section = False
    billed_to_lines = []

    for line in lines:
        line = line.strip()

        # Extract VAT REG NO
        match = re.search(r'VAT REG NO\s*:\s*([\w\/\-]+)', line)
        if match:
            invoice_data["VAT REG NO"] = match.group(1).strip()

        # Extract sales invoice number
        match = re.search(r'Sales Invoice No\s*:\s*([\w\/\-]+)', line)
        if match:
            invoice_data["Sales Invoice No"] = match.group(1).strip()

        # Extract invoice time
        match = re.search(r'Invoice Time\s*:\s*([\d:]+)', line)
        if match:
            invoice_data["Invoice Time"] = match.group(1).strip()

        # Extract date of invoice
        match = re.search(r'Date of Invoice\s*:\s*([\d\/]+)', line)
        if match:
            invoice_data["Date of Invoice"] = match.group(1).strip()

        # Extract sales person
        match = re.search(r'Sales Person\s*:\s*(.+)', line)
        if match:
            invoice_data["Sales Person"] = match.group(1).strip().replace('|', '')

        # Extract sales type
        match = re.search(r'Sales Type\s*:\s*(.+)', line)
        if match:
            invoice_data["Sales Type"] = match.group(1).strip()
            if 'Comptroller' in invoice_data["Sales Type"]:
                invoice_data["Sales Type"] = invoice_data["Sales Type"].split('Comptroller')[0]

        # Extract comptroller
        match = re.search(r'Comptroller\s*:\s*(.+)', line)
        if match:
            invoice_data["Comptroller"] = match.group(1).strip().replace('|', '')

        # Start collecting Billed To information
        if "Billed To" in line:
            billed_to_section = True
            billed_to_lines.append(line.split(":", 1)[1].strip() if ":" in line else line)
            continue
        if billed_to_section:
            if "Telephone" in line or "TRN" in line:
                billed_to_section = False
                telephone_and_trn_section = True
            else:
                billed_to_lines.append(line.strip())
                continue

        # Collect Telephone and TRN information
        # Collect Telephone and TRN information
        if telephone_and_trn_section:
            if "Telephone" in line and "TRN" in line:
                telephone_part = line.split("Telephone")[1].split("TRN")[0].strip()
                trn_part = line.split("TRN")[1].strip()
                
                # Extract only numbers from Telephone part
                match = re.search(r'(\d+)', telephone_part)
                if match:
                    invoice_data["Telephone"] = match.group(1)
                
                # Extract only numbers from TRN part
                match = re.search(r'(\d+)', trn_part)
                if match:
                    invoice_data["TRN"] = match.group(1)
            
            elif "Telephone" in line:
                telephone_part = line.split("Telephone", 1)[1].strip()
                
                # Extract only numbers from Telephone part
                match = re.search(r'(\d+)', telephone_part)
                if match:
                    invoice_data["Telephone"] = match.group(1)
            
            elif "TRN" in line:
                trn_part = line.split("TRN", 1)[1].strip()
                
                # Extract only numbers from TRN part
                match = re.search(r'(\d+)', trn_part)
                if match:
                    invoice_data["TRN"] = match.group(1)

        if "Description" in line and "Qty" in line:
            telephone_and_trn_section = False
            item_section = True


        # Combine Billed To lines
        if billed_to_lines and not billed_to_section:
            invoice_data["Billed To"] = " ".join(billed_to_lines)
            billed_to_lines = []

        # Extract items
        if item_section:
            # print("Item section")
            if line and not line.startswith("+") and not line.startswith("-"):
                parts = re.split(r'\s{2,}', line)  # Split by two or more spaces
                if len(parts) >= 5:  # Ensure that it has enough parts to be a valid item line
                    item = {
                        "Code": parts[0],
                        "Description": parts[1],
                        "Qty": parts[2],
                        "Net Rate": parts[3],
                        "Amount": parts[4]
                    }
                    invoice_data["Items"].append(item)
        
        
        # Extract total from the bottom of the document
        if "Total" in line:
            parts = line.split('|')
            print(parts)
            if len(parts) > 1:
                invoice_data["Total"] = get_total(parts)
            item_section = False
    invoice_data['Billed To'] = extract_billed_to(invoice_data['Billed To'])

    return invoice_data

def save_to_csv(data, output_path):
    # Create a DataFrame for the invoice details
    invoice_details = pd.DataFrame([{
        "VAT REG NO": data.get("VAT REG NO", ""),
        "Sales Invoice No": data.get("Sales Invoice No", ""),
        "Invoice Time": data.get("Invoice Time", ""),
        "Date of Invoice": data.get("Date of Invoice", ""),
        "Sales Person": data.get("Sales Person", ""),
        "Sales Type": data.get("Sales Type", ""),
        "Comptroller": data.get("Comptroller", ""),
        "Billed To": data.get("Billed To", ""),
        "Telephone": data.get("Telephone", ""),
        "TRN": data.get("TRN", ""),
        "Total": data.get("Total", "")
    }])
    invoice_details.to_csv(output_path.replace('.csv', '_details.csv'), index=False)

    # Create a DataFrame for the items
    if data["Items"]:
        items_df = pd.DataFrame(data["Items"])
        items_df.to_csv(output_path.replace('.csv', '_items.csv'), index=False)

def process_pdf(pdf_path, output_dir, invoice_count):
    images = pdf_to_images(pdf_path)

    for i, image in enumerate(images):
        text = extract_text_from_image(image)
        data = parse_invoice_text(text)

        if data:
            output_path = os.path.join(output_dir, f'invoice_{invoice_count}.csv')
            save_to_csv(data, output_path)

def process_pdfs(pdf_paths, output_dir):
    invoice_count = 1
    for pdf_path in pdf_paths:
        print(f"Started processing pdf {pdf_path}..")
        process_pdf(pdf_path, output_dir, invoice_count)
        invoice_count += 1

def consolidate_csv(directory_path, output_file):
    # List to hold dataframes
    dataframes = []

    # Iterate over all files in the directory
    for filename in os.listdir(directory_path):
        # Check if the file is a CSV file
        if filename.endswith('.csv'):
            # Create the full file path
            file_path = os.path.join(directory_path, filename)
            # Read the CSV file into a dataframe
            df = pd.read_csv(file_path)
            # Append the dataframe to the list
            dataframes.append(df)

    # Concatenate all dataframes
    consolidated_df = pd.concat(dataframes, ignore_index=True)

    # Save the consolidated dataframe to a new CSV file
    consolidated_df.to_csv(output_file, index=False)

# Example usage
pdf_paths = ["107691(1158).pdf",
"107692(1157).pdf",
"107811(1115).pdf",
"107813(1100).pdf",
"107815(1109).pdf"]
output_dir = 'output_invoices'  # Output directory to save CSV files

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

process_pdfs(pdf_paths, output_dir)
consolidate_csv(output_dir, 'consolidated.csv')
