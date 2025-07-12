from uuid import UUID
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, constr, validator


class ContactoBase(BaseModel):
    """Campos comunes para crear o actualizar un contacto."""

    phone: constr(strip_whitespace=True, min_length=4, max_length=25) = Field(..., example="+59898765432")
    address: Optional[str] = Field(None, example="Av. Libertador 1234")
    city: Optional[str] = Field(None, example="Montevideo")
    country: Optional[str] = Field(None, example="Uruguay")
    zip_code: Optional[str] = Field(None, example="11200")

    @validator("phone")
    def validate_phone(cls, v):
        if not v.replace("+", "").isdigit():
            raise ValueError("El teléfono debe contener solo dígitos y opcionalmente un '+' inicial")
        return v


class ContactoCreate(ContactoBase):
    """Esquema de entrada para crear o actualizar datos de contacto."""

    pass  # Inherits all fields from base as required/optional


class ContactoRead(ContactoBase):
    """Esquema de salida con metadatos adicionales."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
