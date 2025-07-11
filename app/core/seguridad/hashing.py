from typing import Protocol, runtime_checkable
from passlib.context import CryptContext

# --- Protocol Definition (Interface) ---
# La anotación @runtime_checkable permite usar isinstance() con este protocolo.
# Esto es útil para aserciones y verificaciones en tiempo de ejecución.
@runtime_checkable
class Hasher(Protocol):
    """
    Define la interfaz para un servicio de hashing de contraseñas.
    Cualquier clase que implemente estos métodos cumplirá con el protocolo.
    """
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica si una contraseña plana coincide con su hash."""
        ...

    def hash_password(self, password: str) -> str: # <-- ¡MÉTODO RENOMBRADO AQUÍ!
        """Genera el hash de una contraseña plana."""
        ...


# --- Concrete Implementation ---
class PasslibHasher(Hasher):
    """
    Una implementación concreta del protocolo Hasher usando la librería passlib.
    """
    def __init__(self):
        # Configura el contexto de passlib.
        # 'schemes' define los algoritmos de hashing soportados, en orden de preferencia.
        # "argon2" es el algoritmo principal para hashear nuevas contraseñas.
        # "bcrypt" se incluye para poder verificar contraseñas antiguas que
        # pudieran haber sido hasheadas con bcrypt, permitiendo una migración transparente.
        # 'deprecated="auto"' marcará automáticamente como obsoletos los hashes que no
        # usen el esquema principal ("argon2"), sugiriendo un re-hash en el futuro.
        self.pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica la contraseña usando el contexto de passlib."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str: # <-- ¡MÉTODO RENOMBRADO AQUÍ!
        """Genera el hash de la contraseña usando el contexto de passlib."""
        return self.pwd_context.hash(password)


# Esta aserción ahora funcionará gracias a @runtime_checkable.
assert isinstance(PasslibHasher(), Hasher)