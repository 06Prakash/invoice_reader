# Invoice Extractor

Invoice Extractor is a web application that allows users to upload invoice PDFs, specify fields to extract, and download the extracted data in various formats (JSON, CSV, or plain text). The backend is powered by Flask, and the frontend is a simple HTML/JavaScript interface. The application uses Tesseract OCR and pdf2image for PDF processing.

## Features

- Upload invoice PDF files
- Specify fields to extract from invoices
- Specify separator used in the invoice (e.g., ':', '|', '-')
- Download extracted data in JSON, CSV, or plain text format
- Dockerized for easy deployment

## Prerequisites

- Docker
- Python 3.9 (if running locally without Docker)

## Installation

### Using Docker

1. **Clone the repository**:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. **Build the Docker image**:
    ```sh
    docker build -t invoice-extractor .
    ```

3. **Run the Docker container**:
    ```sh
    docker run -p 5001:5000 invoice-extractor
    ```

4. **Access the application**:
    Open your web browser and go to `http://localhost:5001`.

### Running Locally

1. **Clone the repository**:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

3. **Install Tesseract and Poppler**:
    - On Ubuntu:
        ```sh
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev poppler-utils
        ```
    - On Windows, download and install Tesseract from [here](https://github.com/UB-Mannheim/tesseract/wiki) and Poppler from [here](http://blog.alivate.com.au/poppler-windows/).

4. **Run the Flask application**:
    ```sh
    python invoice_reader_app.py
    ```

5. **Access the application**:
    Open your web browser and go to `http://localhost:5000`.

## Usage

1. **Upload an Invoice PDF**:
    - Click on the "Choose File" button and select a PDF file.
    - Click on the "Upload" button to upload the file.

2. **Specify Extraction Criteria**:
    - Enter the fields you want to extract from the invoice, separated by commas.
    - Enter the separator used in the invoice (e.g., ':', '|', '-').
    - Select the desired output format (JSON, CSV, or Text).

3. **Extract Data**:
    - Click on the "Extract Data" button to process the PDF and extract the specified fields.
    - The extracted data will be displayed in the specified format.

## Project Structure
    invoice_reader/
        ├── Dockerfile
        ├── requirements.txt
        ├── invoice_reader_app.py
        ├── static/
        │ └── invoice_reader_ui.html
        ├── ocr_invoice_app.py
        └── test_pdfs/

   - **Dockerfile**: Docker configuration file for building the image.
   - **requirements.txt**: Python dependencies file.
   - **invoice_reader_app.py**: Main Flask application.
   - **static/**: Directory containing static files (HTML, CSS, JS).
   - **ocr_invoice_app.py**: Additional OCR processing script (if needed).
   - **test_pdfs/**: Directory for storing test PDFs.

## Contributing

Feel free to fork this repository, make changes, and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [pdf2image](https://github.com/Belval/pdf2image)
- [Poppler](https://poppler.freedesktop.org/)

