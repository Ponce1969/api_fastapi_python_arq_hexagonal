"""
Interfaz para el patrón Unit of Work.

Este módulo define la interfaz IUnitOfWork que establece el contrato
que deben cumplir todas las implementaciones del patrón Unit of Work.
"""
from abc import ABC, abstractmethod
from typing import Optional, AsyncContextManager

from sqlalchemy.ext.asyncio import AsyncSession

from app.dominio.repositorios.usuario_repositorio import IUsuarioRepositorio
from app.dominio.repositorios.rol_repositorio import IRolRepositorio
from app.dominio.repositorios.contacto_repositorio import IContactoRepositorio

class IUnitOfWork(ABC):
    """
    Interfaz para el patrón Unit of Work.
    
    Define el contrato que deben cumplir todas las implementaciones
    del patrón Unit of Work, independientemente de la tecnología
    de persistencia utilizada.
    
    Atributos:
        usuarios: Repositorio de usuarios.
        roles: Repositorio de roles.
        contactos: Repositorio de contactos.
    """
    usuarios: IUsuarioRepositorio
    roles: IRolRepositorio
    contactos: IContactoRepositorio
    
    @abstractmethod
    async def __aenter__(self) -> 'IUnitOfWork':
        """
        Inicia una nueva transacción y retorna el UnitOfWork.
        
        Returns:
            IUnitOfWork: La instancia del UnitOfWork.
        """
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Finaliza la transacción con commit o rollback según corresponda.
        
        Args:
            exc_type: Tipo de excepción si ocurrió alguna, None en caso contrario.
            exc_val: Valor de la excepción si ocurrió alguna, None en caso contrario.
            exc_tb: Traceback de la excepción si ocurrió alguna, None en caso contrario.
        """
        pass
    
    @abstractmethod
    async def commit(self):
        """
        Confirma los cambios realizados en la transacción actual.
        """
        pass
    
    @abstractmethod
    async def rollback(self):
        """
        Revierte los cambios realizados en la transacción actual.
        """
        pass
    
    @abstractmethod
    def begin(self) -> AsyncContextManager[AsyncSession]:
        """
        Proporciona un contexto alternativo para iniciar una transacción.
        
        Returns:
            AsyncContextManager[AsyncSession]: Un administrador de contexto asíncrono
            que proporciona una sesión de SQLAlchemy para gestionar la transacción.
        """
        pass
