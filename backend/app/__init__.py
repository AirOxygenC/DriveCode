from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')
    
    # Initialize extensions
    socketio.init_app(app)
    
    # Register Blueprints
    from .routes.auth_routes import auth_bp
    from .routes.system_routes import system_bp
    # Voice handling is primarily WS, but we might have some HTTP endpoints
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(system_bp, url_prefix='/system')

    # Register Socket Events
    from . import socket_handlers
    
    return app
