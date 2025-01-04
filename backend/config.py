import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

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

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Key Vault Configuration
KEY_VAULT_URL = os.getenv("KEY_VAULT_URL")
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)

# Azure Configuration
AZURE_ENDPOINT = secret_client.get_secret("azure-form-recognizer-endpoint").value
AZURE_KEY = secret_client.get_secret("azure-form-recognizer-key").value

# Model Mappings
MODEL_MAPPING = {
    "NIRA AI - handwritten": "MutualFundModelSundaramFinance",
    "NIRA AI - Invoice": "prebuilt-invoice",
    "NIRA AI - Printed Text": "prebuilt-read",
    "NIRA AI - Printed Tables": "prebuilt-layout",
    "NIRA AI - Printed business card": "prebuilt-businessCard",
    "NIRA AI - Printed receipt": "prebuilt-receipt",
}