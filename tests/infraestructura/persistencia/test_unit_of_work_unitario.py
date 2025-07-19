"""
Pruebas unitarias para el patrón Unit of Work.

Este módulo contiene pruebas unitarias que verifican el comportamiento del
Unit of Work en diferentes escenarios, incluyendo el manejo de excepciones
durante commit/rollback, el método begin() y el cierre de sesión.
"""
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.dominio.excepciones.dominio_excepciones import (
    DominioExcepcion,
    PersistenciaError,
    TimeoutDBError
)
from app.infraestructura.persistencia.unit_of_work import SQLAlchemyUnitOfWork
from app.infraestructura.persistencia.excepciones.persistencia_excepciones import ExcepcionesMapper


@pytest_asyncio.fixture
async def mock_session_factory():
    """Crea un mock de la factoría de sesiones para pruebas unitarias."""
    mock_session = AsyncMock(spec=AsyncSession)
    
    # Configurar el comportamiento del mock de la sesión
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    
    # Mock de la factoría que devuelve el mock de la sesión
    mock_factory = MagicMock()
    mock_factory.return_value = mock_session
    
    return mock_factory, mock_session


@pytest.mark.asyncio
async def test_begin_method(mock_session_factory):
    """Prueba el método begin() que proporciona acceso directo a la sesión."""
    mock_factory, mock_session = mock_session_factory
    
    # Crear UnitOfWork con el mock de la factoría
    uow = SQLAlchemyUnitOfWork(mock_factory)
    
    # Entrar al contexto del UnitOfWork
    async with uow:
        # Usar el método begin() para obtener acceso directo a la sesión
        async with uow.begin() as session:
            # Verificar que la sesión devuelta es la misma que la del UnitOfWork
            assert session is mock_session
            
            # Simular alguna operación con la sesión
            await session.execute("SELECT 1")
            
            # Verificar que se llamó a execute en la sesión
            mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_begin_method_error_handling(mock_session_factory):
    """Prueba el manejo de errores en el método begin()."""
    mock_factory, mock_session = mock_session_factory
    
    # Configurar el mock para lanzar una excepción
    mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Error de SQL"))
    
    # Crear UnitOfWork con el mock de la factoría
    uow = SQLAlchemyUnitOfWork(mock_factory)
    
    # Entrar al contexto del UnitOfWork
    async with uow:
        # Usar el método begin() y verificar que la excepción se mapea correctamente
        with pytest.raises(DominioExcepcion) as excinfo:
            async with uow.begin() as session:
                await session.execute("SELECT 1")
        
        # Verificar que la excepción es del tipo correcto
        assert isinstance(excinfo.value, PersistenciaError)


@pytest.mark.asyncio
async def test_begin_method_without_context(mock_session_factory):
    """Prueba que begin() lanza una excepción si se llama fuera del contexto principal."""
    mock_factory, _ = mock_session_factory
    
    # Crear UnitOfWork con el mock de la factoría
    uow = SQLAlchemyUnitOfWork(mock_factory)
    
    # Intentar usar begin() fuera del contexto del UnitOfWork
    with pytest.raises(RuntimeError) as excinfo:
        async with uow.begin():
            pass
    
    # Verificar el mensaje de error
    assert "Cannot begin transaction on a UnitOfWork not yet entered" in str(excinfo.value)


@pytest.mark.asyncio
async def test_exception_during_commit(mock_session_factory):
    """Prueba el manejo de excepciones durante el commit."""
    mock_factory, mock_session = mock_session_factory
    
    # Configurar el mock para lanzar una excepción durante el commit
    mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Error durante commit"))
    
    # Crear UnitOfWork con el mock de la factoría
    uow = SQLAlchemyUnitOfWork(mock_factory)
    
    # Entrar al contexto del UnitOfWork y verificar que la excepción se mapea correctamente
    with pytest.raises(DominioExcepcion) as excinfo:
        async with uow:
            # No hacemos nada, solo queremos probar el commit al salir del contexto
            pass
    
    # Verificar que la excepción es del tipo correcto
    assert isinstance(excinfo.value, PersistenciaError)
    
    # Verificar que se intentó hacer commit
    mock_session.commit.assert_called_once()
    
    # Verificar que la sesión se cerró correctamente a pesar del error
    mock_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_exception_during_rollback(mock_session_factory):
    """Prueba el manejo de excepciones durante el rollback."""
    mock_factory, mock_session = mock_session_factory
    
    # Configurar el mock para lanzar una excepción durante el rollback
    mock_session.rollback = AsyncMock(side_effect=SQLAlchemyError("Error durante rollback"))
    
    # Crear UnitOfWork con el mock de la factoría
    uow = SQLAlchemyUnitOfWork(mock_factory)
    
    # Lanzar una excepción dentro del contexto para forzar un rollback
    original_exception = ValueError("Excepción original")
    
    with pytest.raises(DominioExcepcion) as excinfo:
        async with uow:
            raise original_exception
    
    # Verificar que la excepción es del tipo correcto (la excepción del rollback, no la original)
    assert isinstance(excinfo.value, PersistenciaError)
    assert "Error durante rollback" in str(excinfo.value)
    
    # Verificar que se intentó hacer rollback
    mock_session.rollback.assert_called_once()
    
    # Verificar que la sesión se cerró correctamente a pesar del error
    mock_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_session_cleanup_on_error(mock_session_factory):
    """Prueba que la sesión se limpia correctamente incluso cuando hay errores."""
    mock_factory, mock_session = mock_session_factory
    
    # Crear UnitOfWork con el mock de la factoría
    uow = SQLAlchemyUnitOfWork(mock_factory)
    
    # Simular una excepción dentro del contexto
    try:
        async with uow:
            raise ValueError("Error simulado")
    except Exception:
        pass  # Ignoramos la excepción para verificar la limpieza
    
    # Verificar que la sesión se cerró
    mock_session.close.assert_called_once()
    
    # Verificar que los repositorios se limpiaron (son None)
    assert uow.session is None
    assert uow.usuarios is None
    assert uow.roles is None
    assert uow.contactos is None


@pytest.mark.asyncio
async def test_multiple_repositories_interaction(mock_session_factory):
    """Prueba la interacción entre múltiples repositorios en una misma transacción."""
    mock_factory, mock_session = mock_session_factory
    
    # Crear UnitOfWork con el mock de la factoría
    uow = SQLAlchemyUnitOfWork(mock_factory)
    
    # Entrar al contexto del UnitOfWork para inicializar los repositorios
    async with uow:
        # Reemplazar los repositorios con mocks después de que se hayan inicializado
        uow.usuarios = AsyncMock()
        uow.roles = AsyncMock()
        
        # Configurar los mocks
        uow.usuarios.get_by_id = AsyncMock(return_value={"id": 1, "name": "Test User"})
        uow.roles.get_by_id = AsyncMock(return_value={"id": 1, "name": "Admin"})
        
        # Usar ambos repositorios en la misma transacción
        usuario = await uow.usuarios.get_by_id(1)
        rol = await uow.roles.get_by_id(1)
        
        # Verificar que se obtuvieron los valores esperados
        assert usuario["name"] == "Test User"
        assert rol["name"] == "Admin"
        
        # Verificar que se llamaron los métodos correctos
        uow.usuarios.get_by_id.assert_called_once_with(1)
        uow.roles.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_timeout_handling_in_unit_of_work(mock_session_factory):
    """Prueba el manejo de timeouts dentro del UnitOfWork."""
    mock_factory, mock_session = mock_session_factory
    
    # Crear UnitOfWork con el mock de la factoría
    uow = SQLAlchemyUnitOfWork(mock_factory)
    
    # Crear un mock para ExcepcionesMapper.wrap_exception
    with patch('app.infraestructura.persistencia.excepciones.persistencia_excepciones.ExcepcionesMapper.wrap_exception') as mock_wrap:
        # Configurar el mock para devolver una excepción de TimeoutDBError
        mock_wrap.return_value = TimeoutDBError("Tiempo límite de operación excedido")
        
        # Simular un timeout durante el commit
        mock_session.commit = AsyncMock(side_effect=asyncio.TimeoutError("Operación excedió el tiempo límite"))
        
        # Verificar que el timeout se traduce a la excepción de dominio correcta
        with pytest.raises(TimeoutDBError) as excinfo:
            async with uow:
                # No hacemos nada, solo queremos probar el commit al salir del contexto
                pass
        
        # Verificar que la excepción contiene el mensaje correcto
        assert "tiempo límite" in str(excinfo.value).lower() or "timeout" in str(excinfo.value).lower()
        
        # Verificar que se intentó hacer commit
        mock_session.commit.assert_called_once()
        
        # Verificar que la sesión se cerró correctamente a pesar del error
        mock_session.close.assert_called_once()
        
        # Verificar que se llamó al método wrap_exception
        mock_wrap.assert_called_once()
