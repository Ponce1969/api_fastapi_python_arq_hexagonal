from uuid import UUID
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, constr, ConfigDict


class RolBase(BaseModel):
    """Campos comunes para Rol."""

    name: str = Field(..., min_length=2, max_length=50, json_schema_extra={"example": "admin"})
    description: Optional[str] = Field(None, json_schema_extra={"example": "Rol con todos los permisos"})


class RolCreate(RolBase):
    """Esquema de entrada para crear un rol."""

    pass


class RolUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = None


class RolRead(RolBase):
    """Esquema de salida."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
