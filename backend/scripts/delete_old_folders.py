import os
import sys
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ✅ FIX: Explicitly add the `/app/` directory to `sys.path`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.services.azure_blob_service import AzureBlobService

# Load .env file
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(env_path)

# Read Azure credentials
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER")

print(f"Azure Storage Connection String: {AZURE_STORAGE_CONNECTION_STRING}")
print(f"Azure Storage Container Name: {CONTAINER_NAME}")

# Initialize Azure Blob Service
try:
    blob_service = AzureBlobService(AZURE_STORAGE_CONNECTION_STRING, CONTAINER_NAME)
    print("✅ Successfully connected to Azure Blob Storage.")
except Exception as e:
    print(f"❌ Failed to initialize AzureBlobService: {e}")
    sys.exit(1)

# Run the function to delete folders older than 2 days
try:
    print("🗑️ Attempting to delete old folders...")
    blob_service.delete_old_folders(days_threshold=2)
    print("✅ Old folders deleted successfully.")
except Exception as e:
    print(f"❌ Error deleting old folders: {e}")
