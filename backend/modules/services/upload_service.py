from werkzeug.utils import secure_filename
from modules.services.azure_blob_service import AzureBlobService
from flask import current_app
import os
from modules.logging_util import setup_logger

logger = setup_logger(__name__)

def allowed_file(filename):
    """
    Check if the file extension is allowed.
    """
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def upload_files(user_id, files, filename=None, chunk_index=None, total_chunks=None):
    """
    Handle large file uploads by processing chunks and return filenames after the last chunk.
    """
    blob_service = current_app.config['AZURE_BLOB_SERVICE']
    
    try:
        uploaded_files = []
        upload_folder = f"uploads/{user_id}"
        os.makedirs(upload_folder, exist_ok=True)

        for file in files:
            fname = filename if filename else secure_filename(file.filename)
            file_path = os.path.join(upload_folder, fname)

            # Append chunk if it's a chunked upload
            with open(file_path, 'ab') as f:
                f.write(file.read())

            # If this is the last chunk, upload the final file and return only the filename
            if chunk_index is not None and (chunk_index + 1) == total_chunks:
                uploaded_file_url = blob_service.upload_file(user_id, file_path)
                
                # ✅ Fix: Extract last part of the path correctly
                if isinstance(uploaded_file_url, list):
                    uploaded_file_url = uploaded_file_url[0]  # Convert list to string
                
                filename_only = os.path.basename(uploaded_file_url)  # Get only the filename
                uploaded_files.append(filename_only)

                logger.info(f"Uploaded File Name: {filename_only}") 

        if uploaded_files:
            return {'message': 'Files uploaded successfully', 'filenames': uploaded_files}, 200
        else:
            return {'message': 'Chunk uploaded successfully'}, 200

    except Exception as e:
        return {'error': f'File upload failed: {str(e)}'}, 500
