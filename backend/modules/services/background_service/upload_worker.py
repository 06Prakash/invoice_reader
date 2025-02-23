import os
import ssl
from celery import Celery
from modules.logging_util import setup_logger
from flask import Flask, current_app
from modules.services.upload_service import upload_files

# Use container name as hostname
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://invoice_reader_redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://invoice_reader_redis:6379/1")
logger = setup_logger(__name__)
celery_app = Celery("tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

if os.getenv("FLASK_ENV") != "development":
    broker_transport_options = {"visibility_timeout": 3600}
    if CELERY_BROKER_URL.startswith("rediss://") or CELERY_RESULT_BACKEND.startswith("rediss://"):
        ssl_config = {"ssl_cert_reqs": ssl.CERT_REQUIRED}
        celery_app.conf.update(
            broker_use_ssl=ssl_config,
            redis_backend_use_ssl=ssl_config,
            broker_transport_options=broker_transport_options
        )
    else:
        celery_app.conf.update(broker_transport_options=broker_transport_options)
else:
    celery_app.conf.update(
        broker_use_ssl=False,
        redis_backend_use_ssl=False,
        broker_transport_options={"visibility_timeout": 3600}
    )

@celery_app.task(bind=True)
def process_upload(self, user_id, filenames):
    """
    Celery background task to process file uploads.
    """
    try:
        from app import create_app
        flask_app = create_app()
        
        with flask_app.app_context():
            # Access Azure configuration values from Flask app context
            endpoint = current_app.config['AZURE_ENDPOINT']
            key = current_app.config['AZURE_KEY']
            
            logger.info(f"Using Azure Endpoint: {endpoint}")
            logger.info(f"Using Azure Key: {key}")
            
            # Call the upload_files function
            response, status = upload_files(user_id, filenames)
        
        return {'status': 'completed', 'filenames': response['filenames']}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}
