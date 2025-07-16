"""
Interfaz para el manejador de JSON Web Tokens (JWT).

Este módulo define la interfaz IJWTHandler que establece el contrato
que deben cumplir todas las implementaciones de manejadores de JWT.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.esquemas.token import TokenPayload

class IJWTHandler(ABC):
    """
    Interfaz para el manejador de JSON Web Tokens (JWT).
    Define el contrato que deben cumplir todas las implementaciones
    de manejadores de JWT.
    """
    
    @abstractmethod
    def create_access_token(self, subject: UUID, expires_delta: Optional[int] = None) -> str:
        """
        Crea un token de acceso JWT.
        
        Args:
            subject: ID del usuario para el cual se crea el token.
            expires_delta: Tiempo de expiración en minutos (opcional).
            
        Returns:
            Token JWT codificado como string.
        """
        pass
    
    @abstractmethod
    def decode_token(self, token: str) -> TokenPayload:
        """
        Decodifica y valida un token JWT.
        
        Args:
            token: Token JWT a decodificar.
            
        Returns:
            TokenPayload con la información del token.
            
        Raises:
            CredencialesInvalidasError: Si el token es inválido o ha expirado.
        """
        pass
