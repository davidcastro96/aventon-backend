# Entorno virtual
python311 -m venv venv
venv\Scripts\activate
# Ejecución
python311 run.py

# Estructura del proyecto
/mi_backend_aventon
├── venv/                      # Entorno virtual
├── .env                       # Variables de entorno (claves, secretos)
├── run.py                     # Punto de entrada de la aplicación
├── requirements.txt           # Lista de dependencias
└── /app                       # Directorio principal del backend
    ├── __init__.py            # Crea y configura la aplicación Flask
    ├── config.py              # Configuraciones de la app
    └── /api
        ├── __init__.py        # Blueprint (paquete de rutas) de la API
        └── auth.py            # Rutas para Autenticación (login, registro)