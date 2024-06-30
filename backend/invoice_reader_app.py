from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
import pytesseract
import json
import csv
import io

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

UPLOAD_FOLDER = 'uploads'
TEMPLATE_FOLDER = 'templates'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMPLATE_FOLDER'] = TEMPLATE_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(TEMPLATE_FOLDER):
    os.makedirs(TEMPLATE_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'filename': filename}), 200
    return jsonify({'message': 'File type not allowed'}), 400

@app.route('/templates', methods=['POST'])
def save_template():
    data = request.json
    template_name = data['name']
    template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{template_name}.json')
    with open(template_path, 'w') as f:
        json.dump(data, f)
    return jsonify({'message': 'Template saved successfully'}), 200

@app.route('/templates', methods=['GET'])
def get_templates():
    templates = [f.split('.')[0] for f in os.listdir(app.config['TEMPLATE_FOLDER']) if f.endswith('.json')]
    return jsonify(templates), 200

@app.route('/templates/<name>', methods=['GET'])
def get_template(name):
    template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{name}.json')
    if os.path.exists(template_path):
        with open(template_path, 'r') as f:
            template = json.load(f)
        return jsonify(template), 200
    return jsonify({'message': 'Template not found'}), 404

def extract_value(text, keyword, separator, index):
    lines = text.split('\n')
    for line in lines:
        if keyword in line:
            parts = line.split(separator)
            if len(parts) > index:
                return parts[index].strip()
    return ''

@app.route('/extract', methods=['POST'])
def extract_data():
    data = request.json
    if 'filename' not in data or 'template' not in data:
        return jsonify({'message': 'Filename and template are required'}), 400

    filename = data['filename']
    template_name = data['template']
    output_format = data.get('output_format', 'json')

    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{template_name}.json')

    if not os.path.exists(pdf_path):
        return jsonify({'message': 'File not found'}), 404
    if not os.path.exists(template_path):
        return jsonify({'message': 'Template not found'}), 404

    with open(template_path, 'r') as f:
        template = json.load(f)

    pages = convert_from_path(pdf_path, 300)
    extracted_data = {}
    original_lines = []

    for page_number, page_data in enumerate(pages):
        image_path = f"page_{page_number}.jpg"
        page_data.save(image_path, 'JPEG')

        page_text = pytesseract.image_to_string(image_path)
        os.remove(image_path)

        original_lines.extend(page_text.split('\n'))

        for field in template['fields']:
            name = field['name']
            keyword = field['keyword']
            separator = field.get('separator', ':')
            index = field.get('index', 1)
            value = extract_value(page_text, keyword, separator, index)
            extracted_data[name] = value

    if output_format == 'json':
        return jsonify({'extracted_data': extracted_data, 'lines_data': original_lines}), 200
    elif output_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(extracted_data.keys())
        writer.writerow(extracted_data.values())
        return output.getvalue(), 200, {'Content-Type': 'text/csv'}
    elif output_format == 'text':
        output = "\n".join([f"{key}: {value}" for key, value in extracted_data.items()])
        return output, 200, {'Content-Type': 'text/plain'}
    else:
        return jsonify({'message': 'Unsupported output format'}), 400

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
