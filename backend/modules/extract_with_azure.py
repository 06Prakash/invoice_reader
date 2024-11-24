from concurrent.futures import ThreadPoolExecutor
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import os

# Azure Form Recognizer Configuration
AZURE_ENDPOINT = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT", "YOUR_END_POINT_HERE")
AZURE_KEY = os.getenv("AZURE_FORM_RECOGNIZER_KEY", "YOUR_KEY_HERE")

# Initialize the Azure Form Recognizer client
azure_client = DocumentAnalysisClient(endpoint=AZURE_ENDPOINT, credential=AzureKeyCredential(AZURE_KEY))

def extract_with_azure(filename, upload_folder, template, logger):
    """
    Perform Azure-based extraction using Form Recognizer.
    """
    pdf_path = os.path.join(upload_folder, filename)
    logger.info(f"Starting Azure extraction for {filename} using template {template['name']}")

    try:
        # Read the PDF file
        with open(pdf_path, "rb") as file:
            poller = azure_client.begin_analyze_document("prebuilt-layout", document=file)
            result = poller.result()

        extracted_data = {}
        for page in result.pages:
            logger.info(f"Processing page {page.page_number}")
            for table in page.tables:
                for cell in table.cells:
                    logger.debug(f"Cell text: {cell.content}")

        # Example template-based data extraction
        for field in template["fields"]:
            name = field["name"]
            keyword = field["keyword"]
            value = next(
                (cell.content for table in result.tables for cell in table.cells if keyword.lower() in cell.content.lower()), 
                None
            )
            extracted_data[name] = value or "Not Found"

        return filename, extracted_data, []  # Returning empty lines as Azure handles structured data
    except Exception as e:
        logger.error(f"Azure extraction failed for {filename}: {str(e)}")
        return filename, {'error': str(e)}, []

# Register the Azure extraction route
@app.route('/extract-azure', methods=['POST'])
@jwt_required()
def extract_data_azure():
    """
    Extract data from PDFs using Azure Form Recognizer.
    """
    global progress
    data = request.json
    if 'filenames' not in data or 'template' not in data:
        logger.error('Filenames and template are required')
        return jsonify({'message': 'Filenames and template are required'}), 400

    filenames = data['filenames']
    template_name = data['template']
    upload_folder = app.config['UPLOAD_FOLDER']

    if template_name == "Default Template":
        template_path = 'resources/json_templates/default_template.json'
    else:
        template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{template_name}.json')

    if not os.path.exists(template_path):
        logger.error('Template not found')
        return jsonify({'message': 'Template not found'}), 404

    with open(template_path, 'r') as f:
        template = json.load(f)

    progress = 0  # Reset progress
    results = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(extract_with_azure, filename, upload_folder, template) for filename in filenames]
        for future in as_completed(futures):
            results.append(future.result())

    response_data = {filename: data for filename, data, _ in results}

    return jsonify({
        'json_data': response_data
    }), 200
