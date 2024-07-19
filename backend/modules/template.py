from flask import request, jsonify
import os
import json

def register_template_routes(app):
    @app.route('/templates', methods=['POST'])
    def save_template():
        data = request.json
        template_name = data['name']
        if template_name == "Default Template":
            template_name = 'default_template'
        template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{template_name}.json')
        with open(template_path, 'w') as f:
            json.dump(data, f)
        return jsonify({'message': 'Template saved successfully'}), 200

    @app.route('/templates', methods=['GET'])
    def get_templates():
        templates = [f.split('.')[0] for f in os.listdir(app.config['TEMPLATE_FOLDER']) if f.endswith('.json')]
        return jsonify(templates), 200

    @app.route('/default_template', methods=['GET'])
    def get_default_template():
        template_path = 'resources/json_templates/default_template.json'
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                template = json.load(f)
            return jsonify(template), 200
        return jsonify({'message': 'Default template not found'}), 404

    @app.route('/templates/<name>', methods=['GET'])
    def get_template(name):
        if name == "default":
            template_path = 'resources/json_templates/default_template.json'
        else:
            template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{name}.json')

        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                template = json.load(f)
            return jsonify(template), 200
        return jsonify({'message': 'Template not found'}), 404
