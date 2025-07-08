# app/core/deps.py
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# --- Core Imports ---
from app.core.seguridad.hashing import Hasher, PasslibHasher

# --- Domain Imports (Interfaces) ---
from app.dominio.repositorios.rol_repositorio import IRolRepositorio
from app.dominio.repositorios.usuario_repositorio import IUsuarioRepositorio

# --- Infrastructure Imports (Implementations & Session) ---
from app.infraestructura.persistencia.sesion import get_db_session
from app.infraestructura.persistencia.implementaciones_repositorios.rol_repositorio_impl import RolRepositorioImpl
from app.infraestructura.persistencia.implementaciones_repositorios.usuario_repositorio_impl import UsuarioRepositorioImpl

# --- Service Imports ---
from app.servicios.rol_servicio import RolServicio
from app.servicios.usuario_servicio import UsuarioServicio

# =================================================================
# DATABASE SESSION PROVIDER
# =================================================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia que proporciona una sesión de base de datos por solicitud.
    Reutiliza el generador de `sesion.py` y asegura que el ciclo de vida
    de la sesión (apertura, commit/rollback, cierre) se maneje correctamente.
    """
    async for session in get_db_session():
        yield session

# =================================================================
# CORE SERVICE PROVIDERS
# =================================================================
def get_hasher() -> Hasher:
    """
    Dependencia que proporciona una implementación concreta del Hasher.
    FastAPI cacheará el resultado para una misma solicitud.
    """
    return PasslibHasher()

# =================================================================
# REPOSITORY PROVIDERS
# =================================================================
def get_usuario_repositorio(db: AsyncSession = Depends(get_db)) -> IUsuarioRepositorio:
    """
    Dependencia que proporciona la implementación del repositorio de usuarios.
    Los endpoints dependerán de la interfaz (IUsuarioRepositorio), pero FastAPI
    inyectará la implementación concreta (UsuarioRepositorioImpl).
    """
    return UsuarioRepositorioImpl(db_session=db)

def get_rol_repositorio(db: AsyncSession = Depends(get_db)) -> IRolRepositorio:
    """
    Dependencia que proporciona la implementación del repositorio de roles.
    """
    return RolRepositorioImpl(db_session=db)

# =================================================================
# APPLICATION SERVICE PROVIDERS
# =================================================================
def get_usuario_servicio(
    repo: IUsuarioRepositorio = Depends(get_usuario_repositorio),
    hasher: Hasher = Depends(get_hasher),
) -> UsuarioServicio:
    """
    Dependencia que proporciona el servicio de aplicación de usuarios.
    Depende de la interfaz del repositorio de usuarios y del hasher.
    """
    return UsuarioServicio(usuario_repositorio=repo, hasher=hasher)

def get_rol_servicio(
    repo: IRolRepositorio = Depends(get_rol_repositorio),
) -> RolServicio:
    """
    Dependencia que proporciona el servicio de aplicación de roles.
    """
    return RolServicio(rol_repositorio=repo)