# tests/aplicacion/servicios/test_rol_servicio.py
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional

from app.dominio.entidades.rol import Rol
from app.dominio.entidades.usuario import Usuario
from app.dominio.excepciones.dominio_excepciones import RolNoEncontradoError, RolYaExisteError, UsuarioNoEncontradoError
from app.dominio.interfaces.unit_of_work import IUnitOfWork
from app.servicios.rol_servicio import RolServicio


class MockUnitOfWork:
    """Mock de UnitOfWork para pruebas."""
    
    def __init__(self):
        self.roles = AsyncMock()
        self.usuarios = AsyncMock()
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self._is_committed = False
        self._is_rolled_back = False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
            self._is_rolled_back = True
        else:
            # Llamamos a commit automáticamente al salir del contexto sin excepciones
            await self.commit()
            self._is_committed = True
        return False


@pytest.fixture
def mock_uow():
    return MockUnitOfWork()


@pytest.fixture
def rol_servicio(mock_uow):
    return RolServicio(uow=mock_uow)


@pytest.fixture
def mock_rol():
    return Rol(
        id=uuid.uuid4(),
        name="admin",
        description="Rol de administrador"
    )


@pytest.fixture
def mock_usuario():
    return Usuario(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_pwd="hashed_password",
        full_name="Test User",
        is_active=True
    )


@pytest.mark.asyncio
async def test_crear_rol_exitoso(rol_servicio, mock_uow):
    # Arrange
    mock_uow.roles.get_by_name.return_value = None
    nuevo_rol = Rol(name="editor", description="Rol de editor")
    mock_uow.roles.save.return_value = nuevo_rol
    
    # Act
    resultado = await rol_servicio.crear_rol("editor", "Rol de editor")
    
    # Assert
    assert resultado == nuevo_rol
    mock_uow.roles.get_by_name.assert_called_once_with("editor")
    mock_uow.roles.save.assert_called_once()


@pytest.mark.asyncio
async def test_crear_rol_ya_existe(rol_servicio, mock_uow, mock_rol):
    # Arrange
    mock_uow.roles.get_by_name.return_value = mock_rol
    
    # Act & Assert
    with pytest.raises(RolYaExisteError):
        await rol_servicio.crear_rol("admin", "Rol de administrador")
    
    mock_uow.roles.get_by_name.assert_called_once_with("admin")
    mock_uow.roles.save.assert_not_called()


@pytest.mark.asyncio
async def test_obtener_rol_por_id_exitoso(rol_servicio, mock_uow, mock_rol):
    # Arrange
    mock_uow.roles.get_by_id.return_value = mock_rol
    
    # Act
    resultado = await rol_servicio.obtener_rol_por_id(mock_rol.id)
    
    # Assert
    assert resultado == mock_rol
    mock_uow.roles.get_by_id.assert_called_once_with(mock_rol.id)


@pytest.mark.asyncio
async def test_obtener_rol_por_id_no_encontrado(rol_servicio, mock_uow):
    # Arrange
    rol_id = uuid.uuid4()
    mock_uow.roles.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(RolNoEncontradoError):
        await rol_servicio.obtener_rol_por_id(rol_id)
    
    mock_uow.roles.get_by_id.assert_called_once_with(rol_id)


@pytest.mark.asyncio
async def test_obtener_todos_los_roles(rol_servicio, mock_uow, mock_rol):
    # Arrange
    roles = [mock_rol, Rol(name="editor", description="Rol de editor")]
    mock_uow.roles.get_all.return_value = roles
    
    # Act
    resultado = await rol_servicio.obtener_todos_los_roles()
    
    # Assert
    assert resultado == roles
    mock_uow.roles.get_all.assert_called_once()


@pytest.mark.asyncio
async def test_actualizar_rol_exitoso(rol_servicio, mock_uow, mock_rol):
    # Arrange
    mock_uow.roles.get_by_id.return_value = mock_rol
    mock_uow.roles.get_by_name.return_value = None
    mock_uow.roles.save.return_value = mock_rol
    
    # Act
    resultado = await rol_servicio.actualizar_rol(
        mock_rol.id, name="super_admin", description="Super Administrador"
    )
    
    # Assert
    assert resultado == mock_rol
    mock_uow.roles.get_by_id.assert_called_once_with(mock_rol.id)
    mock_uow.roles.get_by_name.assert_called_once_with("super_admin")
    mock_uow.roles.save.assert_called_once()


@pytest.mark.asyncio
async def test_actualizar_rol_nombre_existente(rol_servicio, mock_uow, mock_rol):
    # Arrange
    otro_rol = Rol(id=uuid.uuid4(), name="editor", description="Rol de editor")
    mock_uow.roles.get_by_id.return_value = mock_rol
    mock_uow.roles.get_by_name.return_value = otro_rol
    
    # Act & Assert
    with pytest.raises(RolYaExisteError):
        await rol_servicio.actualizar_rol(mock_rol.id, name="editor")
    
    mock_uow.roles.get_by_id.assert_called_once_with(mock_rol.id)
    mock_uow.roles.get_by_name.assert_called_once_with("editor")
    mock_uow.roles.save.assert_not_called()


@pytest.mark.asyncio
async def test_actualizar_rol_mismo_nombre(rol_servicio, mock_uow, mock_rol):
    # Arrange
    mock_uow.roles.get_by_id.return_value = mock_rol
    mock_uow.roles.save.return_value = mock_rol
    
    # Act - Actualizamos solo la descripción, manteniendo el mismo nombre
    resultado = await rol_servicio.actualizar_rol(
        mock_rol.id, name=mock_rol.name, description="Nueva descripción"
    )
    
    # Assert
    assert resultado == mock_rol
    mock_uow.roles.get_by_id.assert_called_once_with(mock_rol.id)
    # No se debe llamar a get_by_name cuando el nombre no cambia
    mock_uow.roles.get_by_name.assert_not_called()
    mock_uow.roles.save.assert_called_once()


@pytest.mark.asyncio
async def test_actualizar_rol_no_encontrado(rol_servicio, mock_uow):
    # Arrange
    rol_id = uuid.uuid4()
    mock_uow.roles.get_by_id.return_value = None  # Rol no encontrado
    
    # Act & Assert
    with pytest.raises(RolNoEncontradoError):
        await rol_servicio.actualizar_rol(rol_id, name="nuevo_nombre")
    
    mock_uow.roles.get_by_id.assert_called_once_with(rol_id)
    mock_uow.roles.get_by_name.assert_not_called()
    mock_uow.roles.save.assert_not_called()


@pytest.mark.asyncio
async def test_eliminar_rol_exitoso(rol_servicio, mock_uow, mock_rol):
    # Arrange
    mock_uow.roles.get_by_id.return_value = mock_rol
    
    # Act
    await rol_servicio.eliminar_rol(mock_rol.id)
    
    # Assert
    mock_uow.roles.get_by_id.assert_called_once_with(mock_rol.id)
    mock_uow.roles.delete.assert_called_once_with(mock_rol.id)


@pytest.mark.asyncio
async def test_eliminar_rol_no_encontrado(rol_servicio, mock_uow):
    # Arrange
    rol_id = uuid.uuid4()
    mock_uow.roles.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(RolNoEncontradoError):
        await rol_servicio.eliminar_rol(rol_id)
    
    mock_uow.roles.get_by_id.assert_called_once_with(rol_id)
    mock_uow.roles.delete.assert_not_called()


@pytest.mark.asyncio
async def test_asignar_rol_a_usuario_exitoso(rol_servicio, mock_uow, mock_rol, mock_usuario):
    # Arrange
    mock_uow.roles.get_by_id.return_value = mock_rol
    mock_uow.usuarios.get_by_id.return_value = mock_usuario
    
    # Act
    usuario, rol = await rol_servicio.asignar_rol_a_usuario(mock_usuario.id, mock_rol.id)
    
    # Assert
    assert usuario == mock_usuario
    assert rol == mock_rol
    mock_uow.roles.get_by_id.assert_called_with(mock_rol.id)
    mock_uow.usuarios.get_by_id.assert_called_with(mock_usuario.id)
    mock_uow.usuarios.asignar_rol.assert_called_once_with(mock_usuario.id, mock_rol.id)


@pytest.mark.asyncio
async def test_asignar_rol_a_usuario_rol_no_encontrado(rol_servicio, mock_uow, mock_usuario):
    # Arrange
    rol_id = uuid.uuid4()
    mock_uow.roles.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(RolNoEncontradoError):
        await rol_servicio.asignar_rol_a_usuario(mock_usuario.id, rol_id)
    
    mock_uow.roles.get_by_id.assert_called_once_with(rol_id)
    mock_uow.usuarios.get_by_id.assert_not_called()
    mock_uow.usuarios.asignar_rol.assert_not_called()


@pytest.mark.asyncio
async def test_asignar_rol_a_usuario_usuario_no_encontrado(rol_servicio, mock_uow, mock_rol):
    # Arrange
    usuario_id = uuid.uuid4()
    mock_uow.roles.get_by_id.return_value = mock_rol
    mock_uow.usuarios.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(UsuarioNoEncontradoError):
        await rol_servicio.asignar_rol_a_usuario(usuario_id, mock_rol.id)
    
    mock_uow.roles.get_by_id.assert_called_once_with(mock_rol.id)
    mock_uow.usuarios.get_by_id.assert_called_once_with(usuario_id)
    mock_uow.usuarios.asignar_rol.assert_not_called()


@pytest.mark.asyncio
async def test_remover_rol_de_usuario_exitoso(rol_servicio, mock_uow, mock_rol, mock_usuario):
    # Arrange
    mock_uow.roles.get_by_id.return_value = mock_rol
    mock_uow.usuarios.get_by_id.return_value = mock_usuario
    
    # Act
    usuario, rol = await rol_servicio.remover_rol_de_usuario(mock_usuario.id, mock_rol.id)
    
    # Assert
    assert usuario == mock_usuario
    assert rol == mock_rol
    mock_uow.roles.get_by_id.assert_called_with(mock_rol.id)
    mock_uow.usuarios.get_by_id.assert_called_with(mock_usuario.id)
    mock_uow.usuarios.remover_rol.assert_called_once_with(mock_usuario.id, mock_rol.id)


@pytest.mark.asyncio
async def test_remover_rol_de_usuario_rol_no_encontrado(rol_servicio, mock_uow, mock_usuario):
    # Arrange
    rol_id = uuid.uuid4()
    mock_uow.roles.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(RolNoEncontradoError):
        await rol_servicio.remover_rol_de_usuario(mock_usuario.id, rol_id)
    
    mock_uow.roles.get_by_id.assert_called_once_with(rol_id)
    mock_uow.usuarios.get_by_id.assert_not_called()
    mock_uow.usuarios.remover_rol.assert_not_called()


@pytest.mark.asyncio
async def test_remover_rol_de_usuario_usuario_no_encontrado(rol_servicio, mock_uow, mock_rol):
    # Arrange
    usuario_id = uuid.uuid4()
    mock_uow.roles.get_by_id.return_value = mock_rol
    mock_uow.usuarios.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(UsuarioNoEncontradoError):
        await rol_servicio.remover_rol_de_usuario(usuario_id, mock_rol.id)
    
    mock_uow.roles.get_by_id.assert_called_once_with(mock_rol.id)
    mock_uow.usuarios.get_by_id.assert_called_once_with(usuario_id)
    mock_uow.usuarios.remover_rol.assert_not_called()
