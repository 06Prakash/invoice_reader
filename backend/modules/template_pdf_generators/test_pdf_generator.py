from faker import Faker
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import pdfplumber
import PyPDF2
import random
import io
import os


# Initialize Faker for generating random data
fake = Faker()

def generate_random_data():
    """Generates random data for filling the form."""
    amount_words_map = {
        1000: "One Thousand Rupees only",
        5000: "Five Thousand Rupees only",
        10000: "Ten Thousand Rupees only",
        25000: "Twenty-Five Thousand Rupees only"
    }
    amount = random.choice(list(amount_words_map.keys()))
    amount_in_words = amount_words_map[amount]

    data = {
        "name": fake.name(),
        "account_number": "".join([str(random.randint(0, 9)) for _ in range(16)]),
        "ifsc_code": "SBIN" + "".join([str(random.randint(0, 9)) for _ in range(7)]),
        "amount_in_words": amount_in_words,
        "amount": amount,
        "email": fake.email(),
        "phone": fake.phone_number(),
        "pan": "ABCDE" + str(random.randint(1000, 9999)) + "F",
        "date": fake.date_this_year().strftime("%d/%m/%Y"),
        "frequency": random.choice(["Monthly", "Quarterly", "Half Yearly", "Yearly"])
    }
    return data

def create_overlay(data, width, height):
    """Creates an overlay with form data, including font adjustments, strikethrough, and tick mark."""
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(width, height))

    # Adjusted font size and positioning for specific fields
    c.setFont("Helvetica", 8)
    c.drawString(326, height - 102, data["account_number"])  # Account number

    c.setFont("Helvetica", 10)
    c.drawString(320, height - 119, data["ifsc_code"])  # IFSC code
    
    # Strikethrough for IFSC code (optional)
    ifsc_width = c.stringWidth(data["ifsc_code"], "Helvetica", 10)

    c.drawString(150, height - 134, data["amount_in_words"])  # Amount in words
    c.drawString(475, height - 134, str(data["amount"]))  # Amount

    # Name and email with reduced font size
    c.setFont("Helvetica", 9)
    c.drawString(68, height - 374, data["name"])  # Applicant name
    c.drawString(105, height - 385, data["email"])  # Email
    c.drawString(400, height - 374, data["phone"])  # Phone number
    c.drawString(240, height - 675, data["date"])  # Date

    # Reset to default font for other fields
    c.setFont("Helvetica", 8)
    c.drawString(185, height - 552, data["pan"])  # PAN number

    # line_x, line_y = 320, height - 119
    # c.line(line_x, line_y + 2, line_x + ifsc_width, line_y + 2)
    # Tick mark using ZapfDingbats font
    c.setFont("ZapfDingbats", 12)
    c.drawString(266, height - 686, chr(52))  # Tick mark in checkbox area

    c.save()
    packet.seek(0)
    return packet

def fill_form_with_data(input_pdf_path, output_pdf_path):
    """Fills the PDF form with randomly generated data."""
    # Generate random data
    data = generate_random_data()

    # Open the original PDF and get page dimensions
    with pdfplumber.open(input_pdf_path) as pdf:
        first_page = pdf.pages[0]
        width, height = first_page.width, first_page.height

        # Create the overlay with form data
        overlay = create_overlay(data, width, height)

        # Read the original PDF and overlay
        original_pdf = PyPDF2.PdfReader(input_pdf_path)
        overlay_pdf = PyPDF2.PdfReader(overlay)

        # Combine the overlay with the original page
        output = PyPDF2.PdfWriter()
        page = original_pdf.pages[0]
        page.merge_page(overlay_pdf.pages[0])
        output.add_page(page)

        # Save the combined PDF
        with open(output_pdf_path, "wb") as output_stream:
            output.write(output_stream)

# Define file paths
base_dir = os.path.dirname(__file__)
input_pdf_path = os.path.join(base_dir, "mnt/data/Sundaram SIP Form.pdf")
output_pdf_path = os.path.join(base_dir, "mnt/generated/filled_sip_form_example.pdf")

# Generate and fill the form
fill_form_with_data(input_pdf_path, output_pdf_path)
print("Filled form saved at:", output_pdf_path)
