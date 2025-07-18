"""
Configuración global para pruebas.
Este archivo contiene fixtures y configuraciones que se aplican a todas las pruebas.
"""
import os
import pytest
from unittest.mock import patch
from dotenv import load_dotenv
from pathlib import Path

# Configuramos variables de entorno para pruebas antes de que se importen los módulos
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Configura variables de entorno para pruebas cargando el archivo .env.test.
    Este fixture se ejecuta automáticamente antes de todas las pruebas.
    """
    # Guardamos las variables de entorno originales
    original_env = os.environ.copy()
    
    # Cargamos variables de entorno desde .env.test
    env_test_path = Path(__file__).parent.parent / ".env.test"
    if env_test_path.exists():
        load_dotenv(env_test_path, override=True)
    else:
        pytest.fail(f"Archivo .env.test no encontrado en {env_test_path}. Por favor, crea este archivo con las variables de entorno para pruebas.")
    
    yield
    
    # Restauramos las variables de entorno originales
    os.environ.clear()
    os.environ.update(original_env)
