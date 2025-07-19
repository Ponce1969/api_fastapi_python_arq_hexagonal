import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from app.dominio.entidades.usuario import Usuario
from app.dominio.excepciones.dominio_excepciones import (
    EmailYaRegistradoError,
    UsuarioNoEncontradoError,
    CredencialesInvalidasError
)
from app.servicios.usuario_servicio import UsuarioServicio
from app.dominio.interfaces.unit_of_work import IUnitOfWork


@pytest.fixture
def mock_hasher():
    hasher = MagicMock()
    hasher.hash_password.return_value = "hashed_password"
    hasher.verify_password.return_value = True
    return hasher


@pytest.fixture
def mock_uow():
    uow = AsyncMock(spec=IUnitOfWork)
    uow.usuarios = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None
    return uow


@pytest.fixture
def mock_usuario():
    return Usuario(
        email="test@example.com",
        hashed_pwd="hashed_password",
        full_name="Test User",
        is_active=True,
        id=uuid.uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )


@pytest.fixture
def usuario_servicio(mock_uow, mock_hasher):
    return UsuarioServicio(uow=mock_uow, hasher=mock_hasher)


@pytest.mark.asyncio
async def test_crear_usuario_exitoso(usuario_servicio, mock_uow, mock_hasher):
    # Arrange
    mock_uow.usuarios.get_by_email.return_value = None
    mock_uow.usuarios.save.return_value = Usuario(
        email="nuevo@example.com",
        hashed_pwd="hashed_password",
        full_name="Nuevo Usuario",
        is_active=True
    )
    
    # Act
    resultado = await usuario_servicio.crear_usuario(
        email="nuevo@example.com",
        password="password123",
        full_name="Nuevo Usuario"
    )
    
    # Assert
    assert resultado.email == "nuevo@example.com"
    assert resultado.full_name == "Nuevo Usuario"
    assert resultado.is_active is True
    mock_uow.usuarios.get_by_email.assert_called_once_with("nuevo@example.com")
    mock_hasher.hash_password.assert_called_once_with("password123")
    mock_uow.usuarios.save.assert_called_once()
    # El commit se realiza automáticamente al salir del contexto del UnitOfWork
    # No es necesario verificar mock_uow.commit.call_count


@pytest.mark.asyncio
async def test_crear_usuario_email_ya_registrado(usuario_servicio, mock_uow, mock_usuario):
    # Arrange
    mock_uow.usuarios.get_by_email.return_value = mock_usuario
    
    # Act & Assert
    with pytest.raises(EmailYaRegistradoError):
        await usuario_servicio.crear_usuario(
            email="test@example.com",
            password="password123",
            full_name="Test User"
        )
    
    mock_uow.usuarios.get_by_email.assert_called_once_with("test@example.com")
    mock_uow.usuarios.save.assert_not_called()
    mock_uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_obtener_usuario_por_id_exitoso(usuario_servicio, mock_uow, mock_usuario):
    # Arrange
    mock_uow.usuarios.get_by_id.return_value = mock_usuario
    
    # Act
    resultado = await usuario_servicio.obtener_usuario_por_id(mock_usuario.id)
    
    # Assert
    assert resultado == mock_usuario
    mock_uow.usuarios.get_by_id.assert_called_once_with(mock_usuario.id)


@pytest.mark.asyncio
async def test_obtener_usuario_por_id_no_encontrado(usuario_servicio, mock_uow):
    # Arrange
    user_id = uuid.uuid4()
    mock_uow.usuarios.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(UsuarioNoEncontradoError):
        await usuario_servicio.obtener_usuario_por_id(user_id)
    
    mock_uow.usuarios.get_by_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_obtener_todos_los_usuarios(usuario_servicio, mock_uow, mock_usuario):
    # Arrange
    mock_uow.usuarios.get_all.return_value = [mock_usuario]
    
    # Act
    resultado = await usuario_servicio.obtener_todos_los_usuarios(skip=0, limit=10)
    
    # Assert
    assert len(resultado) == 1
    assert resultado[0] == mock_usuario
    mock_uow.usuarios.get_all.assert_called_once_with(skip=0, limit=10)


@pytest.mark.asyncio
async def test_actualizar_usuario_exitoso(usuario_servicio, mock_uow, mock_usuario):
    # Arrange
    mock_uow.usuarios.get_by_id.return_value = mock_usuario
    mock_uow.usuarios.get_by_email.return_value = None
    mock_uow.usuarios.save.return_value = mock_usuario
    
    # Act
    resultado = await usuario_servicio.actualizar_usuario(
        user_id=mock_usuario.id,
        email="nuevo@example.com",
        full_name="Nombre Actualizado",
        is_active=False
    )
    
    # Assert
    assert resultado == mock_usuario
    mock_uow.usuarios.get_by_id.assert_called_once_with(mock_usuario.id)
    mock_uow.usuarios.get_by_email.assert_called_once_with("nuevo@example.com")
    mock_uow.usuarios.save.assert_called_once()


@pytest.mark.asyncio
async def test_actualizar_usuario_email_ya_registrado(usuario_servicio, mock_uow, mock_usuario):
    # Arrange
    otro_usuario = Usuario(
        id=uuid.uuid4(),
        email="otro@example.com",
        hashed_pwd="hashed_password",
        full_name="Otro Usuario",
        is_active=True
    )
    mock_uow.usuarios.get_by_id.return_value = mock_usuario
    mock_uow.usuarios.get_by_email.return_value = otro_usuario
    
    # Act & Assert
    with pytest.raises(EmailYaRegistradoError):
        await usuario_servicio.actualizar_usuario(
            user_id=mock_usuario.id,
            email="otro@example.com"
        )
    
    mock_uow.usuarios.get_by_id.assert_called_once_with(mock_usuario.id)
    mock_uow.usuarios.get_by_email.assert_called_once_with("otro@example.com")
    mock_uow.usuarios.save.assert_not_called()


@pytest.mark.asyncio
async def test_actualizar_usuario_mismo_email(usuario_servicio, mock_uow, mock_usuario):
    # Arrange
    mock_uow.usuarios.get_by_id.return_value = mock_usuario
    mock_uow.usuarios.save.return_value = mock_usuario
    
    # Act
    resultado = await usuario_servicio.actualizar_usuario(
        user_id=mock_usuario.id,
        email=mock_usuario.email,  # Mismo email que ya tiene el usuario
        full_name="Nombre Actualizado"
    )
    
    # Assert
    assert resultado == mock_usuario
    mock_uow.usuarios.get_by_id.assert_called_once_with(mock_usuario.id)
    # No se debe llamar a get_by_email cuando el email no cambia
    mock_uow.usuarios.get_by_email.assert_not_called()
    mock_uow.usuarios.save.assert_called_once()


@pytest.mark.asyncio
async def test_actualizar_usuario_no_encontrado(usuario_servicio, mock_uow):
    # Arrange
    user_id = uuid.uuid4()
    mock_uow.usuarios.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(UsuarioNoEncontradoError):
        await usuario_servicio.actualizar_usuario(
            user_id=user_id,
            full_name="Nombre Actualizado"
        )
    
    mock_uow.usuarios.get_by_id.assert_called_once_with(user_id)
    mock_uow.usuarios.save.assert_not_called()
    mock_uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_eliminar_usuario_exitoso(usuario_servicio, mock_uow, mock_usuario):
    # Arrange
    mock_uow.usuarios.get_by_id.return_value = mock_usuario
    
    # Act
    await usuario_servicio.eliminar_usuario(mock_usuario.id)
    
    # Assert
    mock_uow.usuarios.get_by_id.assert_called_once_with(mock_usuario.id)
    mock_uow.usuarios.delete.assert_called_once_with(mock_usuario.id)


@pytest.mark.asyncio
async def test_eliminar_usuario_no_encontrado(usuario_servicio, mock_uow):
    # Arrange
    user_id = uuid.uuid4()
    mock_uow.usuarios.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(UsuarioNoEncontradoError):
        await usuario_servicio.eliminar_usuario(user_id)
    
    mock_uow.usuarios.get_by_id.assert_called_once_with(user_id)
    mock_uow.usuarios.delete.assert_not_called()


@pytest.mark.asyncio
async def test_verificar_credenciales_exitoso(usuario_servicio, mock_uow, mock_usuario, mock_hasher):
    # Arrange
    mock_uow.usuarios.get_by_email.return_value = mock_usuario
    mock_hasher.verify_password.return_value = True
    
    # Act
    resultado = await usuario_servicio.verificar_credenciales(
        email="test@example.com",
        password="password123"
    )
    
    # Assert
    assert resultado == mock_usuario
    mock_uow.usuarios.get_by_email.assert_called_once_with("test@example.com")
    mock_hasher.verify_password.assert_called_once_with("password123", mock_usuario.hashed_pwd)


@pytest.mark.asyncio
async def test_verificar_credenciales_usuario_no_encontrado(usuario_servicio, mock_uow):
    # Arrange
    mock_uow.usuarios.get_by_email.return_value = None
    
    # Act & Assert
    with pytest.raises(CredencialesInvalidasError):
        await usuario_servicio.verificar_credenciales(
            email="noexiste@example.com",
            password="password123"
        )
    
    mock_uow.usuarios.get_by_email.assert_called_once_with("noexiste@example.com")


@pytest.mark.asyncio
async def test_verificar_credenciales_contrasena_incorrecta(usuario_servicio, mock_uow, mock_usuario, mock_hasher):
    # Arrange
    mock_uow.usuarios.get_by_email.return_value = mock_usuario
    mock_hasher.verify_password.return_value = False
    
    # Act & Assert
    with pytest.raises(CredencialesInvalidasError):
        await usuario_servicio.verificar_credenciales(
            email="test@example.com",
            password="contrasena_incorrecta"
        )
    
    mock_uow.usuarios.get_by_email.assert_called_once_with("test@example.com")
    mock_hasher.verify_password.assert_called_once_with("contrasena_incorrecta", mock_usuario.hashed_pwd)


@pytest.mark.asyncio
async def test_verificar_credenciales_usuario_inactivo(usuario_servicio, mock_uow, mock_hasher):
    # Arrange
    usuario_inactivo = Usuario(
        id=uuid.uuid4(),
        email="inactivo@example.com",
        hashed_pwd="hashed_password",
        full_name="Usuario Inactivo",
        is_active=False
    )
    mock_uow.usuarios.get_by_email.return_value = usuario_inactivo
    mock_hasher.verify_password.return_value = True
    
    # Act & Assert
    with pytest.raises(CredencialesInvalidasError):
        await usuario_servicio.verificar_credenciales(
            email="inactivo@example.com",
            password="password123"
        )
    
    mock_uow.usuarios.get_by_email.assert_called_once_with("inactivo@example.com")
    mock_hasher.verify_password.assert_called_once_with("password123", usuario_inactivo.hashed_pwd)


@pytest.mark.asyncio
async def test_cambiar_contrasena_exitoso(usuario_servicio, mock_uow, mock_usuario, mock_hasher):
    # Arrange
    mock_uow.usuarios.get_by_id.return_value = mock_usuario
    mock_hasher.verify_password.return_value = True
    mock_hasher.hash_password.return_value = "nueva_contrasena_hasheada"
    
    # Act
    await usuario_servicio.cambiar_contrasena(
        user_id=mock_usuario.id,
        contrasena_actual="password123",
        nueva_contrasena="nueva_password"
    )
    
    # Assert
    mock_uow.usuarios.get_by_id.assert_called_once_with(mock_usuario.id)
    mock_hasher.verify_password.assert_called_once_with("password123", "hashed_password")
    mock_hasher.hash_password.assert_called_once_with("nueva_password")
    mock_uow.usuarios.save.assert_called_once()


@pytest.mark.asyncio
async def test_cambiar_contrasena_usuario_no_encontrado(usuario_servicio, mock_uow):
    # Arrange
    user_id = uuid.uuid4()
    mock_uow.usuarios.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(UsuarioNoEncontradoError):
        await usuario_servicio.cambiar_contrasena(
            user_id=user_id,
            contrasena_actual="password123",
            nueva_contrasena="nueva_password"
        )
    
    mock_uow.usuarios.get_by_id.assert_called_once_with(user_id)
    mock_uow.usuarios.save.assert_not_called()
    mock_uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_cambiar_contrasena_contrasena_actual_incorrecta(usuario_servicio, mock_uow, mock_usuario, mock_hasher):
    # Arrange
    mock_uow.usuarios.get_by_id.return_value = mock_usuario
    mock_hasher.verify_password.return_value = False
    
    # Act & Assert
    with pytest.raises(CredencialesInvalidasError):
        await usuario_servicio.cambiar_contrasena(
            user_id=mock_usuario.id,
            contrasena_actual="contrasena_incorrecta",
            nueva_contrasena="nueva_password"
        )
    
    mock_uow.usuarios.get_by_id.assert_called_once_with(mock_usuario.id)
    mock_hasher.verify_password.assert_called_once_with("contrasena_incorrecta", mock_usuario.hashed_pwd)
    mock_hasher.hash_password.assert_not_called()
    mock_uow.usuarios.save.assert_not_called()
