# app/dominio/entidades/contacto.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, TypeVar

# Usar TypeVar como alternativa a Self para compatibilidad con Python 3.10
T = TypeVar('T', bound='Contacto')

class Contacto:
    def __init__(
        self,
        user_id: UUID,
        name: str,
        email: str,
        phone: str,
        message: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        zip_code: Optional[str] = None,
        is_read: bool = False,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id if id is not None else uuid4()
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone
        self.message = message
        self.address = address
        self.city = city
        self.country = country
        self.zip_code = zip_code
        self.is_read = is_read
        self.created_at = created_at if created_at is not None else datetime.now(timezone.utc)
        self.updated_at = updated_at if updated_at is not None else self.created_at

    def actualizar_datos(
        self,
        name: str,
        email: str,
        phone: str,
        message: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        zip_code: Optional[str] = None
    ):
        """
        Actualiza los datos del perfil de contacto.
        Solo actualiza si hay un cambio real y marca el updated_at.
        """
        changed = False

        if self.name != name:
            self.name = name
            changed = True
        if self.email != email:
            self.email = email
            changed = True
        if self.phone != phone:
            self.phone = phone
            changed = True
        if self.message != message:
            self.message = message
            changed = True
        if self.address != address:
            self.address = address
            changed = True
        if self.city != city:
            self.city = city
            changed = True
        if self.country != country:
            self.country = country
            changed = True
        if self.zip_code != zip_code:
            self.zip_code = zip_code
            changed = True

        if changed:
            self.updated_at = datetime.now(timezone.utc)

    def __eq__(self, other):
        # Evitamos usar isinstance con Self que causa problemas en Python 3.12
        if not hasattr(other, "id") or not isinstance(other.id, UUID):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def marcar_como_leido(self, leido: bool = True) -> bool:
        """
        Marca el contacto como leído o no leído.
        """
        if self.is_read != leido:
            self.is_read = leido
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def __repr__(self):
        return f"<Contacto(id={self.id}, name='{self.name}', email='{self.email}', is_read={self.is_read})>"