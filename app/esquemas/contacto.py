from uuid import UUID
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field, constr, EmailStr, field_validator


class ContactoBase(BaseModel):
    """Campos comunes para crear o actualizar un contacto."""

    # Datos personales
    name: constr(strip_whitespace=True, min_length=2, max_length=100) = Field(..., example="Juan Pérez")
    email: EmailStr = Field(..., example="juan.perez@example.com")
    message: Optional[str] = Field(None, example="Me interesa saber más sobre sus servicios")
    
    # Información de contacto
    phone: constr(strip_whitespace=True, min_length=4, max_length=25) = Field(..., example="+59898765432")
    address: Optional[str] = Field(None, example="Av. Libertador 1234")
    city: Optional[str] = Field(None, example="Montevideo")
    country: Optional[str] = Field(None, example="Uruguay")
    zip_code: Optional[str] = Field(None, example="11200")

    @field_validator("phone")
    def validate_phone(cls, v):
        if not v.replace("+", "").isdigit():
            raise ValueError("El teléfono debe contener solo dígitos y opcionalmente un '+' inicial")
        return v


class ContactoCreate(ContactoBase):
    """Esquema de entrada para crear o actualizar datos de contacto."""

    # Opcional: campos adicionales específicos para la creación
    # No necesarios por ahora - hereda todo de ContactoBase


class ContactoRead(ContactoBase):
    """Esquema de salida con metadatos adicionales."""

    id: UUID
    user_id: UUID
    is_read: bool = Field(default=False, description="Indica si el contacto ha sido revisado por un administrador")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        

class ContactoUpdate(BaseModel):
    """Esquema para actualizar el estado de lectura de un contacto."""
    
    is_read: bool = Field(..., description="Nuevo estado de lectura")
