# app/infraestructura/persistencia/modelos_orm.py
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.infraestructura.persistencia.base import Base # Importamos la Base declarativa

# --- Tabla de Asociación para la relación muchos a muchos entre Usuario y Rol ---
# Representa la tabla 'user_roles' en la base de datos.
# SQLAlchemy creará esta tabla para manejar la relación many-to-many.
user_roles_association_table = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("usuarios.id"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
    # Usamos lambda para que la función se ejecute en el momento de la inserción.
    # datetime.utcnow() está obsoleto desde Python 3.12.
    Column(
        "assigned_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    ),
)

# --- Modelo ORM para la tabla 'usuarios' ---
class UsuarioORM(Base):
    """
    Modelo ORM para la tabla 'usuarios' en la base de datos.
    Mapea la entidad de dominio Usuario a la tabla relacional.
    """
    __tablename__ = "usuarios" # Nombre de la tabla en la base de datos

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_pwd: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relación muchos a muchos con RolORM a través de la tabla de asociación
    # 'secondary' indica la tabla intermedia.
    # 'back_populates' crea una relación bidireccional.
    roles: Mapped[List["RolORM"]] = relationship(
        "RolORM",
        secondary=user_roles_association_table,
        back_populates="usuarios"
    )

    # Relación uno a uno con ContactoORM
    # Si un usuario es eliminado, su perfil de contacto también lo será.
    contacto: Mapped[Optional["ContactoORM"]] = relationship(
        back_populates="usuario", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<UsuarioORM(id={self.id}, email='{self.email}', full_name='{self.full_name}')>"

# --- Modelo ORM para la tabla 'roles' ---
class RolORM(Base):
    """
    Modelo ORM para la tabla 'roles' en la base de datos.
    Mapea la entidad de dominio Rol a la tabla relacional.
    """
    __tablename__ = "roles" # Nombre de la tabla en la base de datos

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relación muchos a muchos con UsuarioORM a través de la tabla de asociación
    # 'secondary' indica la tabla intermedia.
    # 'back_populates' crea una relación bidireccional.
    usuarios: Mapped[List["UsuarioORM"]] = relationship(
        "UsuarioORM",
        secondary=user_roles_association_table,
        back_populates="roles"
    )

    def __repr__(self):
        return f"<RolORM(id={self.id}, name='{self.name}')>"

# --- Modelo ORM para la tabla 'contacts' ---
class ContactoORM(Base):
    """
    Modelo ORM para la tabla 'contacts' en la base de datos.
    Mapea la entidad de dominio Contacto a la tabla relacional.
    """
    __tablename__ = "contacts" # Nombre de la tabla en la base de datos

    # Columnas del perfil de contacto
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Clave foránea para la relación uno a uno con UsuarioORM
    # Es única para garantizar que un usuario solo tenga un perfil de contacto.
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), unique=True, nullable=False, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relación bidireccional con UsuarioORM
    usuario: Mapped["UsuarioORM"] = relationship(
        back_populates="contacto"
    )

    def __repr__(self):
        return f"<ContactoORM(id={self.id}, user_id='{self.user_id}')>"