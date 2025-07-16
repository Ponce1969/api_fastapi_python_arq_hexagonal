# app/esquemas/usuario.py
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator


# Propiedades base compartidas por todos los esquemas de usuario
class UsuarioBase(BaseModel):
    email: EmailStr = Field(..., example="juan.perez@example.com")
    full_name: Optional[str] = Field(None, example="Juan Pérez", min_length=2, max_length=100)
    
    @field_validator('full_name')
    def validate_full_name(cls, v):
        """Validación adicional para full_name si está presente."""
        if v is not None and len(v.strip()) == 0:
            raise ValueError('El nombre no puede estar vacío si se proporciona')
        return v


# Esquema para la creación de un usuario (entrada en el endpoint de registro)
# Hereda de UsuarioBase y añade la contraseña.
class UsuarioCrear(UsuarioBase):
    password: str = Field(..., min_length=8, example="unaContraseñaFuerte123")


# Esquema para la actualización de un usuario
class UsuarioActualizar(UsuarioBase):
    email: Optional[EmailStr] = None # Todos los campos son opcionales en la actualización
    password: Optional[str] = Field(None, min_length=8)
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    is_active: Optional[bool] = None


# Esquema específico para cambio de contraseña
class UsuarioCambioPassword(BaseModel):
    current_password: str = Field(..., min_length=1, example="contraseñaActual")
    new_password: str = Field(..., min_length=8, example="nuevaContraseñaFuerte123")
    
    @field_validator('new_password')
    def validate_new_password(cls, v, values):
        """Validar que la nueva contraseña sea diferente de la actual."""
        if 'current_password' in values.data and v == values.data['current_password']:
            raise ValueError('La nueva contraseña debe ser diferente de la actual')
        return v


# Esquema para la lectura de un usuario (salida en los endpoints)
# No incluye la contraseña por seguridad.
class UsuarioLeer(UsuarioBase):
    id: UUID
    is_active: bool

    class Config:
        from_attributes = True # Permite a Pydantic leer datos desde atributos de objeto (ORM models)