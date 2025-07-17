# app/infraestructura/persistencia/implementaciones_repositorios/usuario_repositorio_impl.py
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.dominio.entidades.usuario import Usuario
from app.dominio.repositorios.usuario_repositorio import IUsuarioRepositorio
from app.infraestructura.persistencia.modelos_orm import UsuarioORM, RolORM
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

    async def asignar_rol(self, usuario_id: UUID, rol_id: UUID) -> None:
        """Asigna un rol a un usuario.
        
        Args:
            usuario_id: UUID del usuario
            rol_id: UUID del rol a asignar
        """
        # Obtener los modelos ORM
        usuario_orm: UsuarioORM = await self.db_session.get(UsuarioORM, usuario_id)
        rol_orm: RolORM = await self.db_session.get(RolORM, rol_id)
        
        # Verificar que ambos existan
        if not usuario_orm or not rol_orm:
            return
        
        # Asignar el rol si no está ya asignado
        if rol_orm not in usuario_orm.roles:
            usuario_orm.roles.append(rol_orm)
            # No hacemos commit aquí, eso lo maneja el UnitOfWork
    
    async def remover_rol(self, usuario_id: UUID, rol_id: UUID) -> None:
        """Remueve un rol de un usuario.
        
        Args:
            usuario_id: UUID del usuario
            rol_id: UUID del rol a remover
        """
        # Obtener los modelos ORM
        usuario_orm: UsuarioORM = await self.db_session.get(UsuarioORM, usuario_id)
        rol_orm: RolORM = await self.db_session.get(RolORM, rol_id)
        
        # Verificar que ambos existan
        if not usuario_orm or not rol_orm:
            return
        
        # Remover el rol si está asignado
        if rol_orm in usuario_orm.roles:
            usuario_orm.roles.remove(rol_orm)
            # No hacemos commit aquí, eso lo maneja el UnitOfWork

    # Los métodos get_by_id, delete, y get_all son heredados directamente
    # de SQLAlchemyBaseRepositorio y funcionan sin necesidad de reimplementación.