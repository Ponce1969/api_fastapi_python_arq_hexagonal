"""
Configuración específica para pruebas.
Este módulo proporciona una configuración alternativa para entornos de prueba.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    """
    Configuraciones para pruebas.
    Esta clase replica la estructura de Settings pero con valores predeterminados para pruebas.
    """
    # Configuración de la Base de Datos
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Configuración de JWT
    SECRET_KEY: str = "test_secret_key_for_testing_only"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Configuración de la Aplicación
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"

    # Configuración SMTP (opcional)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    
    # Configuración de la documentación de la API
    DOCS_USERNAME: str = "test"
    DOCS_PASSWORD: str = "test"
    DOCS_ENABLED: bool = True


# Instancia de configuración para pruebas
test_settings = TestSettings()
