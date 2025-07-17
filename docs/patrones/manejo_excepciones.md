# Patrón de Manejo de Excepciones

## Introducción

Este documento describe el patrón de manejo de excepciones implementado en la aplicación, que consta de tres componentes principales:

1. **Unit of Work (UoW)**: Gestiona transacciones atómicas y captura excepciones técnicas.
2. **Mapeador de Excepciones**: Traduce excepciones técnicas a excepciones de dominio.
3. **Manejador Global de Excepciones**: Convierte excepciones de dominio a respuestas HTTP apropiadas.

Este enfoque garantiza una separación clara de responsabilidades y un manejo consistente de errores en toda la aplicación.

## Diagrama de Flujo

```
┌─────────────┐     ┌─────────────────┐     ┌───────────────────┐     ┌───────────────┐
│  Excepción  │     │   Unit of Work  │     │  Mapeador de      │     │  Manejador    │     ┌───────────┐
│  Técnica    │────▶│   (SQLAlchemy)  │────▶│  Excepciones      │────▶│  Global       │────▶│  Respuesta│
│  (DB, etc)  │     │                 │     │                   │     │  (FastAPI)    │     │  HTTP     │
└─────────────┘     └─────────────────┘     └───────────────────┘     └───────────────┘     └───────────┘
                          │                                                   ▲
                          │                                                   │
                          │           ┌─────────────────────┐                 │
                          └──────────▶│  Excepción de       │─────────────────┘
                                     │  Dominio            │
                                     └─────────────────────┘
```

## 1. Unit of Work (UoW)

El patrón Unit of Work encapsula una transacción de base de datos y garantiza que todas las operaciones dentro de la transacción sean atómicas: o todas tienen éxito o ninguna se aplica.

### Implementación

```python
class SQLAlchemyUnitOfWork(IUnitOfWork):
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            # Si hay una excepción, hacer rollback
            await self.rollback()
            
            # Si es una excepción de dominio, propagarla directamente
            if isinstance(exc_val, DominioExcepcion):
                logger.error(f"UnitOfWork: Error durante commit/rollback: {str(exc_val)}")
                # No envolvemos excepciones de dominio
                return False
                
            # Si es una excepción técnica, mapearla a una excepción de dominio
            logger.error(f"UnitOfWork: Error técnico: {str(exc_val)}", exc_info=True)
            mapped_exception = ExcepcionesMapper.map_exception(exc_val)
            
            # Propagar la excepción mapeada
            raise mapped_exception from exc_val
        
        # Si no hay excepción, hacer commit
        await self.commit()
        return False  # Propagar la excepción si la hay
```

### Características Clave

- **Contexto Asíncrono**: Utiliza `async with` para gestionar el ciclo de vida de la transacción.
- **Atomicidad**: Garantiza que todas las operaciones se confirmen o se reviertan como una unidad.
- **Detección de Excepciones**: Distingue entre excepciones de dominio y técnicas.
- **Integración con Mapeador**: Utiliza el mapeador para traducir excepciones técnicas.

## 2. Mapeador de Excepciones

El mapeador de excepciones traduce excepciones técnicas específicas (como errores de SQLAlchemy) a excepciones de dominio más significativas y desacopladas de la tecnología subyacente.

### Implementación

```python
class ExcepcionesMapper:
    @staticmethod
    def map_exception(exception: Exception) -> DominioExcepcion:
        """
        Mapea excepciones técnicas a excepciones de dominio.
        """
        # Timeout de operaciones
        if isinstance(exception, asyncio.TimeoutError):
            return TimeoutDBError()
            
        # Errores de integridad (claves únicas, foráneas, etc.)
        if isinstance(exception, IntegrityError):
            return ExcepcionesMapper._map_integrity_error(exception)
            
        # Errores operacionales (conexión, permisos, etc.)
        if isinstance(exception, OperationalError):
            return ExcepcionesMapper._map_operational_error(exception)
            
        # Otros errores técnicos
        return PersistenciaError(f"Error de persistencia: {str(exception)}")
```

### Características Clave

- **Desacoplamiento**: Separa la lógica de negocio de los detalles técnicos de persistencia.
- **Mensajes Significativos**: Proporciona mensajes de error más claros y orientados al dominio.
- **Extensibilidad**: Fácil de extender para manejar nuevos tipos de excepciones técnicas.
- **Preservación de Contexto**: Mantiene la excepción original como causa (`__cause__`).

## 3. Manejador Global de Excepciones

El manejador global de excepciones captura las excepciones de dominio y las traduce a respuestas HTTP apropiadas, asegurando una experiencia de API consistente.

### Implementación

```python
def registrar_manejadores_excepciones(app: FastAPI) -> None:
    # Manejador para excepciones de entidad no encontrada (404)
    @app.exception_handler(EntidadNoEncontradaError)
    @app.exception_handler(UsuarioNoEncontradoError)
    async def entidad_no_encontrada_handler(request: Request, exc: DominioExcepcion):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    # Manejador para excepciones de conflicto (409)
    @app.exception_handler(EmailYaRegistradoError)
    async def conflicto_handler(request: Request, exc: DominioExcepcion):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )
        
    # ... otros manejadores específicos ...
    
    # Manejador genérico para excepciones de dominio (400)
    @app.exception_handler(DominioExcepcion)
    async def dominio_exception_handler(request: Request, exc: DominioExcepcion):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )
```

### Características Clave

- **Mapeo HTTP Apropiado**: Asigna códigos de estado HTTP semánticamente correctos según el tipo de excepción.
- **Consistencia**: Garantiza respuestas de error uniformes en toda la API.
- **Logging**: Registra información detallada sobre las excepciones para facilitar la depuración.
- **Seguridad**: Oculta detalles técnicos sensibles en las respuestas de producción.

## Tabla de Mapeo de Excepciones a Códigos HTTP

| Excepción de Dominio | Código HTTP | Descripción |
|----------------------|------------|-------------|
| EntidadNoEncontradaError | 404 Not Found | Recurso solicitado no existe |
| UsuarioNoEncontradoError | 404 Not Found | Usuario específico no encontrado |
| RolNoEncontradoError | 404 Not Found | Rol específico no encontrado |
| ContactoNoEncontradoError | 404 Not Found | Contacto específico no encontrado |
| CredencialesInvalidasError | 401 Unauthorized | Credenciales incorrectas o usuario inactivo |
| EmailInvalidoError | 422 Unprocessable Entity | Formato de email inválido |
| RestriccionCheckError | 422 Unprocessable Entity | Valor no cumple con restricciones |
| EmailYaRegistradoError | 409 Conflict | Email ya existe en el sistema |
| RolYaExisteError | 409 Conflict | Rol con ese nombre ya existe |
| PermisosDBError | 403 Forbidden | Permisos insuficientes |
| ClaveForaneaError | 400 Bad Request | Referencia a entidad inexistente |
| TimeoutDBError | 504 Gateway Timeout | Operación excedió tiempo límite |
| ConexionDBError | 503 Service Unavailable | Problemas de conexión con la BD |
| PersistenciaError | 500 Internal Server Error | Otros errores de persistencia |
| DominioExcepcion | 400 Bad Request | Otras excepciones de dominio |

## Uso en Servicios

Los servicios de la aplicación utilizan el patrón Unit of Work para gestionar transacciones y manejar excepciones:

```python
async def crear_usuario(self, usuario_data: UsuarioCrear) -> Usuario:
    """Crea un nuevo usuario."""
    try:
        # Validar email (puede lanzar EmailInvalidoError)
        email = CorreoElectronico(usuario_data.email)
        
        async with self.uow as uow:
            # Verificar si el email ya existe
            usuario_existente = await uow.usuarios.get_by_email(email.value)
            if usuario_existente:
                raise EmailYaRegistradoError(email.value)
                
            # Crear y guardar el usuario
            hashed_pwd = self.hasher.hash(usuario_data.password)
            nuevo_usuario = Usuario(
                email=email.value,
                hashed_pwd=hashed_pwd,
                full_name=usuario_data.full_name,
                is_active=True
            )
            
            await uow.usuarios.save(nuevo_usuario)
            await uow.commit()
            
            return nuevo_usuario
    except DominioExcepcion as e:
        # Las excepciones de dominio se propagan directamente
        raise
    except Exception as e:
        # Otras excepciones se mapean a excepciones de dominio
        raise PersistenciaError(f"Error al crear usuario: {str(e)}") from e
```

## Beneficios del Patrón

1. **Separación de Responsabilidades**: Cada componente tiene una responsabilidad clara y única.
2. **Desacoplamiento**: La lógica de negocio no depende de detalles técnicos de persistencia.
3. **Consistencia**: Manejo uniforme de errores en toda la aplicación.
4. **Atomicidad**: Garantiza transacciones atómicas y coherentes.
5. **Experiencia de API**: Proporciona respuestas de error significativas y consistentes.
6. **Trazabilidad**: Facilita el seguimiento de errores desde la API hasta la causa raíz.

## Mejores Prácticas

1. **Excepciones Específicas**: Crear excepciones de dominio específicas para cada caso de error.
2. **Mensajes Claros**: Proporcionar mensajes de error descriptivos y orientados al usuario.
3. **Logging Adecuado**: Registrar información detallada para depuración, pero respuestas concisas para usuarios.
4. **Pruebas**: Implementar pruebas unitarias y de integración para validar el manejo de excepciones.
5. **Documentación**: Documentar todas las excepciones posibles en la documentación de la API.
