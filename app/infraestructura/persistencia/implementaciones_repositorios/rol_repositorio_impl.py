# app/infraestructura/persistencia/implementaciones_repositorios/rol_repositorio_impl.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.dominio.entidades.rol import Rol
from app.dominio.repositorios.rol_repositorio import IRolRepositorio
from app.infraestructura.persistencia.modelos_orm import RolORM
from .sqlalchemy_base_repositorio import SQLAlchemyBaseRepositorio


class RolRepositorioImpl(SQLAlchemyBaseRepositorio, IRolRepositorio):
    """Implementación concreta del repositorio de roles con SQLAlchemy."""

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, RolORM)

    def _to_domain_entity(self, orm_instance: RolORM) -> Optional[Rol]:
        """Convierte un modelo ORM de Rol a una entidad de dominio Rol."""
        if not orm_instance:
            return None
        return Rol(
            id=orm_instance.id,
            name=orm_instance.name,
            description=orm_instance.description,
            created_at=orm_instance.created_at,
            updated_at=orm_instance.updated_at, # Ahora este campo existe
        )

    def _populate_orm_from_domain(self, orm_instance: RolORM, domain_entity: Rol) -> None:
        """Puebla un modelo ORM de Rol desde una entidad de dominio Rol."""
        # El ID, created_at y updated_at son manejados por la base o la lógica de save.
        orm_instance.name = domain_entity.name
        orm_instance.description = domain_entity.description

    async def create(self, rol: Rol) -> Rol:
        """Crea un nuevo rol delegando en el método 'save' de la clase base."""
        return await self.save(rol)

    async def update(self, rol: Rol) -> Rol:
        """Actualiza un rol existente delegando en el método 'save' de la clase base."""
        return await self.save(rol)

    async def get_by_name(self, name: str) -> Optional[Rol]:
        """Obtiene un rol por su nombre."""
        return await self._get_one_by_filter({"name": name})

    # Los métodos get_by_id, delete, y get_all son heredados directamente.