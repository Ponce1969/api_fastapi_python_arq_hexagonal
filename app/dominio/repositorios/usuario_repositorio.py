# app/dominio/repositorios/usuario_repositorio.py
from typing import List, Optional, Protocol, Tuple
from uuid import UUID

from app.dominio.entidades.usuario import Usuario
from app.dominio.entidades.rol import Rol


class IUsuarioRepositorio(Protocol):
    """
    Interfaz (Puerto) para el repositorio de usuarios.
    Define las operaciones de persistencia que deben ser implementadas
    por la capa de infraestructura.
    """

    async def save(self, usuario: Usuario) -> Usuario:
        """Guarda un usuario (crea o actualiza)."""
        ...

    async def get_by_id(self, usuario_id: UUID) -> Optional[Usuario]:
        """Obtiene un usuario por su ID."""
        ...

    async def get_by_email(self, email: str) -> Optional[Usuario]:
        """Obtiene un usuario por su correo electrónico."""
        ...

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Usuario]:
        """Obtiene una lista paginada de todos los usuarios."""
        ...

    async def delete(self, usuario_id: UUID) -> None:
        """Elimina un usuario por su ID."""
        ...
        
    async def asignar_rol(self, usuario_id: UUID, rol_id: UUID) -> None:
        """Asigna un rol a un usuario."""
        ...
        
    async def remover_rol(self, usuario_id: UUID, rol_id: UUID) -> None:
        """Remueve un rol de un usuario."""
        ...