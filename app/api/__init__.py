# app/api/__init__.py
from flask import Blueprint

# Crea el Blueprint
api_bp = Blueprint('api_bp', __name__)

# IMPORTACIÓN CRÍTICA: Esto registra las rutas de auth.py en api_bp
from . import auth