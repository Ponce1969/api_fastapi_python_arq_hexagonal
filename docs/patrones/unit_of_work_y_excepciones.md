# Patrón Unit of Work y Mapeador de Excepciones

## Introducción

Este documento describe la implementación del patrón Unit of Work (UoW) y el sistema de mapeo de excepciones en nuestra aplicación. Estos patrones trabajan juntos para proporcionar transacciones atómicas y un manejo de errores coherente en toda la aplicación.

## Patrón Unit of Work

### Propósito

El patrón Unit of Work proporciona una abstracción para agrupar operaciones de base de datos en una única transacción atómica. Esto garantiza que todas las operaciones se completen con éxito o ninguna de ellas se aplique (principio de atomicidad).

### Componentes principales

#### 1. Interfaz `IUnitOfWork`

```python
# app/dominio/repositorios/unit_of_work.py
from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

class IUnitOfWork(ABC):
    """Interfaz para el patrón Unit of Work."""
    
    @abstractmethod
    async def __aenter__(self):
        """Inicia una nueva transacción."""
        ...
        
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Finaliza la transacción con commit o rollback según corresponda."""
        ...
        
    @abstractmethod
    async def commit(self):
        """Realiza commit de la transacción actual."""
        ...
        
    @abstractmethod
    async def rollback(self):
        """Realiza rollback de la transacción actual."""
        ...
```

#### 2. Implementación `SQLAlchemyUnitOfWork`

```python
# app/infraestructura/persistencia/unit_of_work.py
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.dominio.repositorios.unit_of_work import IUnitOfWork
from app.infraestructura.persistencia.excepciones.persistencia_excepciones import ExcepcionesMapper
from app.dominio.excepciones.dominio_excepciones import DominioExcepcion

class SQLAlchemyUnitOfWork(IUnitOfWork):
    """Implementación del patrón Unit of Work con SQLAlchemy."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session: Optional[AsyncSession] = None
        # Los repositorios se inicializan en __aenter__
        self.usuarios = None
        self.roles = None
        self.contactos = None
        
    async def __aenter__(self):
        """Inicia una nueva transacción y crea los repositorios."""
        self.session = self.session_factory()
        
        # Inicializar repositorios con la sesión actual
        from app.infraestructura.persistencia.implementaciones_repositorios.usuario_repositorio_impl import UsuarioRepositorioImpl
        from app.infraestructura.persistencia.implementaciones_repositorios.rol_repositorio_impl import RolRepositorioImpl
        from app.infraestructura.persistencia.implementaciones_repositorios.contacto_repositorio_impl import ContactoRepositorioImpl
        
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
        """
        if self.session is None:
            return False
        
        try:
            if exc_type:
                # Si hay una excepción, hacemos rollback
                logging.debug(f"UnitOfWork: Realizando rollback debido a excepción: {exc_type.__name__ if exc_type else 'None'}")
                await self.rollback()
                
                # Si es una excepción técnica de SQLAlchemy u otra excepción no de dominio,
                # la mapeamos a una excepción de dominio y la relanzamos
                if exc_val and not isinstance(exc_val, Exception):
                    # Si no es una instancia de Exception, no intentamos mapearla
                    logging.debug(f"UnitOfWork: No se mapea el valor {exc_val} porque no es una excepción")
                    return False
                
                # Verificar si es una excepción de dominio
                is_domain_exception = isinstance(exc_val, DominioExcepcion)
                
                if exc_val and not is_domain_exception:
                    # Mapear la excepción técnica a una excepción de dominio
                    logging.debug(f"UnitOfWork: Mapeando excepción técnica {exc_type.__name__} a excepción de dominio")
                    domain_exception = ExcepcionesMapper.wrap_exception(exc_val)
                    # Relanzar la excepción de dominio preservando el traceback
                    raise domain_exception from exc_val
                
                # Si ya es una excepción de dominio, la dejamos propagar
                return False
            else:
                # Si no hay excepción, hacemos commit
                logging.debug("UnitOfWork: Realizando commit")
                await self.commit()
                return True
                
        except Exception as e:
            # Capturar cualquier excepción durante el commit/rollback
            logging.error(f"UnitOfWork: Error durante commit/rollback: {str(e)}")
            raise
        finally:
            # Siempre cerrar la sesión
            await self.session.close()
            self.session = None
            
    async def commit(self):
        """Realiza commit de la transacción actual."""
        if self.session:
            await self.session.commit()
            
    async def rollback(self):
        """Realiza rollback de la transacción actual."""
        if self.session:
            await self.session.rollback()
```

## Sistema de Mapeo de Excepciones

### Propósito

El sistema de mapeo de excepciones traduce excepciones técnicas de la capa de infraestructura (como SQLAlchemy) a excepciones de dominio más significativas. Esto mantiene la separación de capas y proporciona mensajes de error más útiles para los usuarios.

### Componentes principales

#### 1. Excepciones de Dominio

```python
# app/dominio/excepciones/dominio_excepciones.py
class DominioExcepcion(Exception):
    """Excepción base para todas las excepciones del dominio."""
    pass

class EntidadNoEncontradaError(DominioExcepcion):
    """Se lanza cuando no se encuentra una entidad."""
    pass

class EmailYaRegistradoError(DominioExcepcion):
    """Se lanza cuando se intenta registrar un email que ya existe."""
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"El email {email} ya está registrado")

class PersistenciaError(DominioExcepcion):
    """Se lanza cuando ocurre un error de persistencia."""
    pass

# Más excepciones específicas...
```

#### 2. Mapeador de Excepciones

```python
# app/infraestructura/persistencia/excepciones/persistencia_excepciones.py
import traceback
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError

from app.dominio.excepciones.dominio_excepciones import (
    DominioExcepcion,
    EntidadNoEncontradaError,
    EmailYaRegistradoError,
    PersistenciaError
)

class ExcepcionesMapper:
    """Clase utilitaria para mapear excepciones de SQLAlchemy a excepciones de dominio."""
    
    @staticmethod
    def wrap_exception(exception: Exception) -> DominioExcepcion:
        """
        Envuelve una excepción técnica en una excepción de dominio apropiada.
        
        Args:
            exception: La excepción técnica a envolver.
            
        Returns:
            Una excepción de dominio que envuelve la excepción técnica.
        """
        # Capturar el traceback para preservarlo
        tb = traceback.format_exc()
        
        # Mapear excepciones de SQLAlchemy
        if isinstance(exception, IntegrityError):
            error_msg = str(exception).lower()
            
            # Detectar violaciones de clave única para email
            if "unique" in error_msg and "email" in error_msg:
                # Intentar extraer el email del mensaje de error
                email = "desconocido"
                return EmailYaRegistradoError(email)
            
            # Detectar violaciones de clave foránea
            elif "foreign key" in error_msg:
                return PersistenciaError(f"Error de integridad de datos: {str(exception)}")
            
            # Otras violaciones de integridad
            else:
                return PersistenciaError(f"Error de integridad de datos: {str(exception)}")
                
        elif isinstance(exception, NoResultFound):
            return EntidadNoEncontradaError("La entidad solicitada no fue encontrada")
            
        elif isinstance(exception, SQLAlchemyError):
            return PersistenciaError(f"Error de base de datos: {str(exception)}")
            
        # Para otras excepciones, devolver una excepción de dominio genérica
        else:
            return DominioExcepcion(
                f"Error inesperado: {str(exception)}\n"
                f"Excepción original: {type(exception).__name__}: {str(exception)}\n"
                f"Traceback original:\n{tb}"
            )
```

## Uso del Patrón Unit of Work

### En la Inyección de Dependencias

```python
# app/api/deps.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.dominio.repositorios.unit_of_work import IUnitOfWork
from app.infraestructura.persistencia.unit_of_work import SQLAlchemyUnitOfWork
from app.infraestructura.persistencia.sesion import get_session_factory

async def get_unit_of_work() -> IUnitOfWork:
    """
    Proporciona una instancia de Unit of Work para gestionar transacciones.
    
    Returns:
        IUnitOfWork: Una instancia de Unit of Work.
    """
    session_factory = get_session_factory()
    return SQLAlchemyUnitOfWork(session_factory)
```

### En los Servicios

```python
# app/aplicacion/servicios/usuario_servicio.py
from app.dominio.repositorios.unit_of_work import IUnitOfWork
from app.dominio.entidades.usuario import Usuario
from app.dominio.excepciones.dominio_excepciones import UsuarioNoEncontradoError

class UsuarioServicio:
    """Servicio para la gestión de usuarios."""
    
    def __init__(self, uow: IUnitOfWork, hasher):
        self.uow = uow
        self.hasher = hasher
        
    async def crear_usuario(self, email: str, password: str, full_name: str) -> Usuario:
        """
        Crea un nuevo usuario.
        
        Args:
            email: Email del usuario.
            password: Contraseña del usuario.
            full_name: Nombre completo del usuario.
            
        Returns:
            Usuario: El usuario creado.
            
        Raises:
            EmailYaRegistradoError: Si el email ya está registrado.
        """
        # Hashear la contraseña
        hashed_pwd = self.hasher.hash_password(password)
        
        # Crear el usuario
        nuevo_usuario = Usuario(
            email=email,
            hashed_pwd=hashed_pwd,
            full_name=full_name,
            is_active=True
        )
        
        # Guardar el usuario en una transacción
        async with self.uow as uow:
            # Verificar si el email ya existe
            usuario_existente = await uow.usuarios.get_by_email(email)
            if usuario_existente:
                raise EmailYaRegistradoError(email)
                
            # Guardar el usuario
            usuario_guardado = await uow.usuarios.save(nuevo_usuario)
            await uow.commit()
            
        return usuario_guardado
```

## Mejores Prácticas

### 1. Siempre usar Unit of Work para operaciones de base de datos

- **Correcto**: Acceder a los repositorios a través del UoW para garantizar que todas las operaciones usen la misma sesión.

```python
async with uow as uow:
    usuario = await uow.usuarios.get_by_id(usuario_id)
    rol = await uow.roles.get_by_id(rol_id)
    # Todas las operaciones comparten la misma sesión y transacción
```

- **Incorrecto**: Usar proveedores individuales de repositorios.

```python
# ❌ No hacer esto
usuario_repo = get_usuario_repositorio()
rol_repo = get_rol_repositorio()
# Cada repositorio podría usar una sesión diferente
```

### 2. Manejo de excepciones

- **Correcto**: Dejar que el UoW maneje las excepciones técnicas y las traduzca a excepciones de dominio.

```python
try:
    async with uow as uow:
        await uow.usuarios.save(usuario)
        await uow.commit()
except EmailYaRegistradoError as e:
    # Manejar excepción de dominio
    return {"error": str(e)}
```

- **Incorrecto**: Capturar excepciones técnicas directamente.

```python
# ❌ No hacer esto
try:
    async with uow as uow:
        await uow.usuarios.save(usuario)
        await uow.commit()
except IntegrityError as e:
    # Manejar excepción técnica
    return {"error": "Error de base de datos"}
```

### 3. Transacciones atómicas

- **Correcto**: Agrupar operaciones relacionadas en una sola transacción.

```python
async with uow as uow:
    usuario = await uow.usuarios.save(usuario)
    perfil = await uow.perfiles.save(perfil)
    await uow.commit()
    # Si algo falla, se hace rollback de todo
```

- **Incorrecto**: Usar múltiples transacciones para operaciones relacionadas.

```python
# ❌ No hacer esto
async with uow1 as uow:
    usuario = await uow.usuarios.save(usuario)
    
async with uow2 as uow:
    perfil = await uow.perfiles.save(perfil)
    # Si esto falla, el usuario ya se guardó
```

### 4. Commit explícito

- **Correcto**: Llamar a `commit()` explícitamente al final de la transacción.

```python
async with uow as uow:
    # Operaciones...
    await uow.commit()
```

- **Incorrecto**: Confiar en el commit implícito (puede llevar a confusión).

```python
# ❌ No hacer esto
async with uow as uow:
    # Operaciones...
    # Falta commit explícito
```

### 5. Validación en el dominio

- **Correcto**: Realizar validaciones de dominio antes de interactuar con la base de datos.

```python
async def crear_usuario(self, email: str, password: str):
    # Validar email
    if not self._es_email_valido(email):
        raise ValueError("Email inválido")
        
    async with self.uow as uow:
        # Continuar con la creación...
```

## Conclusión

El patrón Unit of Work combinado con el mapeador de excepciones proporciona una base sólida para la gestión de transacciones y el manejo de errores en nuestra aplicación. Siguiendo estas mejores prácticas, podemos garantizar que nuestras operaciones de base de datos sean atómicas, consistentes y que los errores se manejen de manera uniforme en toda la aplicación.
