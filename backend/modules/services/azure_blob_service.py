from azure.storage.blob import BlobServiceClient
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os
from datetime import datetime
from modules.logging_util import setup_logger
import tempfile
from PyPDF2 import PdfReader

logger = setup_logger(__name__)


class AzureBlobService:
    def __init__(self, connection_string, container_name):
        """
        Initialize the AzureBlobService with a connection string and container name.
        """
        logger.info("Initializing AzureBlobService...")
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_name = container_name
        self.container_client = self.blob_service_client.get_container_client(container_name)
        logger.info(f"AzureBlobService initialized with container: {container_name}")

    def _get_date_folder(self):
        """
        Returns the current date folder in 'dd_mm_yyyy' format.
        """
        return datetime.now().strftime('%d_%m_%Y')

    def upload_file(self, user_id, local_file_path, folder_type='user_upload', destination_filename=None):
        """
        Upload a single file to Azure Blob Storage.
        Delegates to `upload_files` if a list of files is provided.
        :param user_id: User ID to organize files in their specific folder.
        :param local_file_path: Local file path or list of file paths to upload.
        :param folder_type: Subfolder type ('user_upload' or 'user_extract').
        :param destination_filename: Optional custom name for the uploaded file.
        :return: List of blob names of the uploaded files.
        """
        if isinstance(local_file_path, list):
            logger.info("Multiple files detected for upload. Delegating to `upload_files`...")
            return self.upload_files(user_id, local_file_path, folder_type)

        if not os.path.exists(local_file_path):
            logger.warning(f"File not found: {local_file_path}")
            raise FileNotFoundError(f"Local file {local_file_path} does not exist.")

        date_folder = self._get_date_folder()
        filename = destination_filename or os.path.basename(local_file_path)
        blob_name = f"uploads/{date_folder}/{user_id}/{folder_type}/{filename}"
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            with open(local_file_path, 'rb') as data:
                blob_client.upload_blob(data, overwrite=True)
            logger.info(f"Uploaded file {local_file_path} to {blob_name}")
        except Exception as e:
            logger.error(f"Failed to upload file {local_file_path}: {e}")
            raise
        return [blob_name]

    def upload_files(self, user_id, files, folder_type='user_upload'):
        """
        Upload multiple files to Azure Blob Storage.
        Handles both FileStorage objects and local file paths efficiently.
        
        :param user_id: User ID to organize files in their specific folder.
        :param files: List of file paths or FileStorage objects to upload.
        :param folder_type: Subfolder type ('user_upload' or 'user_extract').
        :return: List of blob names of the uploaded files.
        """
        logger.info(f"Received files for upload: {files}")
        date_folder = self._get_date_folder()
        blob_names = []

        for file_obj in files:
            temp_file_path = None  # Initialize temporary file path
            try:
                # Check if the file is a FileStorage object
                if isinstance(file_obj, FileStorage):
                    # Save FileStorage object to a temporary file
                    temp_file_path = os.path.join(tempfile.gettempdir(), secure_filename(file_obj.filename))
                    file_obj.save(temp_file_path)
                    local_file_path = temp_file_path
                    logger.info(f"Saved FileStorage object to temporary path: {local_file_path}")
                elif isinstance(file_obj, str) and os.path.exists(file_obj):
                    # If it's a valid local file path, use it directly
                    local_file_path = file_obj
                    logger.info(f"Using local file path: {local_file_path}")
                else:
                    logger.warning(f"Invalid file object: {file_obj}")
                    continue

                # Prepare blob name and upload file
                filename = os.path.basename(local_file_path)
                blob_name = f"uploads/{date_folder}/{user_id}/{folder_type}/{filename}"
                blob_client = self.container_client.get_blob_client(blob_name)
                with open(local_file_path, 'rb') as data:
                    blob_client.upload_blob(data, overwrite=True)
                blob_names.append(blob_name)
                logger.info(f"Uploaded file {local_file_path} to blob: {blob_name}")
            except Exception as e:
                logger.error(f"Failed to upload file {file_obj}: {e}")
            finally:
                # Clean up temporary file if it was created
                if temp_file_path and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    logger.info(f"Temporary file {temp_file_path} deleted.")

        if not blob_names:
            logger.warning("No files were successfully uploaded.")
            raise ValueError("No files were successfully uploaded.")

        return blob_names


    def list_files(self, user_id, folder_type='user_upload', date_folder=None):
        """
        List all files for a specific user in a specified folder type.
        :param user_id: User ID whose files need to be listed.
        :param folder_type: Subfolder type ('user_upload' or 'user_extract').
        :param date_folder: If you want to list a particular date related content we can use this. But for now it has no use.
        :return: List of blob names.
        """
        if date_folder == None:
            date_folder = self._get_date_folder()
        prefix = f"uploads/{date_folder}/{user_id}/{folder_type}/"
        logger.info(f"Listing files for user {user_id} in folder {prefix}...")
        try:
            files = [blob.name for blob in self.container_client.list_blobs(name_starts_with=prefix)]
            logger.info(f"Found {len(files)} files for user {user_id} in folder {prefix}.")
        except Exception as e:
            logger.error(f"Failed to list files for user {user_id} in folder {prefix}: {e}")
            raise
        return files

    def download_file(self, user_id, filename, folder_type='user_upload'):
        """
        Download a specific file for a user.
        :param user_id: User ID whose file needs to be downloaded.
        :param filename: Name of the file to download.
        :param folder_type: Subfolder type ('user_upload' or 'user_extract').
        :return: File content as bytes.
        """
        date_folder = self._get_date_folder()
        blob_name = filename
        logger.info(f"Inside download file function {user_id} => {filename}")
        if folder_type not in blob_name:
            blob_name = f"uploads/{date_folder}/{user_id}/{folder_type}/{filename}"
        logger.info(f"Downloading file {blob_name} for user {user_id}...")
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            content = blob_client.download_blob().readall()
            logger.info(f"Downloaded file {blob_name} for user {user_id}.")
            return content
        except Exception as e:
            logger.error(f"Failed to download file {blob_name}: {e}")
            raise

    def delete_file(self, user_id, filename, folder_type='user_upload'):
        """
        Delete a specific file for a user.
        :param user_id: User ID whose file needs to be deleted.
        :param filename: Name of the file to delete.
        :param folder_type: Subfolder type ('user_upload' or 'user_extract').
        :return: None.
        """
        date_folder = self._get_date_folder()
        blob_name = f"uploads/{date_folder}/{user_id}/{folder_type}/{filename}"
        logger.info(f"Deleting file {blob_name} for user {user_id}...")
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            logger.info(f"Deleted file {blob_name} for user {user_id}.")
        except Exception as e:
            logger.error(f"Failed to delete file {blob_name}: {e}")
            raise

    def create_user_folder(self, user_id):
        """
        Create a folder structure for a new user by uploading dummy blobs to `user_upload` and `user_extract`.
        :param user_id: User ID whose folder structure needs to be created.
        :return: None.
        """
        date_folder = self._get_date_folder()
        logger.info(f"Creating folder structure for user {user_id} for date {date_folder}...")
        try:
            for folder_type in ['user_upload', 'user_extract']:
                blob_name = f"uploads/{date_folder}/{user_id}/{folder_type}/.placeholder"
                blob_client = self.container_client.get_blob_client(blob_name)
                blob_client.upload_blob(b'', overwrite=True)  # Empty content for placeholder
                logger.info(f"Created folder {folder_type} for user {user_id} under {date_folder}.")
        except Exception as e:
            logger.error(f"Failed to create folder structure for user {user_id}: {e}")
            raise

    def delete_user_folder(self, user_id):
        """
        Delete all files and folders associated with a user for the current date.
        :param user_id: User ID whose folder needs to be deleted.
        :return: None.
        """
        date_folder = self._get_date_folder()
        prefix = f"uploads/{date_folder}/{user_id}/"
        logger.info(f"Deleting folder structure for user {user_id} for date {date_folder}...")
        try:
            blobs_to_delete = [blob.name for blob in self.container_client.list_blobs(name_starts_with=prefix)]
            for blob_name in blobs_to_delete:
                blob_client = self.container_client.get_blob_client(blob_name)
                blob_client.delete_blob()
                logger.info(f"Deleted blob {blob_name}.")
            logger.info(f"Successfully deleted all files for user {user_id} under {date_folder}.")
        except Exception as e:
            logger.error(f"Failed to delete folder structure for user {user_id}: {e}")
            raise
    
    def generate_blob_name(self, user_id, blob_name, folder_type):
        date_folder = self._get_date_folder()
        return f"uploads/{date_folder}/{user_id}/{folder_type}/{blob_name}"

    def get_total_pages_from_azure(self, blob_name):
        """
        Calculates the total number of pages in a PDF stored in Azure Blob Storage.
        :param connection_string: Azure Storage connection string.
        :param container_name: The name of the Azure Blob Storage container.
        :param blob_name: The name of the blob (PDF file).
        :return: Total number of pages in the PDF.
        """
        blob_client = self.container_client.get_blob_client(blob_name)

        try:
            # Download the first chunk of the file (enough for metadata extraction)
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                blob_data = blob_client.download_blob()
                temp_file.write(blob_data.readall())
                temp_file_path = temp_file.name

            # Use PyPDF2 to calculate the total number of pages
            reader = PdfReader(temp_file_path)
            total_pages = len(reader.pages)
            logger.info(f"Total pages in {blob_name}: {total_pages}")
        except Exception as e:
            logger.error(f"Error calculating total pages for {blob_name}: {e}")
            raise
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)  # Clean up temporary file

        return total_pages