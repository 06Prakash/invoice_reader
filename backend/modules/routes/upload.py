from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from modules.models.file_processing import FileProcessing
from modules.models.extraction_attempt import ExtractionAttempt
from extensions import db
from modules.services.upload_service import validate_files
from modules.services.background_service.celery_worker import upload_file_task
from datetime import datetime

def register_upload_routes(app):
    @app.route('/upload', methods=['POST'])
    @jwt_required()
    def upload_file():
        """
        API endpoint to handle file uploads asynchronously with Celery.
        """
        user_id = get_jwt_identity()

        if 'files' not in request.files:
            return jsonify({'message': 'No files in request'}), 400

        files = request.files.getlist('files')

        # Validate files
        invalid_files = validate_files(files)
        if invalid_files:
            return jsonify({'error': f"File type not allowed: {', '.join(invalid_files)}"}), 400

        try:
            # Determine the attempt number
            last_attempt = (
                ExtractionAttempt.query.filter_by(user_id=user_id)
                .order_by(ExtractionAttempt.created_at.desc())
                .first()
            )
            attempt_number = (last_attempt.attempt_number + 1) if last_attempt else 1

            # Step 1: Create Extraction Attempt
            extraction_attempt = ExtractionAttempt(
                user_id=user_id,
                attempt_number=attempt_number,
                total_files=len(files),
                status="Pending",
                created_at=datetime.utcnow(),
            )
            db.session.add(extraction_attempt)
            db.session.flush()  # Get `extraction_attempt.id` before committing

            uploaded_files = []
            file_records = []

            for file in files:
                filename = file.filename

                # Step 2: Register each file in `FileProcessing`
                file_record = FileProcessing(
                    extraction_attempt_id=extraction_attempt.id,
                    user_id=user_id,
                    file_name=filename,
                    status="Pending",
                    created_at=datetime.utcnow(),
                )
                file_records.append(file_record)

            # Bulk insert all file records in one commit
            db.session.add_all(file_records)
            db.session.commit()  # One transaction instead of multiple

            # Step 3: Trigger Background Upload Tasks
            for file_record in file_records:
                upload_file_task.delay(user_id, file_record.id)

                uploaded_files.append({
                    "file_id": file_record.id,
                    "file_name": file_record.file_name,
                    "attempt_id": extraction_attempt.id,
                    "status": "Pending"
                })

            return jsonify({'message': 'Upload started', 'files': uploaded_files, 'attempt_id': extraction_attempt.id}), 200
        
        except Exception as e:
            db.session.rollback()  # Rollback if anything goes wrong
            return jsonify({'error': str(e)}), 500
