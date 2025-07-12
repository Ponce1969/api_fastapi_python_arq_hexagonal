from uuid import UUID
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, constr


class RolBase(BaseModel):
    """Campos comunes para Rol."""

    name: constr(strip_whitespace=True, min_length=2, max_length=50) = Field(..., example="admin")
    description: Optional[str] = Field(None, example="Rol con todos los permisos")


class RolCreate(RolBase):
    """Esquema de entrada para crear un rol."""

    pass


class RolUpdate(BaseModel):
    name: Optional[constr(strip_whitespace=True, min_length=2, max_length=50)] = None
    description: Optional[str] = None


class RolRead(RolBase):
    """Esquema de salida."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
