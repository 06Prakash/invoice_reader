# backend\modules\services\upload_service,py
from werkzeug.utils import secure_filename
from modules.services.azure_blob_service import AzureBlobService
from flask import current_app
from modules.logging_util import setup_logger

logger = setup_logger(__name__)


def allowed_file(filename):
    """
    Check if the file extension is allowed.
    """
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def upload_files(user_id, files):
    """
    Upload multiple files for a user.
    :param user_id: ID of the user uploading the files.
    :param files: List of files from the request.
    :return: List of uploaded file paths (blob names).
    """
    # Validate files
    if not files or any(file.filename == '' for file in files):
        return {'error': 'No selected files'}, 400

    invalid_files = [file.filename for file in files if not allowed_file(file.filename)]
    if invalid_files:
        return {'error': f"File type not allowed: {', '.join(invalid_files)}"}, 400

    # Initialize AzureBlobService
    connection_string = current_app.config['AZURE_STORAGE_CONNECTION_STRING']
    container_name = current_app.config['AZURE_STORAGE_CONTAINER']
    blob_service = AzureBlobService(connection_string, container_name)

    try:
        # Upload files to Azure Blob Storage
        uploaded_files = blob_service.upload_files(user_id, files)
        return {'message': 'Files uploaded successfully', 'filenames': uploaded_files}, 200
    except Exception as e:
        return {'error': f'File upload failed: {str(e)}'}, 500
