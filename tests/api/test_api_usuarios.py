"""
Pruebas funcionales para los endpoints de la API de usuarios.
Estas pruebas utilizan TestClient de FastAPI para simular solicitudes HTTP
y verificar las respuestas.
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.main import app
from app.api.deps import get_unit_of_work, get_hasher, get_jwt_handler
from app.infraestructura.persistencia.unit_of_work import SQLAlchemyUnitOfWork
from app.infraestructura.seguridad.hasher import Hasher
from app.infraestructura.seguridad.jwt_handler import JWTHandler
from app.dominio.repositorios.unit_of_work import IUnitOfWork
from app.core.config import settings

# Configuración de la base de datos de prueba
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Fixtures para la configuración de pruebas
@pytest.fixture
def async_engine():
    """Crea un motor de base de datos asíncrono para pruebas."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    yield engine
    engine.dispose()

@pytest.fixture
def session_factory(async_engine):
    """Crea una fábrica de sesiones para pruebas."""
    from app.infraestructura.persistencia.modelos_orm import Base
    
    # Crear tablas
    Base.metadata.create_all(bind=async_engine.sync_engine)
    
    async_session_factory = async_sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    
    yield async_session_factory
    
    # Limpiar la base de datos después de las pruebas
    Base.metadata.drop_all(bind=async_engine.sync_engine)

@pytest.fixture
def unit_of_work(session_factory) -> IUnitOfWork:
    """Proporciona un UnitOfWork para pruebas."""
    return SQLAlchemyUnitOfWork(session_factory)

@pytest.fixture
def hasher():
    """Proporciona un hasher para pruebas."""
    return Hasher()

@pytest.fixture
def jwt_handler():
    """Proporciona un JWT handler para pruebas."""
    return JWTHandler(
        secret_key="test_secret_key",
        algorithm="HS256",
        access_token_expire_minutes=30
    )

@pytest.fixture
def client(unit_of_work, hasher, jwt_handler):
    """Proporciona un cliente de prueba para la API."""
    # Sobreescribir las dependencias con nuestras implementaciones de prueba
    app.dependency_overrides[get_unit_of_work] = lambda: unit_of_work
    app.dependency_overrides[get_hasher] = lambda: hasher
    app.dependency_overrides[get_jwt_handler] = lambda: jwt_handler
    
    # Crear cliente de prueba
    with TestClient(app) as client:
        yield client
    
    # Limpiar las sobreescrituras después de las pruebas
    app.dependency_overrides.clear()

@pytest.fixture
def create_user(client):
    """Función auxiliar para crear un usuario de prueba."""
    def _create_user(email=None, password="testpassword", full_name="Test User"):
        if email is None:
            email = f"test_{uuid.uuid4()}@example.com"
        
        response = client.post(
            "/api/usuarios/",
            json={
                "email": email,
                "password": password,
                "full_name": full_name
            }
        )
        return response.json(), email, password
    
    return _create_user

@pytest.fixture
def auth_headers(client, create_user):
    """Proporciona headers de autenticación para un usuario de prueba."""
    user_data, email, password = create_user()
    
    # Obtener token de acceso
    response = client.post(
        "/api/auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_crear_usuario(client):
    """Prueba la creación de un usuario a través de la API."""
    email = f"test_{uuid.uuid4()}@example.com"
    
    response = client.post(
        "/api/usuarios/",
        json={
            "email": email,
            "password": "testpassword",
            "full_name": "Test User"
        }
    )
    
    # Verificar respuesta
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["full_name"] == "Test User"
    assert "id" in data
    assert "hashed_pwd" not in data  # No debe exponer la contraseña hasheada

def test_crear_usuario_email_duplicado(client, create_user):
    """Prueba que no se pueden crear dos usuarios con el mismo email."""
    # Crear primer usuario
    user_data, email, _ = create_user()
    
    # Intentar crear un segundo usuario con el mismo email
    response = client.post(
        "/api/usuarios/",
        json={
            "email": email,
            "password": "anotherpassword",
            "full_name": "Another User"
        }
    )
    
    # Verificar respuesta de error
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert email in data["detail"]

def test_obtener_usuario_actual(client, auth_headers):
    """Prueba obtener el usuario actual autenticado."""
    response = client.get(
        "/api/usuarios/me",
        headers=auth_headers
    )
    
    # Verificar respuesta
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "full_name" in data
    assert "id" in data

def test_obtener_usuario_sin_autenticacion(client):
    """Prueba que no se puede acceder a rutas protegidas sin autenticación."""
    response = client.get("/api/usuarios/me")
    
    # Verificar respuesta de error
    assert response.status_code == 401

def test_actualizar_usuario(client, auth_headers):
    """Prueba la actualización de un usuario."""
    nuevo_nombre = "Nombre Actualizado"
    
    response = client.put(
        "/api/usuarios/me",
        headers=auth_headers,
        json={
            "full_name": nuevo_nombre
        }
    )
    
    # Verificar respuesta
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == nuevo_nombre

def test_cambiar_password(client, auth_headers, create_user):
    """Prueba el cambio de contraseña de un usuario."""
    # Crear usuario
    _, email, password = create_user()
    
    # Obtener token
    response = client.post(
        "/api/auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Cambiar contraseña
    nueva_password = "nuevapassword123"
    response = client.post(
        "/api/usuarios/me/password",
        headers=headers,
        json={
            "current_password": password,
            "new_password": nueva_password
        }
    )
    
    # Verificar respuesta
    assert response.status_code == 200
    
    # Verificar que la nueva contraseña funciona
    response = client.post(
        "/api/auth/login",
        data={
            "username": email,
            "password": nueva_password
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    
    # Verificar que la contraseña antigua ya no funciona
    response = client.post(
        "/api/auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    assert response.status_code == 401

def test_cambiar_password_incorrecto(client, auth_headers):
    """Prueba el cambio de contraseña con la contraseña actual incorrecta."""
    response = client.post(
        "/api/usuarios/me/password",
        headers=auth_headers,
        json={
            "current_password": "passwordincorrecta",
            "new_password": "nuevapassword123"
        }
    )
    
    # Verificar respuesta de error
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data

def test_login_correcto(client, create_user):
    """Prueba el login con credenciales correctas."""
    # Crear usuario
    _, email, password = create_user()
    
    # Intentar login
    response = client.post(
        "/api/auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    
    # Verificar respuesta
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

def test_login_incorrecto(client):
    """Prueba el login con credenciales incorrectas."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    
    # Verificar respuesta de error
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
