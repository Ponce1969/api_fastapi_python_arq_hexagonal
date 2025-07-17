"""
Manejador global de excepciones para FastAPI.

Este módulo contiene funciones para registrar manejadores de excepciones
en una aplicación FastAPI, traduciendo excepciones de dominio a respuestas
HTTP apropiadas.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import logging

from app.dominio.excepciones.dominio_excepciones import (
    DominioExcepcion,
    PersistenciaError,
    ConexionDBError,
    TimeoutDBError,
    PermisosDBError,
    ClaveForaneaError,
    RestriccionCheckError,
    EmailInvalidoError,
    EmailYaRegistradoError,
    UsuarioNoEncontradoError,
    CredencialesInvalidasError,
    RolNoEncontradoError,
    RolYaExisteError,
    ContactoNoEncontradoError,
    EntidadNoEncontradaError
)

# Configuración del logger
logger = logging.getLogger(__name__)


def registrar_manejadores_excepciones(app: FastAPI) -> None:
    """
    Registra todos los manejadores de excepciones en la aplicación FastAPI.

    Args:
        app: Instancia de FastAPI donde se registrarán los manejadores.
    """
    # Manejador para excepciones de entidad no encontrada (404)
    @app.exception_handler(EntidadNoEncontradaError)
    @app.exception_handler(UsuarioNoEncontradoError)
    @app.exception_handler(RolNoEncontradoError)
    @app.exception_handler(ContactoNoEncontradoError)
    async def entidad_no_encontrada_handler(request: Request, exc: DominioExcepcion):
        """
        Maneja excepciones de entidades no encontradas y las convierte en respuestas HTTP 404.
        """
        logger.warning(f"Entidad no encontrada: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    # Manejador para excepciones de autenticación (401)
    @app.exception_handler(CredencialesInvalidasError)
    async def credenciales_invalidas_handler(request: Request, exc: CredencialesInvalidasError):
        """
        Maneja excepciones de credenciales inválidas y las convierte en respuestas HTTP 401.
        """
        logger.warning(f"Credenciales inválidas: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
        )

    # Manejador para excepciones de validación de datos (422)
    @app.exception_handler(EmailInvalidoError)
    @app.exception_handler(RestriccionCheckError)
    async def validacion_datos_handler(request: Request, exc: DominioExcepcion):
        """
        Maneja excepciones de validación de datos y las convierte en respuestas HTTP 422.
        """
        logger.warning(f"Error de validación: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )

    # Manejador para excepciones de conflicto (409)
    @app.exception_handler(EmailYaRegistradoError)
    @app.exception_handler(RolYaExisteError)
    async def conflicto_handler(request: Request, exc: DominioExcepcion):
        """
        Maneja excepciones de conflicto (recursos duplicados) y las convierte en respuestas HTTP 409.
        """
        logger.warning(f"Conflicto de recursos: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    # Manejador para excepciones de permisos (403)
    @app.exception_handler(PermisosDBError)
    async def permisos_handler(request: Request, exc: PermisosDBError):
        """
        Maneja excepciones de permisos y las convierte en respuestas HTTP 403.
        """
        logger.warning(f"Error de permisos: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc)},
        )

    # Manejador para excepciones de clave foránea (400)
    @app.exception_handler(ClaveForaneaError)
    async def clave_foranea_handler(request: Request, exc: ClaveForaneaError):
        """
        Maneja excepciones de clave foránea y las convierte en respuestas HTTP 400.
        """
        logger.warning(f"Error de clave foránea: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    # Manejador para excepciones de timeout (504)
    @app.exception_handler(TimeoutDBError)
    async def timeout_handler(request: Request, exc: TimeoutDBError):
        """
        Maneja excepciones de timeout y las convierte en respuestas HTTP 504.
        """
        logger.warning(f"Error de timeout: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={"detail": str(exc)},
        )

    # Manejador para excepciones de conexión (503)
    @app.exception_handler(ConexionDBError)
    async def conexion_handler(request: Request, exc: ConexionDBError):
        """
        Maneja excepciones de conexión y las convierte en respuestas HTTP 503.
        """
        logger.warning(f"Error de conexión: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(exc)},
        )

    # Manejador genérico para otras excepciones de persistencia (500)
    @app.exception_handler(PersistenciaError)
    async def persistencia_handler(request: Request, exc: PersistenciaError):
        """
        Maneja otras excepciones de persistencia y las convierte en respuestas HTTP 500.
        """
        logger.error(f"Error de persistencia: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )

    # Manejador genérico para otras excepciones de dominio (400)
    @app.exception_handler(DominioExcepcion)
    async def dominio_exception_handler(request: Request, exc: DominioExcepcion):
        """
        Maneja otras excepciones de dominio y las convierte en respuestas HTTP 400.
        """
        logger.warning(f"Excepción de dominio: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )

    # Manejador para excepciones no capturadas (500)
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """
        Maneja excepciones no capturadas y las convierte en respuestas HTTP 500.
        """
        logger.error(f"Error no manejado: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Error interno del servidor"},
        )
