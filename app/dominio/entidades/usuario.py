# app/dominio/entidades/usuario.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

@dataclass
class Usuario:
    """
    Entidad de dominio que representa a un Usuario.
    Es un objeto puro de Python, sin dependencias de frameworks o ORM.
    """
    email: str
    hashed_pwd: str
    full_name: str
    is_active: bool = True
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def actualizar_nombre(self, nuevo_nombre: str):
        """Actualiza el nombre del usuario y la fecha de modificación."""
        if nuevo_nombre and self.full_name != nuevo_nombre:
            self.full_name = nuevo_nombre
            self._marcar_como_actualizado()

    def actualizar_email(self, nuevo_email: str):
        """Actualiza el email del usuario. La validación de formato y unicidad se hace en el servicio."""
        # La validación de formato y unicidad se hace en el servicio
        if self.email != nuevo_email:
            self.email = nuevo_email
            self._marcar_como_actualizado()

    def activar(self):
        """Activa la cuenta del usuario."""
        if not self.is_active:
            self.is_active = True
            self._marcar_como_actualizado()

    def desactivar(self):
        """Desactiva la cuenta del usuario."""
        if self.is_active:
            self.is_active = False
            self._marcar_como_actualizado()

    def cambiar_contrasena(self, nueva_contrasena_hasheada: str):
        """Actualiza la contraseña hasheada del usuario."""
        if self.hashed_pwd != nueva_contrasena_hasheada:
            self.hashed_pwd = nueva_contrasena_hasheada
            self._marcar_como_actualizado()

    def _marcar_como_actualizado(self):
        """Establece la fecha de actualización a la actual."""
        self.updated_at = datetime.utcnow()