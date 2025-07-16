# app/core/deps.py
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# --- Core Imports ---
from app.core.seguridad.hashing import Hasher, PasslibHasher
from app.core.seguridad.jwt import JWTHandler
from app.core.seguridad.esquemas_oauth2 import oauth2_scheme

# --- Domain Imports (Interfaces & Entities) ---
from app.dominio.entidades.usuario import Usuario
from app.dominio.repositorios.rol_repositorio import IRolRepositorio
from app.dominio.repositorios.contacto_repositorio import IContactoRepositorio
from app.dominio.repositorios.usuario_repositorio import IUsuarioRepositorio
from app.dominio.interfaces.unit_of_work import IUnitOfWork
from app.dominio.interfaces.jwt_handler import IJWTHandler
from app.dominio.excepciones.dominio_excepciones import CredencialesInvalidasError, UsuarioNoEncontradoError

# --- Infrastructure Imports (Implementations & Session) ---
from app.infraestructura.persistencia.sesion import get_db_session, get_session_factory
from app.infraestructura.persistencia.implementaciones_repositorios.rol_repositorio_impl import RolRepositorioImpl
from app.infraestructura.persistencia.implementaciones_repositorios.contacto_repositorio_impl import ContactoRepositorioImpl
from app.infraestructura.persistencia.implementaciones_repositorios.usuario_repositorio_impl import UsuarioRepositorioImpl
from app.infraestructura.persistencia.unit_of_work import SQLAlchemyUnitOfWork

# --- Service Imports ---
from app.servicios.rol_servicio import RolServicio
from app.servicios.autenticacion_servicio import AutenticacionServicio
from app.servicios.contacto_servicio import ContactoServicio
from app.servicios.usuario_servicio import UsuarioServicio

# =================================================================
# ANNOTATED DEPENDENCIES
# =================================================================
DBSession = Annotated[AsyncSession, Depends(get_db_session)]
Token = Annotated[str, Depends(oauth2_scheme)]


# =================================================================
# CORE SERVICE PROVIDERS
# =================================================================
def get_hasher() -> Hasher:
    """
    Dependencia que proporciona una implementación concreta del Hasher.
    FastAPI cacheará el resultado para una misma solicitud.
    """
    return PasslibHasher()

def get_jwt_handler() -> IJWTHandler:
    """
    Dependencia que proporciona el manejador de JWT.
    FastAPI cacheará el resultado para una misma solicitud.
    
    Returns:
        IJWTHandler: Una instancia de la interfaz IJWTHandler, que permite
        crear y validar tokens JWT independientemente de la implementación.
    """
    return JWTHandler()

# =================================================================
# UNIT OF WORK & REPOSITORY PROVIDERS
# =================================================================
def get_unit_of_work() -> IUnitOfWork:
    """
    Dependencia que proporciona una instancia del Unit of Work.
    El UnitOfWork encapsula una sesión de SQLAlchemy y proporciona acceso
    a todos los repositorios, asegurando que todas las operaciones
    participen en la misma transacción.
    
    Returns:
        IUnitOfWork: Una instancia de la interfaz UnitOfWork, que permite
        realizar operaciones transaccionales atómicas con múltiples repositorios.
    """
    return SQLAlchemyUnitOfWork(get_session_factory())

# DEPRECATED: Estos proveedores de repositorios individuales se mantienen temporalmente
# para compatibilidad con código existente, pero se recomienda migrar a UnitOfWork.
# En el futuro, estos proveedores serán eliminados.
def get_usuario_repositorio(db: DBSession) -> IUsuarioRepositorio:
    """
    DEPRECATED: Utilice get_unit_of_work() en su lugar.
    
    Dependencia que proporciona la implementación del repositorio de usuarios.
    Los endpoints dependerán de la interfaz (IUsuarioRepositorio), pero FastAPI
    inyectará la implementación concreta (UsuarioRepositorioImpl).
    
    Advertencia: Este proveedor no garantiza la atomicidad transaccional cuando
    se realizan múltiples operaciones. Para operaciones que requieran transacciones
    atómicas, use get_unit_of_work() en su lugar.
    """
    return UsuarioRepositorioImpl(db_session=db)

def get_rol_repositorio(db: DBSession) -> IRolRepositorio:
    """
    DEPRECATED: Utilice get_unit_of_work() en su lugar.
    
    Dependencia que proporciona la implementación del repositorio de roles.
    
    Advertencia: Este proveedor no garantiza la atomicidad transaccional cuando
    se realizan múltiples operaciones. Para operaciones que requieran transacciones
    atómicas, use get_unit_of_work() en su lugar.
    """
    return RolRepositorioImpl(db_session=db)

def get_contacto_repositorio(db: DBSession) -> IContactoRepositorio:
    """
    DEPRECATED: Utilice get_unit_of_work() en su lugar.
    
    Dependencia que proporciona la implementación del repositorio de contactos.
    
    Advertencia: Este proveedor no garantiza la atomicidad transaccional cuando
    se realizan múltiples operaciones. Para operaciones que requieran transacciones
    atómicas, use get_unit_of_work() en su lugar.
    """
    return ContactoRepositorioImpl(db_session=db)


# =================================================================
# APPLICATION SERVICE PROVIDERS
# =================================================================
def get_usuario_servicio(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
    hasher: Annotated[Hasher, Depends(get_hasher)],
) -> UsuarioServicio:
    """
    Dependencia que proporciona el servicio de aplicación de usuarios.
    Utiliza el Unit of Work para acceder a los repositorios y gestionar transacciones.
    También depende del hasher para operaciones relacionadas con contraseñas.
    """
    return UsuarioServicio(uow=uow, hasher=hasher)

def get_rol_servicio(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
) -> RolServicio:
    """
    Dependencia que proporciona el servicio de aplicación de roles.
    Utiliza el Unit of Work para acceder a los repositorios y gestionar transacciones.
    """
    return RolServicio(uow=uow)

def get_contacto_servicio(
    uow: Annotated[IUnitOfWork, Depends(get_unit_of_work)],
) -> ContactoServicio:
    """
    Dependencia que proporciona el servicio de aplicación de contactos.
    Utiliza el Unit of Work para acceder a los repositorios y gestionar transacciones.
    """
    return ContactoServicio(uow=uow)

def get_autenticacion_servicio(
    usuario_servicio: Annotated[UsuarioServicio, Depends(get_usuario_servicio)],
    jwt_handler: Annotated[IJWTHandler, Depends(get_jwt_handler)],
) -> AutenticacionServicio:
    """
    Dependencia que proporciona el servicio de autenticación.
    """
    return AutenticacionServicio(usuario_servicio=usuario_servicio, jwt_handler=jwt_handler)


# =================================================================
# SECURITY DEPENDENCIES
# =================================================================
async def get_current_user(
    token: Token,
    usuario_servicio: Annotated[UsuarioServicio, Depends(get_usuario_servicio)],
    jwt_handler: Annotated[JWTHandler, Depends(get_jwt_handler)],
) -> Usuario:
    """
    Dependencia para obtener el usuario actual a partir de un token JWT.
    Esta es la función que protegerá tus endpoints y activará el botón "Authorize" en Swagger.
    """
    try:
        user_id = jwt_handler.get_user_id_from_token(token)
        # Asumimos que el servicio de usuario tiene un método para buscar por ID.
        # Este método debería lanzar UsuarioNoEncontradoError si no lo encuentra.
        usuario = await usuario_servicio.obtener_usuario_por_id(user_id)
        if not usuario.is_active:
            raise CredencialesInvalidasError("El usuario está inactivo.")
        return usuario
    except (CredencialesInvalidasError, UsuarioNoEncontradoError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"No se pudo validar las credenciales: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )