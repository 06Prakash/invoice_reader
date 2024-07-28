import logging
from flask import Flask
from flask_cors import CORS
import os

# Import modules from the new location
from modules.routes import register_routes

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.config.from_object('config')

register_routes(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
