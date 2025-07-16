# app/main.py
from fastapi import FastAPI, Request, status, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from contextlib import asynccontextmanager
import logging
import time
import secrets
from typing import Callable, Optional

from app.core.config import settings
from app.api.v2.api import api_router
from app.dominio.excepciones.dominio_excepciones import DominioExcepcion
from app.infraestructura.persistencia.sesion import async_engine
from app.infraestructura.persistencia.modelos_orm import Base

# Configuración del logger
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manejador del ciclo de vida de la aplicación.
    
    Se ejecuta al iniciar y detener la aplicación, permitiendo inicializar
    y liberar recursos como conexiones a bases de datos, colas, etc.
    """
    # Inicialización de recursos
    logger.info("Iniciando la aplicación...")
    
    # Inicializar la base de datos (si es necesario)
    try:
        # Crear tablas si no existen (útil para desarrollo)
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Tablas de la base de datos verificadas/creadas.")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}", exc_info=True)
        # Dependiendo de tu estrategia, podrías querer que la aplicación no arranque si la DB falla

    # Inicializar otros recursos (cache, servicios externos, etc.)
    
    yield  # La aplicación se ejecuta aquí
    
    # Limpieza de recursos
    logger.info("Cerrando la aplicación...")
    # Si necesitas cerrar el pool de conexiones explícitamente:
    # await async_engine.dispose()

def add_exception_handlers(app: FastAPI) -> None:
    """
    Configura los manejadores de excepciones globales para la aplicación.
    """
    @app.exception_handler(DominioExcepcion)
    async def dominio_exception_handler(request: Request, exc: DominioExcepcion):
        """
        Maneja excepciones de dominio y las convierte en respuestas HTTP apropiadas.
        """
        logger.warning(f"Excepción de dominio: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,  # O el código HTTP apropiado según el tipo de DominioExcepcion
            content={"detail": str(exc)},
        )
    
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

def add_middlewares(app: FastAPI) -> None:
    """
    Configura los middlewares para la aplicación.
    """
    # Middleware de CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Permitir todos los orígenes, ajustar según necesidades
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Middleware de logging para peticiones
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.debug(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
        return response

# Configuración de seguridad para la documentación
security = HTTPBasic()

def get_docs_credentials() -> tuple[str, str]:
    """
    Obtiene las credenciales para acceder a la documentación de la API.
    """
    return settings.DOCS_USERNAME, settings.DOCS_PASSWORD

def verify_docs_access(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """
    Verifica las credenciales para acceder a la documentación de la API.
    """
    username, password = get_docs_credentials()
    correct_username = secrets.compare_digest(credentials.username, username)
    correct_password = secrets.compare_digest(credentials.password, password)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso no autorizado a la documentación",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

def create_app() -> FastAPI:
    """
    Crea y configura la instancia de la aplicación FastAPI.
    """
    # Determinar si la documentación debe estar habilitada y cómo
    docs_url = None
    redoc_url = None
    openapi_url = "/api/openapi.json" if settings.DOCS_ENABLED else None
    
    app = FastAPI(
        title="API de Arquitectura Hexagonal",
        description="API statica con base en arquitectura hexagonal",
        version="2.0.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )
    
    # Configurar manejadores de excepciones
    add_exception_handlers(app)
    
    # Configurar middlewares
    add_middlewares(app)
    
    # Incluir routers
    app.include_router(api_router, prefix="/api/v2")
    
    # Endpoint de healthcheck
    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "ok", "version": "2.0.0"}
    
    # Rutas personalizadas para la documentación con autenticación
    if settings.DOCS_ENABLED:
        @app.get("/api/docs", include_in_schema=False)
        async def custom_swagger_ui_html(authenticated: bool = Depends(verify_docs_access)):
            return get_swagger_ui_html(
                openapi_url="/api/openapi.json",
                title="API Documentation - Swagger UI",
                swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
                swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            )
        
        @app.get("/api/redoc", include_in_schema=False)
        async def custom_redoc_html(authenticated: bool = Depends(verify_docs_access)):
            return get_redoc_html(
                openapi_url="/api/openapi.json",
                title="API Documentation - ReDoc",
                redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
            )
    
    return app

# Instancia de la aplicación para ser importada por el servidor ASGI
app = create_app()
