# app/dominio/entidades/rol.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional

class Rol:
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id if id is not None else uuid4()
        self.name = name
        self.description = description
        self.created_at = created_at if created_at is not None else datetime.now(timezone.utc)
        self.updated_at = updated_at if updated_at is not None else self.created_at

    def actualizar_nombre(self, nuevo_nombre: str):
        """Actualiza el nombre del rol y la fecha de modificación."""
        if self.name != nuevo_nombre:
            self.name = nuevo_nombre
            self.updated_at = datetime.now(timezone.utc)
            
    def actualizar_descripcion(self, nueva_descripcion: Optional[str]):
        """Actualiza la descripción del rol y la fecha de modificación."""
        if self.description != nueva_descripcion:
            self.description = nueva_descripcion
            self.updated_at = datetime.now(timezone.utc)

    def __eq__(self, other):
        if not isinstance(other, Rol):
            return NotImplemented
        return self.id == other.id # La igualdad se basa en el ID único

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f"<Rol(id={self.id}, name='{self.name}')>"