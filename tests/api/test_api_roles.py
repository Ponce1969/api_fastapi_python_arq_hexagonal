"""
Pruebas funcionales para los endpoints de la API de roles.
Estas pruebas utilizan TestClient de FastAPI para simular solicitudes HTTP
y verificar las respuestas.
"""
# Establecemos variables de entorno antes de importar cualquier módulo
import os
import sys
from unittest import mock

# Configuramos las variables de entorno para pruebas
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_only"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["DOCS_ENABLED"] = "True"
os.environ["DOCS_USERNAME"] = "test"
os.environ["DOCS_PASSWORD"] = "test"
os.environ["DEBUG"] = "True"

# Parcheamos la función create_async_engine antes de importar cualquier otro módulo
original_create_async_engine = None

def patched_create_async_engine(url, **kwargs):
    """Versión parcheada de create_async_engine que elimina argumentos inválidos para SQLite"""
    if 'sqlite' in url:
        # Eliminamos argumentos que no son válidos para SQLite
        kwargs.pop('pool_size', None)
        kwargs.pop('max_overflow', None)
    return original_create_async_engine(url, **kwargs)

# Guardamos la función original y aplicamos el parche
from sqlalchemy.ext.asyncio import create_async_engine as original_engine
original_create_async_engine = original_engine
sys.modules['sqlalchemy.ext.asyncio'].create_async_engine = patched_create_async_engine

# Ahora importamos los módulos necesarios
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import async_sessionmaker

# Importamos las dependencias necesarias
from app.main import app
from app.core.deps import get_unit_of_work, get_hasher, get_jwt_handler
from app.core.seguridad.hashing import Hasher, PasslibHasher
from app.core.seguridad.jwt import JWTHandler
from app.dominio.interfaces.unit_of_work import IUnitOfWork
from app.infraestructura.persistencia.unit_of_work import SQLAlchemyUnitOfWork
from app.core.config import settings

# Configuración de la base de datos de prueba
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Fixtures para la configuración de pruebas
@pytest.fixture
async def async_engine():
    """Crea un motor de base de datos asíncrono para pruebas."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()

@pytest.fixture
async def session_factory(async_engine):
    """Crea una fábrica de sesiones para pruebas."""
    from app.infraestructura.persistencia.modelos_orm import Base
    
    # Crear tablas de forma asíncrona
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_factory = async_sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    
    yield async_session_factory
    
    # Limpiar la base de datos después de las pruebas de forma asíncrona
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def unit_of_work(session_factory) -> IUnitOfWork:
    """Proporciona un UnitOfWork para pruebas."""
    return SQLAlchemyUnitOfWork(session_factory)

@pytest.fixture
async def hasher() -> Hasher:
    """Proporciona un hasher para pruebas."""
    return PasslibHasher()

@pytest.fixture
async def jwt_handler() -> JWTHandler:
    """Proporciona un manejador JWT para pruebas."""
    return JWTHandler()

@pytest.fixture
async def client(unit_of_work, hasher, jwt_handler):
    """Proporciona un cliente de prueba para la API."""
    # Override dependencies
    app.dependency_overrides[get_unit_of_work] = lambda: unit_of_work
    app.dependency_overrides[get_hasher] = lambda: hasher
    app.dependency_overrides[get_jwt_handler] = lambda: jwt_handler
    
    # Create test client
    test_client = TestClient(app)
    
    yield test_client
    
    # Clean up
    app.dependency_overrides = {}

@pytest.fixture
async def create_user(client):
    """Función auxiliar para crear un usuario de prueba."""
    user_data = {
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    }
    response = client.post("/api/v2/auth/register", json=user_data)
    assert response.status_code == 201
    return response.json()

@pytest.fixture
async def auth_headers(client, create_user):
    """Proporciona headers de autenticación para un usuario de prueba."""
    login_data = {
        "username": "test@example.com",
        "password": "password123"
    }
    response = client.post("/api/v2/auth/login", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_crear_rol(client, auth_headers):
    """Prueba la creación de un rol a través de la API."""
    rol_data = {
        "name": "admin",
        "description": "Administrador del sistema"
    }
    
    response = client.post(
        "/api/v2/roles",
        json=rol_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == rol_data["name"]
    assert data["description"] == rol_data["description"]
    assert "id" in data

@pytest.mark.asyncio
async def test_crear_rol_duplicado(client, auth_headers):
    """Prueba que no se pueden crear dos roles con el mismo nombre."""
    # Crear el primer rol
    rol_data = {
        "name": "editor",
        "description": "Editor de contenido"
    }
    
    response = client.post(
        "/api/v2/roles",
        json=rol_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    
    # Intentar crear un rol con el mismo nombre
    response = client.post(
        "/api/v2/roles",
        json=rol_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "ya existe" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_listar_roles(client, auth_headers):
    """Prueba listar todos los roles."""
    # Crear algunos roles primero
    roles = [
        {"name": "admin", "description": "Administrador del sistema"},
        {"name": "editor", "description": "Editor de contenido"},
        {"name": "viewer", "description": "Visualizador de contenido"}
    ]
    
    for rol_data in roles:
        response = client.post(
            "/api/v2/roles",
            json=rol_data,
            headers=auth_headers
        )
        assert response.status_code == 201
    
    # Listar roles
    response = client.get(
        "/api/v2/roles",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    
    # Verificar que los roles creados están en la lista
    role_names = [rol["name"] for rol in data]
    for rol_data in roles:
        assert rol_data["name"] in role_names

@pytest.mark.asyncio
async def test_obtener_rol_por_id(client, auth_headers):
    """Prueba obtener un rol por su ID."""
    # Crear un rol primero
    rol_data = {
        "name": "supervisor",
        "description": "Supervisor del sistema"
    }
    
    create_response = client.post(
        "/api/v2/roles",
        json=rol_data,
        headers=auth_headers
    )
    
    assert create_response.status_code == 201
    rol_id = create_response.json()["id"]
    
    # Obtener el rol por ID
    response = client.get(
        f"/api/v2/roles/{rol_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == rol_id
    assert data["name"] == rol_data["name"]
    assert data["description"] == rol_data["description"]

@pytest.mark.asyncio
async def test_obtener_rol_inexistente(client, auth_headers):
    """Prueba obtener un rol que no existe."""
    non_existent_id = str(uuid.uuid4())
    
    response = client.get(
        f"/api/v2/roles/{non_existent_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "no se encontró ningún rol" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_actualizar_rol(client, auth_headers):
    """Prueba la actualización de un rol."""
    # Crear un rol primero
    rol_data = {
        "name": "auditor",
        "description": "Auditor del sistema"
    }
    
    create_response = client.post(
        "/api/v2/roles",
        json=rol_data,
        headers=auth_headers
    )
    
    assert create_response.status_code == 201
    rol_id = create_response.json()["id"]
    
    # Actualizar el rol
    update_data = {
        "name": "auditor_senior",
        "description": "Auditor senior del sistema"
    }
    
    response = client.put(
        f"/api/v2/roles/{rol_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == rol_id
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]

@pytest.mark.asyncio
async def test_actualizar_rol_inexistente(client, auth_headers):
    """Prueba actualizar un rol que no existe."""
    non_existent_id = str(uuid.uuid4())
    
    update_data = {
        "name": "non_existent",
        "description": "This role doesn't exist"
    }
    
    response = client.put(
        f"/api/v2/roles/{non_existent_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "no se encontró ningún rol" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_eliminar_rol(client, auth_headers):
    """Prueba la eliminación de un rol."""
    # Crear un rol primero
    rol_data = {
        "name": "temporal",
        "description": "Rol temporal para pruebas"
    }
    
    create_response = client.post(
        "/api/v2/roles",
        json=rol_data,
        headers=auth_headers
    )
    
    assert create_response.status_code == 201
    rol_id = create_response.json()["id"]
    
    # Eliminar el rol
    response = client.delete(
        f"/api/v2/roles/{rol_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    # Verificar que el rol ya no existe
    get_response = client.get(
        f"/api/v2/roles/{rol_id}",
        headers=auth_headers
    )
    
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_eliminar_rol_inexistente(client, auth_headers):
    """Prueba eliminar un rol que no existe."""
    non_existent_id = str(uuid.uuid4())
    
    response = client.delete(
        f"/api/v2/roles/{non_existent_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "no se encontró ningún rol" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_acceso_sin_autenticacion(client):
    """Prueba que no se puede acceder a rutas protegidas sin autenticación."""
    # Intentar listar roles sin autenticación
    response = client.get("/api/v2/roles")
    assert response.status_code == 401
    
    # Intentar crear un rol sin autenticación
    rol_data = {
        "name": "unauthorized",
        "description": "Rol sin autorización"
    }
    
    response = client.post(
        "/api/v2/roles",
        json=rol_data
    )
    
    assert response.status_code == 401
