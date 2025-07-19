"""
Pruebas funcionales para los endpoints de la API de usuarios.
Estas pruebas utilizan TestClient de FastAPI para simular solicitudes HTTP
y verificar las respuestas.
"""
import os
import pytest
import pytest_asyncio
import asyncio
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env.test antes de importar la aplicación
env_path = Path(__file__).parents[2] / ".env.test"  # Subir dos niveles desde tests/api/ a la raíz
load_dotenv(dotenv_path=env_path, override=True)

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# Ahora importamos la aplicación después de cargar las variables de entorno
from app.main import app
from app.core.deps import get_unit_of_work, get_hasher, get_jwt_handler
from app.infraestructura.persistencia.unit_of_work import SQLAlchemyUnitOfWork
from app.core.seguridad.hashing import PasslibHasher
from app.core.seguridad.jwt import JWTHandler
from app.dominio.interfaces.unit_of_work import IUnitOfWork
from app.core.config import settings

# Configuración de la base de datos de prueba
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Fixtures para la configuración de pruebas
@pytest_asyncio.fixture
async def async_engine():
    """Crea un motor de base de datos asíncrono para pruebas."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
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
    
    # Limpiar la base de datos después de las pruebas
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def unit_of_work(session_factory) -> IUnitOfWork:
    """Proporciona un UnitOfWork para pruebas."""
    return SQLAlchemyUnitOfWork(session_factory)

@pytest_asyncio.fixture
async def hasher():
    """Proporciona un hasher para pruebas."""
    return PasslibHasher()

@pytest_asyncio.fixture
async def jwt_handler():
    """Proporciona un JWT handler para pruebas."""
    return JWTHandler()

@pytest_asyncio.fixture
async def async_client(unit_of_work, hasher, jwt_handler):
    """Proporciona un cliente asíncrono de prueba para la API."""
    # Sobreescribir las dependencias con nuestras implementaciones de prueba
    app.dependency_overrides[get_unit_of_work] = lambda: unit_of_work
    app.dependency_overrides[get_hasher] = lambda: hasher
    app.dependency_overrides[get_jwt_handler] = lambda: jwt_handler

    # Crear cliente asíncrono de prueba usando ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        yield client

    # Limpiar las sobreescrituras de dependencias
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def create_user(async_client):
    """Función auxiliar para crear un usuario de prueba."""
    async def _create_user(email=None, password="testpassword", full_name="Test User"):
        if email is None:
            email = f"test_{uuid.uuid4()}@example.com"
        
        response = await async_client.post(
            "/api/v2/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": full_name
            }
        )
        return response.json(), email, password
    
    return _create_user

@pytest_asyncio.fixture
async def auth_headers(async_client, create_user):
    """Proporciona headers de autenticación para un usuario de prueba."""
    user_data, email, password = await create_user()
    
    # Obtener token de acceso
    response = await async_client.post(
        "/api/v2/auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_crear_usuario(async_client):
    """Prueba la creación de un usuario a través de la API."""
    email = f"test_{uuid.uuid4()}@example.com"
    
    response = await async_client.post(
        "/api/v2/auth/register",
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

@pytest.mark.asyncio
async def test_crear_usuario_email_duplicado(async_client, create_user):
    """Prueba que no se pueden crear dos usuarios con el mismo email."""
    # Crear un usuario primero
    _, email, _ = await create_user()
    
    # Intentar crear otro usuario con el mismo email
    response = await async_client.post(
        "/api/v2/auth/register",
        json={
            "email": email,
            "password": "testpassword2",
            "full_name": "Test User 2"
        }
    )
    
    # Verificar que se rechaza la solicitud
    assert response.status_code == 409
    assert "correo electrónico" in response.json()["detail"].lower() and "ya está registrado" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_obtener_usuario_actual(async_client, auth_headers):
    """Prueba obtener el usuario actual autenticado."""
    response = await async_client.get("/api/v2/auth/me", headers=auth_headers)
    
    # Verificar respuesta
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "full_name" in data
    assert "id" in data

@pytest.mark.asyncio
async def test_obtener_usuario_sin_autenticacion(async_client):
    """Prueba que no se puede acceder a rutas protegidas sin autenticación."""
    response = await async_client.get("/api/v2/auth/me")
    
    # Verificar que se rechaza la solicitud
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_actualizar_usuario(async_client, auth_headers):
    """Prueba actualizar los datos de un usuario."""
    # Obtenemos el ID del usuario actual primero
    me_response = await async_client.get(
        "/api/v2/auth/me",
        headers=auth_headers
    )
    user_id = me_response.json()["id"]
    
    response = await async_client.put(
        f"/api/v2/usuarios/{user_id}",
        json={"email": me_response.json()["email"], "full_name": "Nombre Actualizado", "is_active": True},
        headers=auth_headers
    )
    
    # Verificar respuesta
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Nombre Actualizado"

# TODO: Implementar endpoint de cambio de contraseña
# @pytest.mark.asyncio
# async def test_cambiar_password(async_client, auth_headers, create_user):
#     """Prueba cambiar la contraseña de un usuario."""
#     # Obtener datos del usuario creado
#     _, email, old_password = await create_user()
#     
#     # Cambiar contraseña
#     new_password = "nuevacontraseña123"
#     response = await async_client.post(
#         "/api/v2/auth/me/cambiar-password",
#         json={
#             "current_password": old_password,
#             "new_password": new_password
#         },
#         headers=auth_headers
#     )
#     
#     # Verificar respuesta
#     assert response.status_code == 200
#     
#     # Verificar que podemos iniciar sesión con la nueva contraseña
#     login_response = await async_client.post(
#         "/api/v2/auth/login",
#         data={
#             "username": email,
#             "password": new_password
#         }
#     )
#     
#     assert login_response.status_code == 200
#     assert "access_token" in login_response.json()

# TODO: Implementar endpoint de cambio de contraseña
# @pytest.mark.asyncio
# async def test_cambiar_password_incorrecto(async_client, auth_headers):
#     """Prueba que no se puede cambiar la contraseña con credenciales incorrectas."""
#     response = await async_client.post(
#         "/api/v2/auth/me/cambiar-password",
#         json={
#             "current_password": "contraseñaincorrecta",
#             "new_password": "nuevacontraseña123"
#         },
#         headers=auth_headers
#     )
#     
#     # Verificar que se rechaza la solicitud
#     assert response.status_code == 400
#     assert "contraseña actual" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_login_correcto(async_client, create_user):
    """Prueba iniciar sesión con credenciales correctas."""
    # Crear usuario
    _, email, password = await create_user()
    
    # Intentar iniciar sesión
    response = await async_client.post(
        "/api/v2/auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    
    # Verificar respuesta
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_incorrecto(async_client, create_user):
    """Prueba que no se puede iniciar sesión con credenciales incorrectas."""
    # Crear usuario
    _, email, _ = await create_user()
    
    # Intentar iniciar sesión con contraseña incorrecta
    response = await async_client.post(
        "/api/v2/auth/login",
        data={
            "username": email,
            "password": "contraseñaincorrecta"
        }
    )
    
    # Verificar que se rechaza la solicitud
    assert response.status_code == 401
    assert "correo electrónico o contraseña incorrectos" in response.json()["detail"].lower()
