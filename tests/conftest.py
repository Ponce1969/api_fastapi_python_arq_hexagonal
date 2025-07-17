"""
Configuración global para pruebas.
Este archivo contiene fixtures y configuraciones que se aplican a todas las pruebas.
"""
import os
import pytest
from unittest.mock import patch

# Configuramos variables de entorno para pruebas antes de que se importen los módulos
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Configura variables de entorno para pruebas.
    Este fixture se ejecuta automáticamente antes de todas las pruebas.
    """
    # Guardamos las variables de entorno originales
    original_env = os.environ.copy()
    
    # Establecemos variables de entorno para pruebas
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["SECRET_KEY"] = "test_secret_key_for_testing_only"
    os.environ["ALGORITHM"] = "HS256"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    os.environ["DOCS_ENABLED"] = "True"
    os.environ["DOCS_USERNAME"] = "test"
    os.environ["DOCS_PASSWORD"] = "test"
    os.environ["DEBUG"] = "True"
    
    yield
    
    # Restauramos las variables de entorno originales
    os.environ.clear()
    os.environ.update(original_env)
