import os
import sys
from celery import Celery
from flask import Flask
from extensions import db
from modules.models.file_processing import FileProcessing
from datetime import datetime
from modules.services.upload_service import upload_file_to_azure

# Ensure the app module path is correctly added for Celery to find models & services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# Initialize Flask app
def create_flask_app():
    app = Flask(__name__)
    app.config.from_object("config")
    db.init_app(app)
    return app

flask_app = create_flask_app()

# Configure Celery
CELERY_BROKER_URL = os.getenv("AZURE_STORAGE_QUEUE_URL") if os.getenv("FLASK_ENV") == "production" else "redis://redis:6379/0"
CELERY_RESULT_BACKEND = None if os.getenv("FLASK_ENV") == "production" else "redis://redis:6379/0"

celery_app = Celery("tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery_app.conf.update(flask_app.config)

@celery_app.task(bind=True)
def upload_file_task(self, user_id, file_id):
    """
    Background task to upload a file to Azure Blob Storage.
    Ensures database access is available within Celery.
    """
    with flask_app.app_context():
        file_record = db.session.get(FileProcessing, file_id)  # SQLAlchemy 2.0+
        
        if not file_record:
            return {"error": f"File ID {file_id} not found"}

        # Update file status
        file_record.status = "Uploading"
        db.session.commit()

        try:
            result = upload_file_to_azure(user_id, file_id)
            return result
        except Exception as e:
            db.session.rollback()  # Ensure DB rollback on failure
            file_record.status = "Failed"
            file_record.error_message = str(e)
            db.session.commit()
            return {"error": str(e)}
