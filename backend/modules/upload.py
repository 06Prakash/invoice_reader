from flask import request, jsonify
from werkzeug.utils import secure_filename
import os

def register_upload_routes(app):
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    @app.route('/upload', methods=['POST'])
    def upload_file():
        if 'files' not in request.files:
            return jsonify({'message': 'No files part'}), 400
        files = request.files.getlist('files')
        filenames = []
        for file in files:
            if file.filename == '':
                return jsonify({'message': 'No selected file'}), 400
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                filenames.append(filename)
        return jsonify({'filenames': filenames}), 200
