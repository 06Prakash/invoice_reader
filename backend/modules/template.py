from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import json
from .models import db, User
import logging


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# File handler for logging
file_handler = logging.FileHandler('/app/logs/app.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def register_template_routes(app):
    """
    Register routes for managing templates.
    """

    @app.route('/templates', methods=['POST'])
    @jwt_required()
    def save_template():
        """
        Save a new template or update an existing template.
        """
        try:
            current_user = get_jwt_identity()
            logger.info(f"Saving template for user: {current_user}")

            data = request.json
            template_name = data.get('name')
            if not template_name:
                logger.error("Template name is missing in the request")
                return jsonify({'message': 'Template name is required'}), 400

            if template_name == "Default Template":
                logger.warning("Attempt to overwrite default template")
                return jsonify({'message': 'Cannot overwrite default template'}), 400

            user = User.query.filter_by(username=current_user).first()
            if not user:
                logger.error("User not found")
                return jsonify({'message': 'User not found'}), 404

            if user.company:
                template_name = f"{user.company.name}_{template_name}"
            else:
                logger.error("User has no associated company")
                return jsonify({'message': 'Company name is required to save templates'}), 400

            template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{template_name}.json')
            os.makedirs(app.config['TEMPLATE_FOLDER'], exist_ok=True)

            with open(template_path, 'w') as f:
                json.dump(data, f)

            logger.info(f"Template saved successfully: {template_name}")
            return jsonify({'message': 'Template saved successfully', 'generatedTemplateName': template_name}), 200
        except Exception as e:
            logger.error(f"Error saving template: {e}")
            return jsonify({'message': 'Error saving template'}), 500

    @app.route('/templates', methods=['GET'])
    @jwt_required()
    def get_templates():
        """
        Retrieve the list of templates available for the current user's company.
        """
        try:
            current_user = get_jwt_identity()
            logger.info(f"Fetching templates for user: {current_user}")

            user = User.query.filter_by(username=current_user).first()
            if not user:
                logger.error("User not found")
                return jsonify({'message': 'User not found'}), 404

            templates = ["Default Template"]
            if user.company:
                try:
                    template_folder = app.config['TEMPLATE_FOLDER']
                    company_templates = [
                        f.split('.')[0]
                        for f in os.listdir(template_folder)
                        if f.startswith(user.company.name) and f.endswith('.json')
                    ]
                    templates.extend(company_templates)
                except Exception as e:
                    logger.error(f"Error accessing TEMPLATE_FOLDER: {e}")
                    return jsonify({'message': 'Error accessing templates'}), 500
            else:
                logger.warning("User has no associated company")
                return jsonify({'message': 'User has no associated company'}), 400

            logger.info(f"Templates retrieved: {templates}")
            return jsonify(templates), 200
        except Exception as e:
            logger.error(f"Error retrieving templates: {e}")
            return jsonify({'message': 'Error retrieving templates'}), 500

    @app.route('/default_template', methods=['GET'])
    def get_default_template():
        """
        Retrieve the default template.
        """
        try:
            template_path = os.path.join('resources', 'json_templates', 'default_template.json')
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    template = json.load(f)
                logger.info("Default template retrieved successfully")
                return jsonify(template), 200
            logger.warning("Default template not found")
            return jsonify({'message': 'Default template not found'}), 404
        except Exception as e:
            logger.error(f"Error retrieving default template: {e}")
            return jsonify({'message': 'Error retrieving default template'}), 500

    @app.route('/templates/<name>', methods=['GET'])
    @jwt_required()
    def get_template(name):
        """
        Retrieve a specific template by name for the current user's company.
        """
        try:
            current_user = get_jwt_identity()
            logger.info(f"Fetching template '{name}' for user: {current_user}")

            user = User.query.filter_by(username=current_user).first()
            if not user:
                logger.error("User not found")
                return jsonify({'message': 'User not found'}), 404

            if name == "default":
                template_path = os.path.join('resources', 'json_templates', 'default_template.json')
            else:
                if user.company and not name.startswith(user.company.name):
                    name = f"{user.company.name}_{name}"
                template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{name}.json')

            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    template = json.load(f)
                logger.info(f"Template '{name}' retrieved successfully")
                return jsonify(template), 200

            logger.warning(f"Template '{name}' not found")
            return jsonify({'message': 'Template not found'}), 404
        except Exception as e:
            logger.error(f"Error retrieving template '{name}': {e}")
            return jsonify({'message': 'Error retrieving template'}), 500
