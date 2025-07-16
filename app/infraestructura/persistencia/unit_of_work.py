"""
Implementación del patrón Unit of Work para gestionar transacciones atómicas en SQLAlchemy.

Este módulo define la clase SQLAlchemyUnitOfWork que permite agrupar múltiples operaciones
de repositorio en una única transacción atómica, asegurando la consistencia de los datos
y facilitando la implementación de casos de uso complejos.
"""
from typing import Callable, AsyncContextManager, Optional, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager

from app.infraestructura.persistencia.excepciones.persistencia_excepciones import ExcepcionesMapper

# Importar interfaces de repositorios y UnitOfWork
from app.dominio.interfaces.unit_of_work import IUnitOfWork
from app.dominio.repositorios.usuario_repositorio import IUsuarioRepositorio
from app.dominio.repositorios.rol_repositorio import IRolRepositorio
from app.dominio.repositorios.contacto_repositorio import IContactoRepositorio

# Importar implementaciones concretas de repositorios
from app.infraestructura.persistencia.implementaciones_repositorios.usuario_repositorio_impl import UsuarioRepositorioImpl
from app.infraestructura.persistencia.implementaciones_repositorios.rol_repositorio_impl import RolRepositorioImpl
from app.infraestructura.persistencia.implementaciones_repositorios.contacto_repositorio_impl import ContactoRepositorioImpl

class SQLAlchemyUnitOfWork(IUnitOfWork):
    """
    Implementa el patrón Unit of Work para SQLAlchemy.
    
    Esta clase actúa como un administrador de contexto asíncrono que encapsula
    una sesión de SQLAlchemy y gestiona las transacciones (commit/rollback).
    Permite agrupar múltiples operaciones de repositorio en una única transacción
    atómica, garantizando que todas tengan éxito o ninguna se aplique.
    
    Además, proporciona acceso a todos los repositorios de la aplicación
    a través de atributos, asegurando que todos utilicen la misma sesión
    y por tanto participen en la misma transacción.
    
    Ejemplo de uso:
    ```python
    async with SQLAlchemyUnitOfWork(session_factory) as uow:
        usuario = await uow.usuarios.save(usuario_data)
        await uow.roles.asignar_rol_a_usuario(usuario.id, rol_id)
        # Al salir del contexto, se hará commit automáticamente si no hay excepciones
        # Si ocurre una excepción, se hará rollback automáticamente
    ```
    """
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        """
        Inicializa el Unit of Work con una fábrica de sesiones.
        
        Args:
            session_factory: Fábrica de sesiones que crea y devuelve una nueva sesión de SQLAlchemy.
        """
        self.session_factory = session_factory
        self.session: Optional[AsyncSession] = None
        
        # Repositorios (inicializados en __aenter__)
        self.usuarios: IUsuarioRepositorio = None
        self.roles: IRolRepositorio = None
        self.contactos: IContactoRepositorio = None
    
    async def __aenter__(self) -> IUnitOfWork:
        """
        Inicia una nueva sesión y la devuelve para su uso en el contexto.
        También inicializa todos los repositorios con esta sesión.
        
        Returns:
            La instancia actual de SQLAlchemyUnitOfWork como IUnitOfWork.
        """
        self.session = self.session_factory()
        
        # Inicializar todos los repositorios con la misma sesión
        self.usuarios = UsuarioRepositorioImpl(self.session)
        self.roles = RolRepositorioImpl(self.session)
        self.contactos = ContactoRepositorioImpl(self.session)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Cierra la sesión y realiza commit o rollback según corresponda.
        
        Si ocurrió una excepción durante el contexto, se hace rollback.
        De lo contrario, se realiza commit.
        
        Si la excepción es de tipo SQLAlchemyError u otra excepción técnica,
        se mapea a una excepción de dominio apropiada utilizando el ExcepcionesMapper.
        
        Args:
            exc_type: Tipo de excepción si ocurrió alguna, None en caso contrario.
            exc_val: Valor de la excepción si ocurrió alguna, None en caso contrario.
            exc_tb: Traceback de la excepción si ocurrió alguna, None en caso contrario.
            
        Returns:
            bool: True si la excepción fue manejada y no debe propagarse, False en caso contrario.
        """
        if self.session is None:
            return False
            
        try:
            if exc_type:
                # Si hay una excepción, hacemos rollback
                await self.rollback()
                
                # Si es una excepción técnica de SQLAlchemy u otra excepción no de dominio,
                # la mapeamos a una excepción de dominio y la relanzamos
                if exc_val and not isinstance(exc_val, Exception):
                    # Si no es una instancia de Exception, no intentamos mapearla
                    return False
                    
                if exc_val and not hasattr(exc_val, "__module__") or not exc_val.__module__.startswith("app.dominio"):
                    # Mapear la excepción técnica a una excepción de dominio
                    domain_exception = ExcepcionesMapper.wrap_exception(exc_val)
                    # Relanzar la excepción de dominio preservando el traceback
                    raise domain_exception from exc_val
                
                # Si ya es una excepción de dominio, la dejamos propagar
                return False
            else:
                # Si no hay excepción, hacemos commit
                await self.commit()
                return False
        except Exception as e:
            # Si ocurre una excepción durante el commit/rollback, la mapeamos y relanzamos
            if not hasattr(e, "__module__") or not e.__module__.startswith("app.dominio"):
                domain_exception = ExcepcionesMapper.wrap_exception(e)
                raise domain_exception from e
            raise
        finally:
            # Cerramos la sesión y limpiamos las referencias
            await self.session.close()
            self.session = None
            
            # Limpiar referencias a los repositorios
            self.usuarios = None
            self.roles = None
            self.contactos = None
    
    async def commit(self):
        """
        Confirma la transacción actual.
        
        Raises:
            SQLAlchemyError: Si ocurre un error durante el commit.
        """
        if self.session:
            await self.session.commit()
    
    async def rollback(self):
        """
        Revierte la transacción actual.
        
        Raises:
            SQLAlchemyError: Si ocurre un error durante el rollback.
        """
        if self.session:
            await self.session.rollback()
    
    @asynccontextmanager
    async def begin(self) -> AsyncContextManager[AsyncSession]:
        """
        Proporciona un contexto alternativo que expone la sesión para uso directo.
        
        Útil para casos específicos donde se necesita acceder directamente a la sesión
        para operaciones avanzadas o en funciones que no pueden envolverse completamente
        en el 'async with uow:' principal.
        
        Ejemplo de uso:
        ```python
        async with uow:
            # Operaciones normales con repositorios
            usuario = await uow.usuarios.get_by_id(id)
            
            # Acceso directo a la sesión para operaciones específicas
            async with uow.begin() as session:
                # Operaciones directas con la sesión
                result = await session.execute(query_especial)
        ```
        
        Yields:
            AsyncSession: La sesión de SQLAlchemy asociada con este Unit of Work.
        
        Raises:
            RuntimeError: Si se llama antes de entrar al contexto principal del UnitOfWork.
            DominioExcepcion: Si ocurre un error técnico, se mapea a una excepción de dominio.
        """
        if self.session is None:
            raise RuntimeError("Cannot begin transaction on a UnitOfWork not yet entered.")
            
        try:
            yield self.session  # Devuelve directamente la sesión, no self
            # No hacemos commit/rollback aquí, eso es responsabilidad del __aexit__ del UoW
            # o de quien use este método si no hay un UoW principal envolvente
        except Exception as e:
            # Mapear excepciones técnicas a excepciones de dominio
            if not hasattr(e, "__module__") or not e.__module__.startswith("app.dominio"):
                domain_exception = ExcepcionesMapper.wrap_exception(e)
                raise domain_exception from e
            # Si ya es una excepción de dominio, simplemente la relanzamos
            raise e
