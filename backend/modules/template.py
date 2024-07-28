from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import json
import time
from .models import db, User

def register_template_routes(app):
    @app.route('/templates', methods=['POST'])
    @jwt_required()
    def save_template():
        """
        Save a new template or update an existing template.
        """
        current_user = get_jwt_identity()
        data = request.json
        template_name = data['name']
        
        if template_name == "Default Template":
            return jsonify({'message': 'Cannot overwrite default template'}), 400
        
        user = User.query.filter_by(username=current_user['username']).first()
        if user.company:
            template_name = f"{user.company.name}_{template_name}"
        else:
            return jsonify({'message': 'Company name is required to save templates'}), 400

        template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{template_name}.json')
        with open(template_path, 'w') as f:
            json.dump(data, f)
        
        return jsonify({'message': 'Template saved successfully', 'generatedTemplateName': template_name}), 200

    @app.route('/templates', methods=['GET'])
    @jwt_required()
    def get_templates():
        """
        Retrieve the list of templates available for the current user's company.
        """
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user['username']).first()
        
        templates = ["Default Template"]
        if user.company:
            company_templates = [f.split('.')[0] for f in os.listdir(app.config['TEMPLATE_FOLDER']) if f.startswith(user.company.name) and f.endswith('.json')]
            templates.extend(company_templates)
        
        return jsonify(templates), 200

    @app.route('/default_template', methods=['GET'])
    def get_default_template():
        """
        Retrieve the default template.
        """
        template_path = os.path.join('resources', 'json_templates', 'default_template.json')
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                template = json.load(f)
            return jsonify(template), 200
        return jsonify({'message': 'Default template not found'}), 404

    @app.route('/templates/<name>', methods=['GET'])
    @jwt_required()
    def get_template(name):
        """
        Retrieve a specific template by name for the current user's company.
        """
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user['username']).first()
        
        if name == "default":
            template_path = os.path.join('resources', 'json_templates', 'default_template.json')
        else:
            if user.company and not name.startswith(user.company.name):
                name = f"{user.company.name}_{name}"
            template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{name}.json')

        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                template = json.load(f)
            return jsonify(template), 200
        return jsonify({'message': 'Template not found'}), 404
