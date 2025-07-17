"""
Pruebas de integración para el servicio de usuario.
Estas pruebas validan que el servicio de usuario funcione correctamente
con el UnitOfWork y el mapeador de excepciones.
"""
import pytest
import uuid
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.dominio.entidades.usuario import Usuario
from app.dominio.excepciones.dominio_excepciones import (
    EmailYaRegistradoError, 
    UsuarioNoEncontradoError,
    CredencialesInvalidasError
)
from app.dominio.interfaces.unit_of_work import IUnitOfWork
from app.infraestructura.persistencia.unit_of_work import SQLAlchemyUnitOfWork
from app.servicios.usuario_servicio import UsuarioServicio
from app.core.seguridad.hashing import PasslibHasher

# Configuración de la base de datos de prueba
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

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
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_factory = async_sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    
    yield async_session_factory
    
    # Limpiar la base de datos después de las pruebas
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def unit_of_work(session_factory) -> AsyncGenerator[IUnitOfWork, None]:
    """Proporciona un UnitOfWork para pruebas."""
    uow = SQLAlchemyUnitOfWork(session_factory)
    yield uow

@pytest.fixture
def hasher():
    """Proporciona un hasher para pruebas."""
    return PasslibHasher()

@pytest.fixture
def usuario_servicio(unit_of_work, hasher):
    """Proporciona un servicio de usuario para pruebas."""
    return UsuarioServicio(unit_of_work, hasher)

@pytest.mark.asyncio
async def test_crear_usuario(usuario_servicio):
    """Prueba la creación de un usuario."""
    # Datos de prueba
    email = f"test_{uuid.uuid4()}@example.com"
    password = "password123"
    full_name = "Test User"
    
    # Crear usuario
    usuario = await usuario_servicio.crear_usuario(
        email=email,
        password=password,
        full_name=full_name
    )
    
    # Verificar que el usuario se creó correctamente
    assert usuario is not None
    assert usuario.email == email
    assert usuario.full_name == full_name
    assert usuario.is_active == True
    
    # Verificar que la contraseña está hasheada
    assert usuario.hashed_pwd != password
    assert len(usuario.hashed_pwd) > 0

@pytest.mark.asyncio
async def test_crear_usuario_email_duplicado(usuario_servicio):
    """Prueba que no se pueden crear dos usuarios con el mismo email."""
    # Datos de prueba
    email = f"test_{uuid.uuid4()}@example.com"
    password = "password123"
    full_name = "Test User"
    
    # Crear el primer usuario
    await usuario_servicio.crear_usuario(
        email=email,
        password=password,
        full_name=full_name
    )
    
    # Intentar crear un segundo usuario con el mismo email
    with pytest.raises(EmailYaRegistradoError) as excinfo:
        await usuario_servicio.crear_usuario(
            email=email,
            password="otherpassword",
            full_name="Other User"
        )
    
    # Verificar el mensaje de error
    assert email in str(excinfo.value)

@pytest.mark.asyncio
async def test_obtener_usuario_por_id(usuario_servicio):
    """Prueba obtener un usuario por su ID."""
    # Crear usuario
    email = f"test_{uuid.uuid4()}@example.com"
    usuario_creado = await usuario_servicio.crear_usuario(
        email=email,
        password="password123",
        full_name="Test User"
    )
    
    # Obtener usuario por ID
    usuario = await usuario_servicio.obtener_usuario_por_id(usuario_creado.id)
    
    # Verificar que se obtuvo el usuario correcto
    assert usuario is not None
    assert usuario.id == usuario_creado.id
    assert usuario.email == email

@pytest.mark.asyncio
async def test_obtener_usuario_por_id_no_existente(usuario_servicio):
    """Prueba obtener un usuario con un ID que no existe."""
    # ID que no existe
    id_no_existente = uuid.uuid4()
    
    # Intentar obtener usuario por ID
    with pytest.raises(UsuarioNoEncontradoError):
        await usuario_servicio.obtener_usuario_por_id(id_no_existente)

@pytest.mark.asyncio
async def test_autenticar_usuario(usuario_servicio):
    """Prueba la autenticación de un usuario."""
    # Datos de prueba
    email = f"test_{uuid.uuid4()}@example.com"
    password = "password123"
    
    # Crear usuario
    await usuario_servicio.crear_usuario(
        email=email,
        password=password,
        full_name="Test User"
    )
    
    # Autenticar usuario
    usuario_autenticado = await usuario_servicio.verificar_credenciales(email, password)
    
    # Verificar que la autenticación fue exitosa
    assert usuario_autenticado is not None
    assert usuario_autenticado.email == email

@pytest.mark.asyncio
async def test_autenticar_usuario_email_incorrecto(usuario_servicio):
    """Prueba la autenticación con un email que no existe."""
    # Email que no existe
    email_no_existente = f"nonexistent_{uuid.uuid4()}@example.com"
    
    # Intentar autenticar
    with pytest.raises(CredencialesInvalidasError):
        await usuario_servicio.verificar_credenciales(email_no_existente, "password123")

@pytest.mark.asyncio
async def test_autenticar_usuario_password_incorrecto(usuario_servicio):
    """Prueba la autenticación con una contraseña incorrecta."""
    # Datos de prueba
    email = f"test_{uuid.uuid4()}@example.com"
    password = "password123"
    
    # Crear usuario
    await usuario_servicio.crear_usuario(
        email=email,
        password=password,
        full_name="Test User"
    )
    
    # Intentar autenticar con contraseña incorrecta
    with pytest.raises(CredencialesInvalidasError):
        await usuario_servicio.verificar_credenciales(email, "wrong_password")

@pytest.mark.asyncio
async def test_cambiar_password(usuario_servicio):
    """Prueba el cambio de contraseña de un usuario."""
    # Datos de prueba
    email = f"test_{uuid.uuid4()}@example.com"
    password_original = "password123"
    password_nuevo = "newpassword456"
    
    # Crear usuario
    usuario_creado = await usuario_servicio.crear_usuario(
        email=email,
        password=password_original,
        full_name="Test User"
    )
    
    # Cambiar contraseña
    await usuario_servicio.cambiar_contrasena(
        user_id=usuario_creado.id,
        contrasena_actual=password_original,
        nueva_contrasena=password_nuevo
    )  
    # Verificar que la autenticación falla con la contraseña antigua
    with pytest.raises(CredencialesInvalidasError):
        await usuario_servicio.verificar_credenciales(email, password_original)
    
    # Verificar que la autenticación funciona con la nueva contraseña
    usuario = await usuario_servicio.verificar_credenciales(email, password_nuevo)
    assert usuario is not None
    assert usuario.id == usuario_creado.id

@pytest.mark.asyncio
async def test_cambiar_password_current_incorrecto(usuario_servicio):
    """Prueba el cambio de contraseña con la contraseña actual incorrecta."""
    # Datos de prueba
    email = f"test_{uuid.uuid4()}@example.com"
    password_original = "password123"
    
    # Crear usuario
    usuario_creado = await usuario_servicio.crear_usuario(
        email=email,
        password=password_original,
        full_name="Test User"
    )
    
    # Intentar cambiar contraseña con contraseña actual incorrecta
    with pytest.raises(CredencialesInvalidasError):
        await usuario_servicio.cambiar_contrasena(
            user_id=usuario_creado.id,
            contrasena_actual="wrong_password",
            nueva_contrasena="newpassword456"
        )

@pytest.mark.asyncio
async def test_actualizar_usuario(usuario_servicio):
    """Prueba la actualización de un usuario."""
    # Datos de prueba
    email = f"test_{uuid.uuid4()}@example.com"
    
    # Crear usuario
    usuario_creado = await usuario_servicio.crear_usuario(
        email=email,
        password="password123",
        full_name="Test User"
    )
    
    # Nuevos datos
    nuevo_full_name = "Updated User"
    
    # Actualizar usuario
    usuario_actualizado = await usuario_servicio.actualizar_usuario(
        user_id=usuario_creado.id,
        full_name=nuevo_full_name
    )  
    # Verificar que se actualizó correctamente
    assert usuario_actualizado.full_name == nuevo_full_name
    assert usuario_actualizado.email == email  # El email no debe cambiar
    
    # Verificar que los cambios persisten
    usuario = await usuario_servicio.obtener_usuario_por_id(usuario_creado.id)
    assert usuario.full_name == nuevo_full_name
