from werkzeug.utils import secure_filename
from modules.services.azure_blob_service import AzureBlobService
from flask import current_app
import os
from modules.logging_util import setup_logger
import asyncio
import aiofiles

logger = setup_logger(__name__)

def allowed_file(filename):
    """
    Check if the file extension is allowed.
    """
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

async def write_chunk_async(file_path, data):
    """
    Asynchronously write a file chunk to disk.
    """
    async with aiofiles.open(file_path, 'ab') as f:
        await f.write(data)

async def upload_to_blob(blob_service, user_id, file_path):
    """
    Upload file asynchronously to Azure Blob Storage.
    """
    blob_name = blob_service.generate_blob_name(user_id, os.path.basename(file_path), 'user_upload')
    blob_client = blob_service.container_client.get_blob_client(blob_name)

    try:
        async with aiofiles.open(file_path, 'rb') as data:
            file_content = await data.read()
        
        blob_client.upload_blob(file_content, overwrite=True)

        logger.info(f"File uploaded to Azure Blob: {blob_name}")
        return blob_name
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise

def upload_files(user_id, files, filename=None, chunk_index=None, total_chunks=None):
    """
    Handle large file uploads by processing chunks and return filenames after the last chunk.
    """
    # Access Azure Blob Service from Flask config
    blob_service = current_app.config['AZURE_BLOB_SERVICE']

    # Logging for Azure Form Recognizer details
    azure_endpoint = current_app.config.get('AZURE_ENDPOINT')
    azure_key = current_app.config.get('AZURE_KEY')
    logger.info(f"Azure Endpoint: {azure_endpoint}")
    logger.info(f"Azure Key: {azure_key}")

    try:
        uploaded_files = []
        upload_folder = f"uploads/{user_id}"
        os.makedirs(upload_folder, exist_ok=True)

        for file in files:
            fname = filename if filename else secure_filename(file.filename)
            file_path = os.path.join(upload_folder, fname)

            # Read file in non-blocking mode and write asynchronously
            file_content = file.stream.read()  # Using stream to read efficiently
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(write_chunk_async(file_path, file_content))

            # Upload to Azure Blob Storage when the last chunk is received
            if chunk_index is not None and (chunk_index + 1) == total_chunks:
                uploaded_file_url = loop.run_until_complete(upload_to_blob(blob_service, user_id, file_path))

                filename_only = os.path.basename(uploaded_file_url)
                uploaded_files.append(filename_only)
                logger.info(f"Uploaded File Name: {filename_only}") 

        if uploaded_files:
            return {'message': 'Files uploaded successfully', 'filenames': uploaded_files}, 200
        else:
            return {'message': 'Chunk uploaded successfully'}, 200

    except Exception as e:
        logger.error(f"File upload failed: {e}")
        return {'error': f'File upload failed: {str(e)}'}, 500
