# app/infraestructura/persistencia/sesion.py
from typing import AsyncGenerator, Callable
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings # Importamos la configuración de la aplicación

# --- Configuración del Motor de la Base de Datos Asíncrono ---
# El motor de SQLAlchemy es la interfaz principal con la base de datos.
# Usamos create_async_engine para soporte asíncrono.
# El driver `asyncpg` es el recomendado para FastAPI y PostgreSQL.
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO, # Muestra las consultas SQL en la consola (útil para depuración)
    pool_size=settings.DB_POOL_SIZE, # Número de conexiones persistentes en el pool
    max_overflow=settings.DB_MAX_OVERFLOW, # Conexiones adicionales que pueden crearse más allá de pool_size
    pool_pre_ping=True, # Verifica si las conexiones están vivas antes de usarlas
    # Usa NullPool si el pooling es manejado externamente (ej. PgBouncer) o en entornos serverless.
    # De lo contrario, SQLAlchemy usará un QueuePool por defecto, que es ideal para la mayoría de las aplicaciones.
    poolclass=NullPool if settings.DB_POOL_SIZE == 0 else None,
)

# --- Configuración de la Factoría de Sesiones Asíncronas ---
# async_sessionmaker es una factoría para crear nuevas instancias de AsyncSession.
AsyncSessionFactory = async_sessionmaker(
    autocommit=False, # No hacer commit automáticamente después de cada operación
    autoflush=False, # No hacer flush automáticamente antes de cada consulta
    bind=async_engine, # Vincula esta factoría al motor de la base de datos
    class_=AsyncSession, # Especifica que el tipo de sesión a crear es AsyncSession
    # expire_on_commit=False: Evita que los objetos se 'expiren' después de un commit.
    # Esto permite que las entidades sigan siendo accesibles en otras partes del código
    # después de que la sesión se haya cerrado, lo cual es útil para los DTOs.
    expire_on_commit=False,
)

# Alias para compatibilidad con código existente
AsyncSessionLocal = AsyncSessionFactory

# --- Función para obtener la fábrica de sesiones ---
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Proporciona la fábrica de sesiones para crear nuevas instancias de AsyncSession.
    Esta función es útil para patrones como Unit of Work que necesitan crear
    sus propias sesiones bajo demanda.
    
    Returns:
        async_sessionmaker: La fábrica de sesiones configurada para la aplicación.
    """
    return AsyncSessionFactory

# --- Dependencia para Obtener una Sesión de Base de Datos ---
# Esta función es un "generador de dependencias" que FastAPI utilizará.
# Asegura que cada solicitud HTTP obtenga su propia sesión de DB,
# y que la sesión se cierre correctamente después de que la solicitud haya sido procesada.
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Proporciona una sesión de base de datos asíncrona para inyección de dependencias.
    Asegura que la sesión se cierre correctamente después de su uso.
    El `async with` se encarga de abrir la sesión, manejar errores (con rollback) y cerrarla.
    
    Nota: Para patrones como Unit of Work que necesitan crear sus propias sesiones,
    utilice get_session_factory() en su lugar.
    """
    async with AsyncSessionFactory() as session:
        yield session