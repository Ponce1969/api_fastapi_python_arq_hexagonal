# app/infraestructura/persistencia/implementaciones_repositorios/usuario_repositorio_impl.py
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.dominio.entidades.usuario import Usuario
from app.dominio.repositorios.usuario_repositorio import IUsuarioRepositorio
from app.infraestructura.persistencia.modelos_orm import UsuarioORM
from .sqlalchemy_base_repositorio import SQLAlchemyBaseRepositorio


class UsuarioRepositorioImpl(SQLAlchemyBaseRepositorio, IUsuarioRepositorio):
    """Implementación concreta del repositorio de usuarios con SQLAlchemy."""

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, UsuarioORM)

    def _to_domain_entity(self, orm_instance: UsuarioORM) -> Optional[Usuario]:
        """Convierte un modelo ORM de Usuario a una entidad de dominio Usuario."""
        if not orm_instance:
            return None
        return Usuario(
            id=orm_instance.id,
            email=orm_instance.email,
            hashed_pwd=orm_instance.hashed_pwd,
            full_name=orm_instance.full_name,
            is_active=orm_instance.is_active,
            created_at=orm_instance.created_at,
            updated_at=orm_instance.updated_at,
        )

    def _populate_orm_from_domain(
        self, orm_instance: UsuarioORM, domain_entity: Usuario
    ) -> None:
        """
        Puebla un modelo ORM de Usuario desde una entidad de dominio Usuario.
        Se omiten los campos 'id', 'created_at' y 'updated_at' ya que son
        gestionados por la base de datos y el ORM.
        """
        orm_instance.email = domain_entity.email
        orm_instance.hashed_pwd = domain_entity.hashed_pwd
        orm_instance.full_name = domain_entity.full_name
        orm_instance.is_active = domain_entity.is_active

    async def create(self, usuario: Usuario) -> Usuario:
        """Crea un nuevo usuario delegando en el método 'save' de la clase base."""
        return await self.save(usuario)

    async def update(self, usuario: Usuario) -> Usuario:
        """Actualiza un usuario existente delegando en el método 'save' de la clase base."""
        return await self.save(usuario)

    async def get_by_email(self, email: str) -> Optional[Usuario]:
        """Obtiene un usuario por su dirección de correo electrónico."""
        return await self._get_one_by_filter({"email": email})

    # Los métodos get_by_id, delete, y get_all son heredados directamente
    # de SQLAlchemyBaseRepositorio y funcionan sin necesidad de reimplementación.