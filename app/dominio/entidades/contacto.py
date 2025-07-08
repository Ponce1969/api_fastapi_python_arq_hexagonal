# app/dominio/entidades/contacto.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, Self

class Contacto:
    def __init__(
        self,
        user_id: UUID,
        phone: str,
        address: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        zip_code: Optional[str] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id if id is not None else uuid4()
        self.user_id = user_id
        self.phone = phone
        self.address = address
        self.city = city
        self.country = country
        self.zip_code = zip_code
        self.created_at = created_at if created_at is not None else datetime.now(timezone.utc)
        self.updated_at = updated_at if updated_at is not None else self.created_at

    def actualizar_datos(
        self,
        phone: str,
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

        if self.phone != phone:
            self.phone = phone
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
        if not isinstance(other, Self):
            return NotImplemented
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f"<Contacto(id={self.id}, user_id='{self.user_id}', phone='{self.phone}')>"