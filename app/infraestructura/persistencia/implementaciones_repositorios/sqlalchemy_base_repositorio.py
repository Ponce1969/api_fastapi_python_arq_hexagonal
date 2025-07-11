# app/infraestructura/persistencia/implementaciones_repositorios/sqlalchemy_base_repositorio.py
from abc import ABC, abstractmethod
from typing import TypeVar, Type, List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


# Definir TypeVars para mayor flexibilidad y tipado estricto
SQLAlchemyModel = TypeVar("SQLAlchemyModel")
DomainEntity = TypeVar("DomainEntity")


class SQLAlchemyBaseRepositorio(ABC):
    """
    Clase base abstracta y genérica para repositorios SQLAlchemy.
    Proporciona métodos comunes para la interacción con la base de datos
    y delega la conversión entre modelos ORM y entidades de dominio a las subclases.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        orm_model: Type[SQLAlchemyModel],
    ):
        self.db_session = db_session
        self.orm_model = orm_model

    @abstractmethod
    def _to_domain_entity(self, orm_instance: SQLAlchemyModel) -> Optional[DomainEntity]:
        """
        Convierte una instancia de modelo ORM a una entidad de dominio.
        Este método DEBE ser implementado por cada repositorio concreto.
        """
        ...

    @abstractmethod
    def _populate_orm_from_domain(
        self, orm_instance: SQLAlchemyModel, domain_entity: DomainEntity
    ) -> None:
        """
        Puebla una instancia de modelo ORM con datos de una entidad de dominio.
        Este método DEBE ser implementado por cada repositorio concreto.
        """
        ...

    async def get_by_id(self, entity_id: UUID) -> Optional[DomainEntity]:
        """Obtiene una entidad por su ID."""
        orm_instance = await self.db_session.get(self.orm_model, entity_id)
        return self._to_domain_entity(orm_instance)

    async def save(self, domain_entity: DomainEntity) -> DomainEntity:
        """
        Guarda una entidad de dominio en la base de datos.
        Si la entidad ya tiene un ID y existe, la actualiza.
        Si no, la crea.
        """
        orm_instance = None
        if hasattr(domain_entity, 'id') and domain_entity.id:
            orm_instance = await self.db_session.get(self.orm_model, domain_entity.id)

        if orm_instance is None:
            # Crear una nueva instancia ORM si no se encontró una existente
            orm_instance = self.orm_model()

        # Poblar la instancia ORM (nueva o existente) con los datos del dominio
        self._populate_orm_from_domain(orm_instance, domain_entity)

        self.db_session.add(orm_instance)
        await self.db_session.flush()
        await self.db_session.refresh(orm_instance)
        # Commit para hacer persistentes los cambios una vez finalizada la operación
        await self.db_session.commit()

        return self._to_domain_entity(orm_instance)

    async def delete(self, entity_id: UUID) -> None:
        """Elimina una entidad por su ID."""
        orm_instance = await self.db_session.get(self.orm_model, entity_id)
        if orm_instance:
            await self.db_session.delete(orm_instance)
            await self.db_session.flush()
            await self.db_session.commit()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[DomainEntity]:
        """Obtiene una lista de todas las entidades con paginación."""
        return await self._get_many_by_filter({}, skip=skip, limit=limit)

    async def _get_one_by_filter(self, filter_criteria: Dict[str, Any]) -> Optional[DomainEntity]:
        """
        Método de utilidad protegido para obtener una única entidad basada en criterios de filtro.
        """
        query = select(self.orm_model)
        for key, value in filter_criteria.items():
            query = query.filter(getattr(self.orm_model, key) == value)

        result = await self.db_session.execute(query)
        orm_instance = result.scalar_one_or_none()
        return self._to_domain_entity(orm_instance)

    async def _get_many_by_filter(
        self, filter_criteria: Dict[str, Any], skip: int = 0, limit: int = 100
    ) -> List[DomainEntity]:
        """
        Método de utilidad protegido para obtener múltiples entidades basadas en criterios de filtro.
        """
        query = select(self.orm_model)
        for key, value in filter_criteria.items():
            # Permite filtros opcionales al ignorar los valores None
            if value is not None:
                query = query.filter(getattr(self.orm_model, key) == value)

        result = await self.db_session.execute(query.offset(skip).limit(limit))
        orm_instances = result.scalars().all()
        return [self._to_domain_entity(orm) for orm in orm_instances if orm]