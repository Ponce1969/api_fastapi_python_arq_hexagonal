# app/infraestructura/persistencia/implementaciones_repositorios/contacto_repositorio_impl.py
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.dominio.entidades.contacto import Contacto
from app.dominio.repositorios.contacto_repositorio import IContactoRepositorio
from app.infraestructura.persistencia.modelos_orm import ContactoORM
from .sqlalchemy_base_repositorio import SQLAlchemyBaseRepositorio


class ContactoRepositorioImpl(SQLAlchemyBaseRepositorio, IContactoRepositorio):
    """Implementación concreta del repositorio de contactos con SQLAlchemy."""

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, ContactoORM)

    def _to_domain_entity(self, orm_instance: ContactoORM) -> Optional[Contacto]:
        """Convierte un modelo ORM de Contacto a una entidad de dominio Contacto."""
        if not orm_instance:
            return None
        return Contacto(
            id=orm_instance.id,
            phone=orm_instance.phone,
            address=orm_instance.address,
            city=orm_instance.city,
            country=orm_instance.country,
            zip_code=orm_instance.zip_code,
            user_id=orm_instance.user_id,
            created_at=orm_instance.created_at,
            updated_at=orm_instance.updated_at,
        )

    def _populate_orm_from_domain(
        self, orm_instance: ContactoORM, domain_entity: Contacto
    ) -> None:
        """
        Puebla un modelo ORM de Contacto desde una entidad de dominio Contacto.
        """
        orm_instance.phone = domain_entity.phone
        orm_instance.address = domain_entity.address
        orm_instance.city = domain_entity.city
        orm_instance.country = domain_entity.country
        orm_instance.zip_code = domain_entity.zip_code
        orm_instance.user_id = domain_entity.user_id

    async def get_by_user_id(self, user_id: UUID) -> Optional[Contacto]:
        """Obtiene un perfil de contacto por el ID del usuario asociado."""
        return await self._get_one_by_filter({"user_id": user_id})

    # Los métodos get_by_id, save, delete, y get_all son heredados directamente
    # de SQLAlchemyBaseRepositorio y funcionan sin necesidad de reimplementación.