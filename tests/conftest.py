import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

from app.main import app
from app.db import Base, get_db
from app.models import models # Importar para que se creen las tablas (Alembic sería mejor en producción)

# Cargar variables de entorno para las pruebas
load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not set in the .env file. Please create a separate PostgreSQL database for testing and set TEST_DATABASE_URL.")

# Configuración del motor para la base de datos de prueba (PostgreSQL)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Sobrescribir la Dependencia get_db ---
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Aplicamos la sobrescritura a nuestra app
app.dependency_overrides[get_db] = override_get_db

# --- Fixture de Pytest para el cliente de prueba ---
@pytest.fixture(scope="module")
def client():
    # Creamos las tablas antes de que se ejecuten las pruebas del módulo
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    # Borramos todas las tablas después de que terminen las pruebas del módulo
    Base.metadata.drop_all(bind=engine)

# --- Fixture para la sesión de base de datos ---
@pytest.fixture(scope="function")
def db_session():
    """Proporciona una sesión de BD para cada test, y se hace rollback después."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Reemplazamos get_db durante la duración del test con esta sesión transaccional
    def override_get_db_for_session():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db_for_session
    
    yield session

    # Hacemos rollback de la transacción y cerramos la conexión
    transaction.rollback()
    connection.close()
    app.dependency_overrides[get_db] = override_get_db # Restaurar la dependencia original