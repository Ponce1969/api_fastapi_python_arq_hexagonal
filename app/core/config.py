# app/core/config.py
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuraciones de la aplicación cargadas desde variables de entorno.
    Utiliza pydantic-settings para validar y gestionar la configuración.
    """
    # Carga las variables desde un archivo .env si existe.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Configuración de la Base de Datos (leída desde DATABASE_URL en .env)
    DATABASE_URL: str
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Configuración de JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Configuración de la Aplicación
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Configuración SMTP (opcional)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    
    # Configuración de la documentación de la API
    DOCS_USERNAME: str  # Debe definirse en .env
    DOCS_PASSWORD: str  # Debe definirse en .env
    DOCS_ENABLED: bool = True
    
    # Configuración de Redis para rate limiting
    REDIS_URL: Optional[str] = None  # Debe definirse en .env si se habilita rate limiting
    RATE_LIMITING_ENABLED: bool = False  # Por defecto desactivado, activar en .env

# Instancia única de la configuración que será importada en otros módulos.
settings = Settings()