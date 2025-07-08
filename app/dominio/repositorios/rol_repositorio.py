# app/dominio/repositorios/rol_repositorio.py
from typing import List, Optional, Protocol
from uuid import UUID

from app.dominio.entidades.rol import Rol


class IRolRepositorio(Protocol):
    """
    Interfaz (Puerto) para el repositorio de roles.
    Define las operaciones de persistencia que deben ser implementadas
    por la capa de infraestructura.
    """

    async def save(self, rol: Rol) -> Rol:
        """Guarda un rol (crea o actualiza)."""
        ...

    async def get_by_id(self, rol_id: UUID) -> Optional[Rol]:
        """Obtiene un rol por su ID."""
        ...

    async def get_by_name(self, name: str) -> Optional[Rol]:
        """Obtiene un rol por su nombre."""
        ...

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Rol]:
        """Obtiene una lista paginada de todos los roles."""
        ...

    async def delete(self, rol_id: UUID) -> None:
        """Elimina un rol por su ID."""
        ...