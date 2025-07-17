# Patrón Unit of Work y Manejo de Excepciones

## Introducción

Este documento describe la implementación del patrón Unit of Work (UoW) en nuestra aplicación, su integración con el sistema de mapeo de excepciones, y las mejores prácticas para su uso efectivo.

## ¿Qué es el Patrón Unit of Work?

El patrón Unit of Work es un patrón de diseño que permite agrupar múltiples operaciones de base de datos en una única transacción atómica, garantizando que todas las operaciones tengan éxito o ninguna se aplique (principio de atomicidad).

En nuestra arquitectura hexagonal, el Unit of Work actúa como una capa de abstracción entre los servicios de aplicación y los repositorios, permitiendo:

1. **Transacciones atómicas**: Todas las operaciones de base de datos se ejecutan en una única transacción.
2. **Consistencia de datos**: Se garantiza que los datos permanezcan en un estado consistente.
3. **Desacoplamiento**: Los servicios no necesitan conocer los detalles de la gestión de transacciones.
4. **Centralización del manejo de errores**: Las excepciones técnicas se mapean a excepciones de dominio de forma centralizada.

## Componentes Principales

### 1. Interfaces

#### `IUnitOfWork` (Dominio)

```python
# app/dominio/interfaces/unit_of_work.py
from abc import ABC, abstractmethod

class IUnitOfWork(ABC):
    """
    Interfaz para el patrón Unit of Work.
    Define el contrato que deben cumplir todas las implementaciones.
    """
    
    @abstractmethod
    async def commit(self):
        """Confirma la transacción actual."""
        pass
        
    @abstractmethod
    async def rollback(self):
        """Revierte la transacción actual."""
        pass
```

### 2. Implementaciones

#### `SQLAlchemyUnitOfWork` (Infraestructura)

```python
# app/infraestructura/persistencia/unit_of_work.py
from app.dominio.interfaces.unit_of_work import IUnitOfWork
from app.infraestructura.persistencia.excepciones.persistencia_excepciones import ExcepcionesMapper

class SQLAlchemyUnitOfWork(IUnitOfWork):
    """
    Implementa el patrón Unit of Work para SQLAlchemy.
    """
    # ... (implementación)
```

### 3. Sistema de Mapeo de Excepciones

#### `ExcepcionesMapper` (Infraestructura)

```python
# app/infraestructura/persistencia/excepciones/persistencia_excepciones.py
from app.dominio.excepciones.dominio_excepciones import DominioExcepcion

class ExcepcionesMapper:
    """
    Clase que mapea excepciones técnicas de SQLAlchemy a excepciones de dominio.
    """
    # ... (implementación)
```

## Flujo de Trabajo

1. **Inicio de la transacción**: Al entrar en el contexto del UnitOfWork (`async with uow as uow:`).
2. **Operaciones de repositorio**: Los servicios utilizan los repositorios expuestos por el UoW.
3. **Finalización de la transacción**: Al salir del contexto:
   - Si no hay excepciones, se hace commit.
   - Si hay excepciones, se hace rollback.
   - Las excepciones técnicas se mapean a excepciones de dominio.

## Uso en Servicios

### Ejemplo Básico

```python
class UsuarioServicio:
    def __init__(self, uow: IUnitOfWork, hasher: IHasher):
        self.uow = uow
        self.hasher = hasher
        
    async def crear_usuario(self, usuario_data: UsuarioCrear) -> Usuario:
        async with self.uow as uow:
            # Verificar si el email ya existe
            email = CorreoElectronico(usuario_data.email)
            existing_user = await uow.usuarios.get_by_email(email.value)
            if existing_user:
                raise EmailYaRegistradoError(email.value)
                
            # Crear y guardar el nuevo usuario
            hashed_password = self.hasher.hash(usuario_data.password)
            usuario = Usuario(
                id=None,
                email=email.value,
                password=hashed_password,
                full_name=usuario_data.full_name,
                is_active=True,
                is_superuser=usuario_data.is_superuser
            )
            
            return await uow.usuarios.save(usuario)
```

### Operaciones Complejas con Múltiples Repositorios

```python
async def asignar_rol_a_usuario(self, usuario_id: int, rol_id: int) -> Usuario:
    async with self.uow as uow:
        # Obtener usuario y rol
        usuario = await uow.usuarios.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con ID {usuario_id} no encontrado")
            
        rol = await uow.roles.get_by_id(rol_id)
        if not rol:
            raise RolNoEncontradoError(f"Rol con ID {rol_id} no encontrado")
            
        # Asignar rol al usuario
        await uow.roles.asignar_a_usuario(usuario.id, rol.id)
        
        # Actualizar usuario con nuevo rol
        usuario.roles.append(rol)
        return usuario
```

### Acceso Directo a la Sesión

Para casos especiales donde se necesita acceso directo a la sesión de SQLAlchemy:

```python
async def ejecutar_consulta_compleja(self, parametros: dict) -> List[ResultadoDTO]:
    async with self.uow as uow:
        async with uow.begin() as session:
            # Operaciones directas con la sesión
            query = text("SELECT * FROM tabla WHERE condicion = :param")
            result = await session.execute(query, {"param": parametros["valor"]})
            return [ResultadoDTO(**row) for row in result]
```

## Manejo de Excepciones

### Tipos de Excepciones

1. **Excepciones de Dominio**: Representan errores de negocio (ej. `EmailYaRegistradoError`).
2. **Excepciones Técnicas**: Errores de infraestructura (ej. `SQLAlchemyError`).

### Flujo de Mapeo de Excepciones

1. Se captura una excepción técnica en el UnitOfWork.
2. Se pasa al `ExcepcionesMapper` para traducirla a una excepción de dominio.
3. Se relanza la excepción de dominio, preservando el traceback original.

### Ejemplo de Mapeo

```
IntegrityError (email duplicado) → EmailYaRegistradoError
NoResultFound → UsuarioNoEncontradoError
SQLAlchemyError (genérica) → DominioExcepcion
```

## Mejores Prácticas

1. **Siempre usar el UnitOfWork en servicios**:
   ```python
   async with self.uow as uow:
       # Operaciones de repositorio
   ```

2. **No mezclar UnitOfWork con repositorios individuales**:
   ```python
   # INCORRECTO
   async with self.uow as uow:
       usuario = await uow.usuarios.get_by_id(id)
       # No usar repositorios individuales aquí
       await self.otro_repositorio.save(algo)  # ❌
   ```

3. **No hacer commit/rollback manualmente en servicios**:
   ```python
   # INCORRECTO
   async with self.uow as uow:
       usuario = await uow.usuarios.get_by_id(id)
       await uow.commit()  # ❌ El UoW maneja esto automáticamente
   ```

4. **Manejar excepciones de dominio en la capa de API**:
   ```python
   @router.post("/usuarios/")
   async def crear_usuario(usuario: UsuarioCrear, servicio: UsuarioServicio = Depends(get_usuario_servicio)):
       try:
           return await servicio.crear_usuario(usuario)
       except EmailYaRegistradoError as e:
           raise HTTPException(status_code=400, detail=str(e))
   ```

5. **No capturar excepciones técnicas en servicios**:
   ```python
   # INCORRECTO
   async def crear_usuario(self, usuario_data: UsuarioCrear):
       try:
           async with self.uow as uow:
               # ...
       except SQLAlchemyError as e:  # ❌ El UoW ya maneja esto
           # ...
   ```

6. **Usar el método `begin()` solo cuando sea necesario**:
   ```python
   # Solo para operaciones avanzadas que requieren acceso directo a la sesión
   async with uow.begin() as session:
       result = await session.execute(query_especial)
   ```

## Diagnóstico y Solución de Problemas

### Logs Relevantes

El UnitOfWork genera logs detallados que ayudan a diagnosticar problemas:

- `UnitOfWork: Realizando commit de la transacción`
- `UnitOfWork: Realizando rollback debido a excepción: {tipo_excepcion}`
- `UnitOfWork: Mapeando excepción técnica {tipo_excepcion} a excepción de dominio`

### Problemas Comunes

1. **Excepción: "Cannot begin transaction on a UnitOfWork not yet entered"**
   - Causa: Se intentó usar `uow.begin()` fuera del contexto principal del UoW.
   - Solución: Asegurarse de que `begin()` se llame dentro de un bloque `async with uow:`.

2. **Excepción de dominio no esperada**
   - Causa: Una excepción técnica se mapeó a una excepción de dominio.
   - Diagnóstico: Revisar los logs para ver el tipo de excepción original.

3. **Operaciones que no se persisten**
   - Causa: Se está usando un repositorio fuera del contexto del UoW.
   - Solución: Asegurarse de que todas las operaciones de repositorio se realicen dentro del contexto del UoW.

## Conclusión

El patrón Unit of Work, combinado con el sistema de mapeo de excepciones, proporciona una base sólida para la gestión de transacciones y el manejo de errores en nuestra aplicación. Siguiendo las mejores prácticas descritas en este documento, se garantiza la consistencia de los datos y se mejora la mantenibilidad del código.

## Referencias

- [Patrón Unit of Work - Martin Fowler](https://martinfowler.com/eaaCatalog/unitOfWork.html)
- [Arquitectura Hexagonal - Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
- [SQLAlchemy - Documentación Oficial](https://docs.sqlalchemy.org/en/14/orm/session_basics.html)
