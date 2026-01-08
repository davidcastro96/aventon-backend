# app/api/auth.py
from flask import jsonify, request
from . import api_bp

# -------------------------------------------------------------
# RUTAS DE AUTENTICACIÓN
# -------------------------------------------------------------

# RUTA 1: Raíz del Blueprint (/api/v1/)
@api_bp.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Backend aventon v1 - Estado: Operativo (Simulación)", "status": "ok"})

# RUTA 2: Registro (/api/v1/auth/register)
@api_bp.route('/auth/register', methods=['POST'])
def register():
    # Lógica simulada
    data = request.get_json()
    email = data.get('email', 'N/A')
    
    return jsonify({
        "message": f"Usuario {email} registrado exitosamente (Simulación).",
        "user_id": 999
    }), 201

# RUTA 3: Login (/api/v1/auth/login)
@api_bp.route('/auth/login', methods=['POST'])
def login():
    # Lógica simulada
    data = request.get_json()
    email = data.get('email', 'N/A')
    
    return jsonify({
        "message": f"Login exitoso para {email} (Simulación).",
        "user_id": 100
    }), 200