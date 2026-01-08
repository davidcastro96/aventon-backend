# app/__init__.py
from flask import Flask
from .config import Config # Importa la configuración

def create_app(config_class=Config):
    """Inicializa la aplicación Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 1. Registro de Blueprints 
    
    # Importamos el Blueprint de la API
    from app.api import api_bp
    
    # REGISTRO CRÍTICO: Aquí se define el prefijo /api/v1
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    return app