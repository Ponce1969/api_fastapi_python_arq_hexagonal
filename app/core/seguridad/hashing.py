# app/core/seguridad/hashing.py
from typing import Protocol
from passlib.context import CryptContext


class Hasher(Protocol):
    """
    Interfaz (Puerto) para un servicio de hashing de contraseñas.
    Define los métodos que cualquier implementación de hasher debe proporcionar.
    """

    def hash_password(self, password: str) -> str:
        """Hashea una contraseña en texto plano."""
        ...

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica si una contraseña en texto plano coincide con su hash."""
        ...


class PasslibHasher:
    """
    Implementación concreta del Hasher utilizando la librería passlib.
    Configurado para usar Argon2 como el algoritmo de hashing por defecto.
    """
    def __init__(self):
        self.pwd_context = CryptContext(
            schemes=["argon2", "bcrypt"],  # Argon2 es el preferido
            deprecated="auto"             # Las contraseñas con esquemas antiguos se actualizarán automáticamente
        )

    def hash_password(self, password: str) -> str:
        """Hashea una contraseña en texto plano usando Argon2."""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica si una contraseña en texto plano coincide con su hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

# Para asegurar que nuestra implementación cumple con la interfaz en tiempo de desarrollo.
assert isinstance(PasslibHasher(), Hasher)