# app/dominio/repositorios/contacto_repositorio.py
from typing import Protocol, Optional, List
from uuid import UUID
from app.dominio.entidades.contacto import Contacto

class IContactoRepositorio(Protocol):
    """
    Interfaz (Puerto) para el repositorio de Contactos.
    Define las operaciones que cualquier implementación de repositorio de contactos debe soportar.
    """
    async def save(self, contacto: Contacto) -> Contacto:
        """Guarda un perfil de contacto (crea o actualiza)."""
        ...

    async def get_by_id(self, contacto_id: UUID) -> Optional[Contacto]:
        """Obtiene un perfil de contacto por su ID."""
        ...

    async def get_by_user_id(self, user_id: UUID) -> Optional[Contacto]:
        """Obtiene el perfil de contacto asociado a un ID de usuario."""
        ...

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Contacto]:
        """Obtiene una lista paginada de todos los perfiles de contacto."""
        ...

    async def delete(self, contacto_id: UUID) -> None:
        """Elimina un perfil de contacto por su ID."""
        ...