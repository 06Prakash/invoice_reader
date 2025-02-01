import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from modules.services.azure_blob_service import AzureBlobService
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
OUTPUT_FOLDER = 'uploads' # we can change this later

SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key')
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///site.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default_jwt_secret_key')
SQLALCHEMY_POOL_SIZE = 20  # Increase pool size
SQLALCHEMY_MAX_OVERFLOW = 10
SQLALCHEMY_POOL_TIMEOUT = 30
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
MAIL_SERVER = 'smtp.zoho.com'  # SMTP server for Zoho
MAIL_PORT = 587               # TLS port
MAIL_USE_TLS = True           # Enable TLS
MAIL_USE_SSL = False          # Do not use SSL
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_USERNAME')  # Default sender address
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'False').lower() in ['true', '1', 'yes']  # Convert to boolean
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() in ['true', '1', 'yes']  # Convert to boolean
MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_PORT = os.getenv('MAIL_PORT')
AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER")
ALLOWED_EXTENSIONS = {'pdf'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Key Vault Configuration
KEY_VAULT_URL = os.getenv("KEY_VAULT_URL")
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)

# Azure Configuration
AZURE_ENDPOINT = secret_client.get_secret("azure-form-recognizer-endpoint").value
AZURE_KEY = secret_client.get_secret("azure-form-recognizer-key").value
AZURE_BLOB_SERVICE = AzureBlobService(AZURE_STORAGE_CONNECTION_STRING, AZURE_STORAGE_CONTAINER)

# Model Mappings
MODEL_MAPPING = {
    "NIRA AI - handwritten": "MutualFundModelSundaramFinance",
    "NIRA AI - Invoice": "prebuilt-invoice",
    "NIRA AI - Printed Text": "prebuilt-read",
    "NIRA AI - Printed Tables": "prebuilt-layout",
    "NIRA AI - Printed business card": "prebuilt-businessCard",
    "NIRA AI - Printed receipt": "prebuilt-receipt",
}