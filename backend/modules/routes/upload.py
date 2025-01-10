from flask import request, jsonify
from werkzeug.utils import secure_filename
import os
from flask_jwt_extended import jwt_required, get_jwt_identity


def register_upload_routes(app):
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    @app.route('/upload', methods=['POST'])
    @jwt_required()
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
