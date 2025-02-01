from werkzeug.utils import secure_filename
from modules.services.azure_blob_service import AzureBlobService
from flask import current_app
from modules.logging_util import setup_logger
from modules.models.file_processing import FileProcessing
from extensions import db
from datetime import datetime
import os

logger = setup_logger(__name__)

def validate_files(files):
    """
    Validate file types before upload.
    """
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    invalid_files = [file.filename for file in files if not allowed_file(file.filename, allowed_extensions)]
    return invalid_files

def allowed_file(filename, allowed_extensions):
    """
    Check if the file extension is allowed.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file_record(user_id, filename):
    """
    Save file upload record to the database before uploading to Azure.
    """
    file_record = FileProcessing(
        user_id=user_id,
        file_name=filename,
        status="Pending",
        created_at=datetime.utcnow()
    )
    db.session.add(file_record)
    db.session.commit()
    return file_record.id

def upload_file_to_azure(user_id, file_id):
    """
    Upload a file to Azure Blob Storage with error handling.
    """
    blob_service = current_app.config['AZURE_BLOB_SERVICE']
    file_record = FileProcessing.query.get(file_id)

    if not file_record:
        logger.error(f"File ID {file_id} not found in database.")
        return {"error": "File record not found"}, 400

    try:
        logger.info(f"Starting upload for {file_record.file_name} (File ID: {file_id}) by user {user_id}...")

        # Upload file
        blob_service.upload_file(user_id, file_record.file_name, "user_upload")

        # Update DB
        file_record.status = "Completed"
        file_record.completed_at = datetime.utcnow()
        db.session.commit()

        logger.info(f"Upload successful for {file_record.file_name} (File ID: {file_id}) by user {user_id}.")
        return {"message": "Upload successful", "file_name": file_record.file_name}

    except FileNotFoundError:
        logger.error(f"File {file_record.file_name} not found for upload by user {user_id}.")
        file_record.status = "Failed"
        file_record.error_message = "File not found"
        db.session.commit()
        return {"error": "File not found"}, 400

    except ConnectionError:
        logger.error(f"Connection issue while uploading {file_record.file_name} (File ID: {file_id}) for user {user_id}. Retrying...")
        return {"error": "Connection error, retrying..."}, 500

    except Exception as e:
        logger.exception(f"Unexpected error during upload of {file_record.file_name} (File ID: {file_id}) for user {user_id}: {str(e)}")
        file_record.status = "Failed"
        file_record.error_message = str(e)
        db.session.commit()
        return {"error": f"Unexpected error: {str(e)}"}, 500
