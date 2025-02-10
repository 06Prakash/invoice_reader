from celery import Celery
from modules.services.upload_service import upload_files
import os
import ssl
# Use Upstash Redis with SSL
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

celery_app = Celery("tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

celery_app.conf.update(
    broker_use_ssl={
        "ssl_cert_reqs": ssl.CERT_REQUIRED,  # Change to CERT_OPTIONAL or CERT_NONE if needed
    },
    redis_backend_use_ssl={
        "ssl_cert_reqs": ssl.CERT_REQUIRED
    },
    broker_transport_options={
        "visibility_timeout": 3600  # Optional timeout
    }
)


@celery_app.task(bind=True)
def process_upload(self, user_id, filenames):
    """
    Celery background task to process file uploads.
    """
    try:
        response, status = upload_files(user_id, filenames)
        return {'status': 'completed', 'filenames': response['filenames']}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}