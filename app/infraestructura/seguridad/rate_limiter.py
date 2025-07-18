"""
Módulo para la configuración y gestión del rate limiting (limitación de tasa).

Este módulo proporciona funciones para inicializar y configurar el limitador de tasa
utilizando fastapi-limiter con Redis como backend. También incluye decoradores
personalizados para aplicar diferentes políticas de limitación según las necesidades.
"""
from fastapi import FastAPI, Request, HTTPException, status
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
import logging
from typing import Optional, Callable
import functools

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configuración por defecto para rate limiting
DEFAULT_RATE_LIMIT = "100/minute"  # Límite por defecto: 100 solicitudes por minuto
AUTH_RATE_LIMIT = "20/minute"      # Límite para endpoints de autenticación: 20 por minuto
SENSITIVE_RATE_LIMIT = "50/minute"  # Límite para endpoints sensibles: 50 por minuto

# Variable global para almacenar la conexión a Redis
redis_client: Optional[redis.Redis] = None

async def setup_rate_limiter(app: FastAPI) -> None:
    """
    Configura e inicializa el limitador de tasa con Redis.
    
    Args:
        app: Instancia de FastAPI
    """
    global redis_client
    
    # Verificar si la configuración de Redis está disponible
    redis_url = getattr(settings, "REDIS_URL", None)
    if not redis_url:
        logger.warning("REDIS_URL no está configurado. Rate limiting desactivado.")
        return
    
    try:
        # Inicializar cliente Redis
        redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Probar conexión
        await redis_client.ping()
        
        # Inicializar FastAPILimiter
        await FastAPILimiter.init(redis_client)
        
        logger.info("Rate limiter inicializado correctamente con Redis.")
    except Exception as e:
        logger.error(f"Error al inicializar rate limiter: {e}", exc_info=True)
        # No lanzamos excepción para permitir que la aplicación inicie sin rate limiting
        # si Redis no está disponible

async def close_rate_limiter() -> None:
    """
    Cierra la conexión con Redis al detener la aplicación.
    """
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Conexión con Redis cerrada.")

def rate_limit(limit: str = DEFAULT_RATE_LIMIT):
    """
    Decorador personalizado para aplicar rate limiting a endpoints específicos.
    
    Args:
        limit: Cadena que define el límite de tasa en formato "{número}/{unidad}"
              Ejemplos: "5/second", "10/minute", "100/hour", "1000/day"
    
    Returns:
        Un decorador que aplica el límite de tasa especificado
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Si el rate limiter no está inicializado, simplemente ejecutamos la función
            if not hasattr(FastAPILimiter, "redis"):
                return await func(*args, **kwargs)
            
            # Extraer la solicitud de los argumentos
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                for _, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                        break
            
            if not request:
                logger.warning("No se encontró objeto Request para aplicar rate limiting")
                return await func(*args, **kwargs)
            
            # Aplicar limitación de tasa
            key = f"{request.client.host}:{request.url.path}"
            
            # Verificar si el cliente ha excedido el límite
            is_limited = await check_rate_limit(key, limit)
            if is_limited:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Demasiadas solicitudes. Por favor, intente más tarde."
                )
            
            # Ejecutar la función original
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

async def check_rate_limit(key: str, limit: str) -> bool:
    """
    Verifica si una clave ha excedido su límite de tasa.
    
    Args:
        key: Clave única para identificar al cliente
        limit: Límite de tasa en formato "{número}/{unidad}"
    
    Returns:
        True si el límite ha sido excedido, False en caso contrario
    """
    if not redis_client:
        return False
    
    # Parsear el límite
    count, period = limit.split("/")
    count = int(count)
    
    # Convertir periodo a segundos
    seconds = {
        "second": 1,
        "minute": 60,
        "hour": 3600,
        "day": 86400
    }
    period_seconds = seconds.get(period.lower(), 60)  # Default a 1 minuto
    
    # Incrementar contador
    current = await redis_client.incr(key)
    
    # Si es la primera solicitud para esta clave, establecer tiempo de expiración
    if current == 1:
        await redis_client.expire(key, period_seconds)
    
    # Verificar si se ha excedido el límite
    return current > count
