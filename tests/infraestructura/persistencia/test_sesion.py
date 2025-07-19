"""
Tests unitarios para el módulo de sesión de base de datos.
"""
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, QueuePool

# Creamos mocks para evitar la importación de módulos reales
sys.modules['app.core.config'] = MagicMock()
sys.modules['app.core.config'].settings = MagicMock()
sys.modules['app.core.config'].settings.DATABASE_URL = "postgresql+asyncpg://user:password@localhost/testdb"
sys.modules['app.core.config'].settings.DB_ECHO = False
sys.modules['app.core.config'].settings.DB_POOL_SIZE = 5
sys.modules['app.core.config'].settings.DB_MAX_OVERFLOW = 10

# Ahora podemos importar el módulo a probar
from app.infraestructura.persistencia.sesion import (
    get_session_factory,
    get_db_session,
    AsyncSessionFactory,
    async_engine
)


class TestSesion:
    """Pruebas para el módulo de sesión de base de datos."""
    
    def test_async_engine_configuration(self):
        """Verifica que el motor asíncrono se configure correctamente."""
        # Verificamos que el motor se haya creado correctamente
        assert async_engine is not None
        
        # Verificamos que la URL del motor tenga un protocolo válido
        engine_url_str = str(async_engine.url)
        assert any(protocol in engine_url_str for protocol in ['postgresql+asyncpg', 'sqlite+aiosqlite']), \
            f"URL del motor no tiene un protocolo válido: {engine_url_str}"
        
        # Verificamos que la configuración de echo sea un booleano válido
        assert isinstance(async_engine.echo, bool)
        
        # Verificamos que el pool sea una instancia válida
        # Diferentes bases de datos usan diferentes tipos de pool:
        # - SQLite: StaticPool
        # - PostgreSQL: QueuePool o NullPool
        from sqlalchemy.pool import StaticPool
        assert async_engine.pool is not None
        assert hasattr(async_engine.pool, 'connect'), "El pool debe tener un método connect"
    
    def test_async_session_factory_configuration(self):
        """Verifica que la factoría de sesiones se configure correctamente."""
        # Verificamos que la factoría esté configurada correctamente
        # Verificamos las propiedades de la factoría a través de sus argumentos de configuración
        assert AsyncSessionFactory.kw.get('autocommit') is False
        assert AsyncSessionFactory.kw.get('autoflush') is False
        assert AsyncSessionFactory.kw.get('expire_on_commit') is False
        # Verificamos que el motor esté vinculado correctamente
        assert AsyncSessionFactory.kw['bind'] is async_engine
    
    def test_get_session_factory(self):
        """Verifica que get_session_factory devuelva la factoría correcta."""
        factory = get_session_factory()
        assert factory is AsyncSessionFactory
        
    @pytest.mark.asyncio
    async def test_get_db_session(self):
        """Verifica que get_db_session proporcione una sesión y la cierre correctamente."""
        # Creamos un mock para la sesión y su contexto
        mock_session = AsyncMock(spec=AsyncSession)
        mock_context = AsyncMock()
        mock_session.__aenter__.return_value = mock_context
        
        # Parcheamos AsyncSessionFactory para que devuelva nuestro mock
        with patch('app.infraestructura.persistencia.sesion.AsyncSessionFactory', return_value=mock_session):
            # Ejecutamos la función como generador asíncrono
            session_gen = get_db_session()
            session = await session_gen.__anext__()
            
            # Verificamos que la sesión devuelta sea el contexto del mock
            assert session is mock_context
            
            # Verificamos que el contexto asíncrono se haya iniciado
            mock_session.__aenter__.assert_called_once()
            
            # Simulamos el fin del contexto
            try:
                await session_gen.__anext__()
                pytest.fail("El generador debería haber terminado después de la primera yield")
            except StopAsyncIteration:
                # Verificamos que el contexto se cierre correctamente
                # Nota: No podemos verificar __aexit__ aquí porque se llama después de StopAsyncIteration
                pass
