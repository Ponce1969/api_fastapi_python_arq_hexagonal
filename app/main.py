# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging # Importa el módulo de logging
from fastapi.middleware.cors import CORSMiddleware # Para configurar CORS (si lo necesitas)

from app.core.config import settings # Importa tus configuraciones
from app.api.v2.api import api_router # Importa el router principal de la v2 de tu API

def create_app() -> FastAPI:
    """
    Crea y configura la instancia de la aplicación FastAPI.
    """
    # Configuración básica del logger
    logging.basicConfig(level=settings.LOG_LEVEL)
    logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manejador del ciclo de vida de la aplicación."""
        logger.info("La aplicación está arrancando…")
        # TODO: inicializar recursos (e.g., conexión a la base de datos)
        yield
        logger.info("La aplicación se está apagando…")
        # TODO: liberar recursos (e.g., cerrar conexiones)

    app = FastAPI(
        title="Mi Aplicación con Arquitectura Hexagonal",  # Título para la documentación de OpenAPI
        description="Una API RESTful construida con FastAPI y Arquitectura Hexagonal.",
        version="2.0.0",
        debug=settings.DEBUG,  # Controla el modo debug basado en la configuración
        lifespan=lifespan,
    )

    # Configuración de CORS (Cross-Origin Resource Sharing)
    # Permite que tu frontend (ej. React, Angular, Vue) pueda comunicarse con tu API
    # Ajusta origins según tus necesidades de producción. '*' permite cualquier origen.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # Puedes especificar dominios como ["http://localhost:3000", "https://tudominio.com"]
        allow_credentials=True,
        allow_methods=["*"], # Permite todos los métodos (GET, POST, PUT, DELETE, etc.)
        allow_headers=["*"], # Permite todos los encabezados
    )

    # Incluir los routers de la API
    # api_router ya incluye todos los routers de la v2 (auth, etc.)
    app.include_router(api_router, prefix="/api/v2")

    # Puedes añadir más configuraciones, eventos de inicio/apagado, etc. aquí



    return app

# Crea la instancia de la aplicación
app = create_app()

# Para ejecutar la aplicación, usarías un servidor ASGI como Uvicorn:
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000