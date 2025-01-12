from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from modules.services.upload_service import upload_files

def register_upload_routes(app):
    @app.route('/upload', methods=['POST'])
    @jwt_required()
    def upload_file():
        """
        API endpoint to handle file uploads.
        """
        # Get the current user ID from JWT token
        user_id = get_jwt_identity()

        if 'files' not in request.files:
            return jsonify({'message': 'No files part in the request'}), 400

        files = request.files.getlist('files')

        # Call the service to handle the upload
        response, status = upload_files(user_id, files)
        local_files_array = []
        for file in response['filenames']:
            local_files_array.append(file.split("/")[-1])
        response['filenames'] = local_files_array
        return jsonify(response), status
