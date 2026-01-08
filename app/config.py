import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Clase de configuración base."""
    # Accede a la variable SECRET_KEY definida en .env
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_de_respaldo_muy_segura'
    # No hay configuración de base de datos aquí