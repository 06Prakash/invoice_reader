from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from modules.services.upload_service import upload_files
from modules.services.background_service.upload_worker import process_upload  # Celery Task
from modules.logging_util import setup_logger

logger = setup_logger(__name__)

def register_upload_routes(app):
    @app.route('/upload', methods=['POST'])
    @jwt_required()
    def upload_file():
        """
        API endpoint to handle file uploads asynchronously.
        """
        user_id = get_jwt_identity()

        if 'files' not in request.files:
            return jsonify({'message': 'No files found in the request'}), 400

        files = request.files.getlist('files')

        # Start a Celery task to process uploads in the background
        task = process_upload.delay(user_id, [file.filename for file in files])
        
        return jsonify({'message': 'Upload in progress', 'task_id': task.id}), 202

    @app.route('/upload_chunk', methods=['POST'])
    @jwt_required()
    def upload_chunk():
        """
        API endpoint for chunked uploads to avoid timeouts.
        """
        user_id = get_jwt_identity()
        chunk = request.files['file']
        filename = request.form['filename']
        chunk_index = int(request.form['chunkIndex'])
        total_chunks = int(request.form['totalChunks'])
        logger.info(f"Received chunk {chunk_index + 1}/{total_chunks} for {filename}")

        response, status = upload_files(user_id, [chunk], filename, chunk_index, total_chunks)
        return jsonify(response), status
