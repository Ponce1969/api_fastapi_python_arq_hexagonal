# app/esquemas/usuario.py
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


# Propiedades base compartidas por todos los esquemas de usuario
class UsuarioBase(BaseModel):
    email: EmailStr = Field(..., example="juan.perez@example.com")
    full_name: Optional[str] = Field(None, example="Juan Pérez")


# Esquema para la creación de un usuario (entrada en el endpoint de registro)
# Hereda de UsuarioBase y añade la contraseña.
class UsuarioCrear(UsuarioBase):
    password: str = Field(..., min_length=8, example="unaContraseñaFuerte123")


# Esquema para la actualización de un usuario
class UsuarioActualizar(UsuarioBase):
    email: Optional[EmailStr] = None # Todos los campos son opcionales en la actualización
    password: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


# Esquema para la lectura de un usuario (salida en los endpoints)
# No incluye la contraseña por seguridad.
class UsuarioLeer(UsuarioBase):
    id: UUID
    is_active: bool

    class Config:
        from_attributes = True # Permite a Pydantic leer datos desde atributos de objeto (ORM models)