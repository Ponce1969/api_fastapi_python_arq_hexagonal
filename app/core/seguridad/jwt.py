# app/core/seguridad/jwt.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from jose import jwt, JWTError # Importa las excepciones de JWT
from pydantic import ValidationError # Para manejar errores de validación de modelos Pydantic
from app.core.config import settings
from app.dominio.excepciones.dominio_excepciones import CredencialesInvalidasError
from app.esquemas.token import TokenPayload
from app.dominio.interfaces.jwt_handler import IJWTHandler


class JWTHandler(IJWTHandler):
    """
    Manejador de JSON Web Tokens (JWT).
    Encapsula la lógica para crear, decodificar y validar tokens de acceso.
    """

    def __init__(self):
        # Asegúrate de que estas configuraciones estén definidas en app/core/config.py
        self.SECRET_KEY: str = settings.SECRET_KEY
        self.ALGORITHM: str = settings.ALGORITHM
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def create_access_token(self, subject: UUID, expires_delta: Optional[int] = None) -> str:
        """
        Crea un token de acceso JWT.

        Args:
            subject: ID del usuario para el cual se crea el token.
            expires_delta: Tiempo de expiración en minutos (opcional).
                          Si es None, usa el valor por defecto de configuración.

        Returns:
            str: El token JWT codificado.
        """
        to_encode = {"sub": str(subject)}
        if expires_delta:
            expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire}) # Añade el tiempo de expiración
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt

    def decode_token(self, token: str) -> TokenPayload:
        """
        Decodifica y valida un token de acceso JWT.

        Args:
            token (str): El token JWT a decodificar.

        Returns:
            TokenPayload: Un objeto Pydantic con el payload validado.

        Raises:
            CredencialesInvalidasError: Si el token es inválido, ha expirado o no puede ser decodificado.
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            # Valida el payload contra el esquema Pydantic. Esto también convierte 'sub' a UUID.
            token_data = TokenPayload.model_validate(payload)
            return token_data
        except (JWTError, ValidationError) as e:
            # Captura errores de JWT (firma, expiración) y de validación de Pydantic (formato).
            raise CredencialesInvalidasError(f"No se pudo validar las credenciales: {e}")

    def get_user_id_from_token(self, token: str) -> UUID:
        """
        Extrae el user_id (UUID) del payload de un token JWT.

        Args:
            token (str): El token JWT.

        Returns:
            UUID: El user_id extraído.

        Raises:
            CredencialesInvalidasError: Si el token es inválido o no contiene un user_id válido.
        """
        token_data = self.decode_token(token)
        if token_data.sub is None:
            raise CredencialesInvalidasError("Token no contiene un 'sub' (ID de usuario).")
        # La validación de Pydantic ya aseguró que 'sub' es un UUID si no es None.
        return token_data.sub