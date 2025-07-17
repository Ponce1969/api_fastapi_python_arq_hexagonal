# 🚀 Guía de Implementación: Desarrollo de la API v2

Este documento es una **lista de verificación paso a paso** diseñada para guiar a los desarrolladores a través del proceso de implementación de nuevas funcionalidades o el mantenimiento de las existentes en la API v2.

**Objetivo**: Asegurar que el código se escriba y se coloque en la capa y ubicación correcta, manteniendo la integridad de la Arquitectura Limpia y el Domain-Driven Design.

**Instrucciones**:
* Completa cada paso en orden.
* Una vez que un paso esté **completado y revisado**, márcalo con una `[x]` dentro del casillero.
* **No saltes pasos**. Si un paso no aplica a tu tarea actual, discútelo con el líder del equipo antes de marcarlo.
* Si tienes dudas sobre dónde debe ir el código o cómo implementar algo, consulta primero el `README.md` y luego a un compañero con más experiencia.

---

## ✅ Lista de Verificación de Desarrollo

### Fase 1: Planificación y Diseño (Antes de escribir código)

* [ ] 1. **Comprender el Requisito**: Entender completamente la nueva funcionalidad o el cambio solicitado.
* [ ] 2. **Identificar el Dominio**: Determinar a qué **dominios de negocio** (ej., `usuarios`, `roles`, `contactos`, `operarios`) afecta esta funcionalidad.
* [ ] 3. **Modelado de Entidades de Dominio**: Si la funcionalidad introduce nuevos conceptos de negocio, esbozar las **nuevas entidades puras** en `app/dominio/entidades/` (clases Python simples, sin dependencias de ORM).
* [ ] 4. **Definir Interfaces de Repositorio (Puertos)**: Si se necesita persistencia para nuevas entidades o nuevas operaciones de persistencia, definir las **nuevas interfaces abstractas (Protocolos/ABCs)** en `app/dominio/repositorios/`.
* [ ] 5. **Definir Interfaces de Servicios Externos**: Si la funcionalidad requiere interacción con servicios externos (ej., logging, email, HTTP), y no existen, definir las **interfaces (Protocolos/ABCs)** en `app/dominio/interfaces/`.
* [ ] 6. **Esbozar Casos de Uso (Servicios)**: Pensar en la **lógica de negocio** y cómo se orquestarán las entidades y repositorios en la capa de `app/servicios/`.
* [ ] 7. **Diseñar Esquemas Pydantic (DTOs)**: Determinar qué datos se recibirán y qué datos se enviarán, y esbozar los **esquemas Pydantic** correspondientes en `app/esquemas/`.
* [ ] 8. **Actualizar el Esquema de Base de Datos**: Si se necesitan nuevas tablas o columnas, actualizar mentalmente (o en un borrador) el **esquema de base de datos**.

### Fase 2: Implementación - De adentro hacia afuera (Dominio y Abstracciones)

* [ ] 9. **Crear Entidades de Dominio**: Implementar las **clases de entidades puras** en `app/dominio/entidades/`.
* [ ] 10. **Crear Objetos de Valor**: Si aplica, implementar **objetos de valor inmutables** en `app/dominio/objetos_valor/`.
* [ ] 11. **Definir Excepciones de Dominio**: Crear **excepciones personalizadas** relevantes para la lógica de negocio en `app/dominio/excepciones/`.
* [ ] 12. **Codificar Interfaces de Repositorio**: Escribir las **clases abstractas o protocolos** para los repositorios en `app/dominio/repositorios/`. (Ej. `class IUsuarioRepositorio(Protocol): ...`)
* [ ] 13. **Codificar Interfaces de Servicios Externos**: Si se definieron, escribir las **clases abstractas o protocolos** para los servicios externos en `app/dominio/interfaces/`.

### Fase 3: Implementación - Infraestructura (Concreciones y Adaptadores)

* [ ] 14. **Actualizar Modelos ORM**: Si se necesitan nuevas tablas o modificaciones, actualizar `app/infraestructura/persistencia/modelos_orm.py` para mapear las **entidades de dominio a las tablas de la base de datos** usando SQLAlchemy.
* [ ] 15. **Crear Migraciones de DB**: Utilizar Alembic (o tu herramienta de migración) para generar y aplicar las **migraciones de base de datos** basadas en los cambios de `modelos_orm.py`.
    * `alembic revision --autogenerate -m "Descripción de los cambios"`
    * `alembic upgrade head`
* [ ] 16. **Implementar Repositorios Concretos**: En `app/infraestructura/persistencia/implementaciones_repositorios/`, implementar las **clases concretas del repositorio** que satisfacen las interfaces definidas en `app/dominio/repositorios/`. (Ej. `class UsuarioRepositorioImpl(IUsuarioRepositorio): ...`). Estas clases interactuarán con los `modelos_orm`.
* [ ] 17. **Implementar Adaptadores de Servicios Externos**: Si se definieron nuevas interfaces de servicios externos (ej., logging, email), crear sus **implementaciones concretas** en `app/infraestructura/adaptadores/` o `app/infraestructura/correo_electronico/`.

### Fase 4: Lógica de Aplicación (Servicios) y Presentación (API)

* [ ] 18. **Implementar Lógica de Servicio**: Codificar la **lógica de negocio central** en `app/servicios/`. Asegurarse de que estos servicios **dependan de las interfaces de repositorio**, no de sus implementaciones concretas.
* [ ] 19. **Crear Esquemas Pydantic**: Implementar los **DTOs de entrada y salida** en `app/esquemas/` que validarán los datos de la API y formatearán las respuestas.
* [ ] 20. **Crear o Modificar Endpoints de API**: En `app/api/v1/endpoints/`, crear o actualizar los **endpoints de FastAPI** (`auth.py`, `usuarios.py`, etc.).
* [ ] 20. **Crear o Modificar Endpoints de API**: En `app/api/v2/endpoints/`, crear o actualizar los **endpoints de FastAPI** (`auth.py`, `usuarios.py`, etc.).
    * Asegurarse de que los endpoints reciban **esquemas Pydantic** como entrada.
    * Convertir los esquemas de entrada a **entidades de dominio** antes de pasarlos a los servicios.
    * Invocar los **servicios de la capa de aplicación**.
    * Convertir las entidades de dominio o resultados del servicio a **esquemas Pydantic de salida** antes de devolver la respuesta.
    * Utilizar la **inyección de dependencias de FastAPI** (`app/core/deps.py`) para obtener las instancias de los servicios y otros recursos.
* [ ] 21. **Registrar Endpoints**: Asegurarse de que los nuevos routers de FastAPI estén registrados en `app/api/v2/api.py`.

### Fase 5: Pruebas y Revisión

* [ ] 22. **Escribir Tests Unitarios de Dominio**: Crear tests para las **entidades**, **objetos de valor** y **servicios** (mockeando las dependencias del servicio) en `tests/dominio/`.
* [ ] 23. **Escribir Tests de Integración de Repositorios**: Crear tests que verifiquen las **implementaciones de repositorio** interactuando con una base de datos de prueba en `tests/infraestructura/persistencia/implementaciones_repositorios/`.
* [ ] 24. **Escribir Tests de Integración de API**: Crear tests para los **endpoints de FastAPI** usando el `TestClient` de FastAPI en `tests/api/v2/endpoints/`.
* [ ] 25. **Ejecutar Todas las Pruebas**: Asegurarse de que todas las pruebas pasen (`pytest`).
* [ ] 26. **Revisión de Código (Code Review)**: Obtener una revisión de código de un compañero. Prestar especial atención a la ubicación del código, la separación de responsabilidades y la adhesión a los principios de la arquitectura.
* [ ] 27. **Documentación (Opcional pero Recomendado)**: Si la funcionalidad es compleja, añadir notas en el `README.md` o en la documentación interna.

---


## 📈 Plan de Desarrollo y Pasos a Seguir (Para Programadores Junior)

Para los nuevos miembros del equipo, esta sección describe el flujo de trabajo recomendado para implementar nuevas funcionalidades o entender las existentes.

### 1. Entender el Dominio (Capa `app/dominio/`)

* **Lee las `entidades/`**: Comprende los objetos de negocio puros (ej. `Usuario`, `Rol`). Son clases Python simples sin lógica de base de datos.
* **Revisa las `interfaces/`**: Estas son las "promesas" o contratos. Por ejemplo, `usuario_repositorio.py` define qué operaciones se pueden hacer con un usuario (buscar por email, crear, etc.), ¡pero no cómo se hacen!
* **Familiarízate con los `objetos_valor/`**: Cómo se modelan conceptos como un `CorreoElectronico` de forma inmutable y segura.
* **Estudia las `excepciones/`**: Entiende qué errores específicos de negocio pueden ocurrir.

### 2. Explorar la Lógica de Negocio (Capa `app/servicios/`)

* Aquí es donde reside la "magia" de la aplicación. Los archivos en `app/servicios/` (ej. `usuario_servicio.py`) implementan los casos de uso.
* Verás cómo los servicios interactúan con las **interfaces** de los repositorios (no con las implementaciones directas) y manipulan las **entidades** de dominio.
* Esta capa no conoce FastAPI ni SQLAlchemy; solo se enfoca en resolver problemas de negocio.

### 3. Entender la Persistencia (Capa `app/infraestructura/persistencia/`)

* **`modelos_orm.py`**: Aquí verás cómo nuestras entidades de dominio se "mapean" a las tablas de la base de datos usando SQLAlchemy.
* **`implementaciones_repositorios/`**: Estos son los "adaptadores" que toman las interfaces de `app/dominio/repositorios/` y las implementan utilizando SQLAlchemy para interactuar con la base de datos. Por ejemplo, `usuario_repositorio_impl.py` implementa `IUsuarioRepositorio`.
* **`sesion.py`**: Aprende cómo se configura y gestiona la conexión a la base de datos.

### 4. Comprender la Presentación (Capa `app/api/`)

* **`esquemas/`**: Son tus DTOs de Pydantic. Sirven para validar la entrada de datos de las requests HTTP y para formatear la salida de las respuestas.
* **`endpoints/`**: Contienen las funciones de los *path operations* de FastAPI. Verás cómo reciben los esquemas, invocan los servicios de la capa de aplicación y devuelven respuestas.
* **Inyección de Dependencias (DI)**: Presta atención a cómo FastAPI inyecta las dependencias (ej. objetos de servicio, sesiones de DB) en los *endpoints* a través de `app/core/deps.py`.

### 5. Cómo se Conecta Todo (`main.py` y `core/`)

* **`main.py`**: Es el punto de entrada. Aquí se inicializa la aplicación FastAPI y se integran los routers de la API.
* **`core/config.py`**: Gestiona las variables de entorno y la configuración de la aplicación.
* **`core/seguridad/`**: Contiene las utilidades transversales de seguridad como el hashing de contraseñas y la gestión de JWT, que son usadas por los servicios (especialmente los de autenticación).
* **Logging y Middleware**: Observa cómo se configuran el sistema de logging (`app/infraestructura/adaptadores/logging/standard_logger.py`) y el middleware HTTP (`app/infraestructura/adaptadores/http/fastapi_middleware.py`) para una observabilidad robusta.

### 6. Contribuyendo con Nueva Funcionalidad

1.  **Define el Dominio**: Si es una nueva funcionalidad, ¿necesitas nuevas **entidades** en `app/dominio/entidades/`? ¿Nuevas **interfaces de repositorio** en `app/dominio/repositorios/`?
2.  **Crea el Servicio**: Implementa la lógica de negocio en un nuevo archivo de servicio en `app/servicios/`. Este servicio utilizará las interfaces de repositorio que hayas definido.
3.  **Implementa el Repositorio**: En `app/infraestructura/persistencia/implementaciones_repositorios/`, crea la implementación concreta del repositorio usando SQLAlchemy que satisfaga la interfaz definida en el dominio. Si es necesario, añade o modifica modelos ORM en `app/infraestructura/persistencia/modelos_orm.py`.
4.  **Define los Esquemas**: En `app/esquemas/`, crea los esquemas Pydantic necesarios para la entrada y salida de datos en la API.
5.  **Crea el Endpoint**: En `app/api/v2/endpoints/`, crea un nuevo archivo (o modifica uno existente) para exponer la funcionalidad a través de HTTP, utilizando el servicio que creaste.
6.  **Escribe Pruebas**: ¡Es crucial! Escribe tests unitarios para tu dominio y servicios, y tests de integración para tus repositorios y endpoints, siguiendo la estructura en `tests/`.

---

## 🧪 Pruebas

El proyecto incluye un conjunto de pruebas exhaustivas para cada capa de la arquitectura, garantizando la calidad y el comportamiento esperado.

* **Tests Unitarios**: Se enfocan en probar unidades pequeñas de código de forma aislada (ej. entidades, servicios con *mocks*).
* **Tests de Integración**: Verifican la interacción entre componentes (ej. repositorios con la base de datos, endpoints con los servicios).

Para ejecutar las pruebas, asegúrate de tener `pytest` instalado y un entorno de base de datos de prueba configurado (usualmente a través de Docker Compose para tests de integración).

```bash
uv pip install -e .[dev,test]  # Instala las dependencias de desarrollo y testing
pytest                         # Ejecuta todas las pruebas

⚙️ Configuración y Ejecución

Requisitos

    Docker y Docker Compose (para el entorno de desarrollo y base de datos)

    Python 3.12+

Pasos para el Entorno Local

    Clona el Repositorio:
    Bash

git clone [URL_DE_TU_REPOSITORIO]
cd api_statica # O el nombre de tu carpeta de proyecto

Configura el Entorno (.env):
Crea un archivo .env en la raíz del proyecto (al mismo nivel que docker-compose.yml) con las variables de entorno necesarias. Puedes usar example.env como plantilla.
Fragmento de código

# .env
DB_HOST=db
DB_PORT=5432
DB_USER=user
DB_PASSWORD=password
DB_NAME=app_db

APP_HOST=0.0.0.0
APP_PORT=8000

JWT_SECRET_KEY=TU_SECRETO_SUPER_SEGURO_PARA_JWT # ¡Cambia esto en producción!
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

LOG_LEVEL=DEBUG # INFO en producción
DEBUG=True      # False en producción

# Configuración SMTP (si se usa para envío de correos)
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_email@example.com
SMTP_PASSWORD=your_email_password
SMTP_USE_TLS=True

Levanta la Base de Datos con Docker Compose:
Bash

docker compose up -d db

Crea y Activa el Entorno Virtual con UV:
Bash

uv venv
source .venv/bin/activate  # En Linux/macOS
# .venv\Scripts\activate   # En Windows

Instala las Dependencias:
Bash

uv pip install -e ".[dev]" # Instala las dependencias de desarrollo. `.[test]` si vas a ejecutar tests.

Ejecuta las Migraciones (Si usas Alembic o similar):
Si utilizas un sistema de migraciones (como Alembic), este es el momento de aplicar las migraciones a tu base de datos:
Bash

# Ejemplo con Alembic (asumiendo que ya está configurado)
# alembic revision --autogenerate -m "Initial migration"
# alembic upgrade head

    Nota para Juniors: Al principio, puedes optar por que SQLAlchemy recree las tablas automáticamente en desarrollo (usando Base.metadata.create_all(engine) en un script, por ejemplo), pero para producción y un desarrollo serio, las migraciones son esenciales.

Inicia la Aplicación FastAPI:
Bash

    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

        --reload es útil para desarrollo, reinicia el servidor automáticamente al detectar cambios en el código.

    Accede a la API:
    Una vez iniciada, puedes acceder a la documentación interactiva de Swagger UI en:
    http://localhost:8000/docs
    Y a ReDoc en:
    http://localhost:8000/redoc

🔒 Logging Global y Depuración

El proyecto implementa un sistema de logging profesional y middleware para una observabilidad robusta, siguiendo los principios de Arquitectura Limpia y el patrón de puertos y adaptadores.

¿Cómo funciona el Logging?

La configuración global de logging se maneja en app/main.py y app/infraestructura/adaptadores/logging/standard_logger.py, controlando el nivel de detalle en toda la aplicación.

    Configuración Automática por Entorno:

        Desarrollo: Si DEBUG en settings es True, el nivel de logging es DEBUG. Muestra información detallada para depuración.

        Producción: Si DEBUG es False, el nivel de logging es INFO. Solo se muestran mensajes importantes, reduciendo el ruido y protegiendo información sensible.

    Ejemplo de Registro:
    En métodos de repositorio (ej. list_filtered en sqlalchemy_base_repositorio.py), se registra automáticamente:

        Los filtros aplicados (excluyendo contraseñas u otros datos sensibles).

        Los parámetros de paginación (skip, limit).

        El nombre del modelo consultado.
        Esta información se loguea solo si el nivel es DEBUG.

    2025-07-05 10:30:00,123 - app.infraestructura.persistencia.implementaciones_repositorios.sqlalchemy_base_repositorio - DEBUG - [Usuario] Filtros aplicados: {'email': 'test@example.com'}, skip=0, limit=100

¿Cómo cambiar el Entorno?

El entorno se controla desde la configuración en .env (y app/core/config.py):
Fragmento de código

# .env
DEBUG=True # Cambia a False en producción
LOG_LEVEL=DEBUG # Cambia a INFO en producción

Recomendaciones

    Mantén DEBUG = True y LOG_LEVEL = DEBUG solo durante el desarrollo.

    En producción, usa DEBUG = False y LOG_LEVEL = INFO para evitar logs sensibles y mejorar el rendimiento.

    Para solucionar problemas en producción, puedes activar temporalmente el nivel DEBUG o WARNING, pero recuerda volver a INFO cuando termines.

🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor, revisa el Plan de Desarrollo y la Estructura de Directorios antes de comenzar. Sigue las prácticas de código limpio y crea pruebas para tus cambios.

📝 Licencia

Este proyecto está bajo la Licencia MIT.
