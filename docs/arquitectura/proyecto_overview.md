# API de FastAPI v2 para Gestión de Usuarios, Roles y Contactos

---

## 🚀 Visión General del Proyecto

Esta API proporciona los servicios backend para una aplicación web estática, inicialmente enfocada en la gestión de usuarios, roles y contactos. Su diseño modular y escalable permite una fácil expansión para incorporar nuevas funcionalidades y dominios de negocio en el futuro, como la gestión de operarios y rubros especializados.

Construida con **FastAPI**, **PostgreSQL**, **SQLAlchemy ORM** y **JSON Web Tokens (JWT)**, esta API sigue los principios de la **Arquitectura Limpia (Clean Architecture)** y el **Domain-Driven Design (DDD)** para garantizar la separación de preocupaciones, alta testabilidad, mantenibilidad y flexibilidad.

---

## ✨ Tecnologías y Herramientas Utilizadas

Este proyecto utiliza un stack de tecnologías modernas para asegurar rendimiento, seguridad y facilidad de desarrollo:

* **Python 3.12+**: La última versión del lenguaje, aprovechando sus mejoras de rendimiento y sintaxis.
* **UV**: Gestor de dependencias ultrarrápido y moderno para Python, reemplazo mejorado de `pip`.
* **FastAPI**: Framework web asíncrono de alto rendimiento para construir APIs REST.
* **Pydantic**: Para la validación de datos, serialización/deserialización y gestión de configuraciones.
* **SQLAlchemy 2.0**: ORM robusto y flexible para interactuar con la base de datos relacional.
* **PostgreSQL**: Base de datos relacional poderosa, fiable y escalable.
* **Redis**: Base de datos en memoria utilizada para rate limiting y caché.
* **`asyncpg` (o `psycopg2-binary`)**: Controlador asíncrono para PostgreSQL.
* **`python-dotenv`**: Para la gestión segura de variables de entorno.
* **`fastapi-limiter`**: Implementación de rate limiting para proteger la API contra abusos.
* **`passlib[argon2]`**: Hashing de contraseñas seguro utilizando el algoritmo Argon2.
* **`python-jose`**: Implementación de JSON Web Tokens (JWT) para la autenticación y autorización.
* **Uvicorn**: Servidor ASGI de alto rendimiento para ejecutar la aplicación FastAPI.
* **Docker & Docker Compose**: Para la contenerización y orquestación de la aplicación y la base de datos, facilitando el despliegue y el entorno de desarrollo.
* **Pytest**: Marco completo para la escritura y ejecución de pruebas automatizadas.

---

## 📐 Principios de Arquitectura Aplicados

La API está diseñada siguiendo una **Arquitectura Limpia (Clean Architecture)** y **Domain-Driven Design (DDD)**, lo que se traduce en una estructura de capas concéntricas donde las dependencias siempre apuntan hacia el centro. Esto garantiza:

* **Separación de Responsabilidades (SRP)**: Cada componente tiene una función única y bien definida.
* **Modularidad**: Estructura por capas que facilita el mantenimiento y la evolución.
* **Escalabilidad**: Preparada para crecer con nuevos módulos y versionado de la API.
* **Desacoplamiento (DIP)**: Los componentes son independientes e interactúan a través de interfaces (principios de Inversión de Dependencias).
* **Testabilidad**: Cada capa se puede probar de forma aislada mediante el uso de *mocks* para sus dependencias.
* **Independencia de Frameworks**: Las reglas de negocio centrales no dependen de frameworks o bibliotecas externas. Podemos cambiar FastAPI o SQLAlchemy sin reescribir la lógica de negocio.

### Capas de la Arquitectura

1.  **Capa de Dominio (El Centro)**:
    * Contiene las **entidades** y reglas de negocio centrales y puras. Es el "corazón" de la aplicación.
    * **No tiene dependencias externas** (frameworks, bases de datos).
    * Define **interfaces (puertos)** para la persistencia (repositorios) y servicios externos (logging, http).
    * Incluye **excepciones específicas** del dominio y **objetos de valor** inmutables.

2.  **Capa de Servicios (Capa de Aplicación / Casos de Uso)**:
    * Implementa los **casos de uso** o flujos de trabajo de la aplicación.
    * **Orquesta** las entidades del dominio y utiliza las interfaces de los repositorios para interactuar con los datos.
    * Depende de la capa de Dominio, pero no de la Infraestructura (Principio de Inversión de Dependencias).

3.  **Capa de Infraestructura (Implementaciones / Adaptadores)**:
    * Contiene las **implementaciones técnicas concretas** (adaptadores) para los puertos definidos en el Dominio.
    * Incluye los modelos ORM (SQLAlchemy), las implementaciones concretas de los repositorios, adaptadores para logging, middleware HTTP y servicios externos (correo electrónico).
    * Aquí es donde se configuran los frameworks y bibliotecas externas.

4.  **Capa de API (Presentación)**:
    * Adaptadores para interactuar con el mundo exterior (FastAPI).
    * Define los **endpoints REST** y maneja la validación de entrada/salida usando DTOs (Pydantic Schemas).
    * Es responsable de la **conversión** entre los DTOs (Esquemas Pydantic) y los modelos de dominio.

---

## 📁 Estructura de Directorios (Versión 2 - Profesionalizada)

Esta es la estructura detallada del proyecto, diseñada para reflejar las capas de la Arquitectura Limpia y facilitar la navegación y el desarrollo:

📁 app/
├── 📁 api/               # Capa de Presentación (FastAPI endpoints)
│   └── 📁 v2/            # Versionado de la API (ej. /api/v2)
│       ├── 📁 endpoints/ # Endpoints por recurso
│       └── api.py       # Registra routers de los endpoints
│
├── 📁 core/              # Configuración global y utilidades compartidas
│   ├── config.py
│   ├── deps.py
│   ├── eventos.py
│   ├── excepciones.py
│   └── 📁 seguridad/
│       ├── hashing.py
│       └── jwt.py
│
├── 📁 dominio/           # Capa del Dominio (reglas de negocio puras)
│   ├── 📁 entidades/     # Entidades del negocio (sin ORM)
│   ├── 📁 excepciones/   # Excepciones del dominio
│   ├── 📁 interfaces/    # Puertos (interfaces HTTP, logging...)
│   ├── 📁 objetos_valor/ # Conceptos inmutables con significado
│   └── 📁 repositorios/  # Interfaces de acceso a datos
│
├── 📁 infraestructura/   # Adaptadores que implementan puertos del dominio
│   ├── 📁 adaptadores/   # Logging, middleware HTTP
│   ├── 📁 correo_electronico/  # SMTP u otros proveedores
│   └── 📁 persistencia/  # SQLAlchemy, PostgreSQL, etc.
│       ├── base.py
│       ├── modelos_orm.py
│       ├── sesion.py
│       └── 📁 implementaciones_repositorios/
│
├── 📁 servicios/         # Casos de Uso (capa de aplicación)
│   ├── autenticacion_servicio.py
│   ├── contacto_servicio.py
│   └── ...
│
├── 📁 esquemas/          # DTOs (Data Transfer Objects) con Pydantic
│   ├── contacto.py
│   ├── usuario.py
│   └── ...
│
└── main.py              # Punto de entrada FastAPI

📁 tests/                 # Tests organizados por capa
├── dominio/             # Tests unitarios del dominio
├── infraestructura/     # Tests integración de adaptadores
├── api/v2/endpoints/    # Tests de endpoints
└── core/seguridad/      # Tests de hashing y JWT



## 🛠️ Lógica de Negocio Principal y Funcionalidades

Esta API proporciona las siguientes funcionalidades clave, siguiendo los principios de la arquitectura:

* **Gestión de Usuarios**:
    * Operaciones CRUD (Crear, Leer, Actualizar, Eliminar) para usuarios.
    * Asignación de roles a usuarios (ej. `admin`, `empleador`, `candidato`).
    * Hashing seguro de contraseñas con **Argon2** para máxima protección.
* **Autenticación y Autorización**:
    * Inicio de sesión basado en correo electrónico y contraseña.
    * Generación y validación de **tokens JWT** para acceder a recursos protegidos.
    * Protección de rutas basada en los roles y permisos del usuario.
* **Gestión de Roles**:
    * Operaciones CRUD básicas para definir roles en el sistema.
    * Roles predefinidos como "admin", "empleador", "candidato".
* **Gestión de Contactos**:
    * Registro de información de contacto de personas interesadas (nombre, correo electrónico, mensaje, etc.).
    * Mecanismo para que los administradores puedan marcar los contactos como "leídos" para seguimiento.

---

## 🗄️ Esquema de Base de Datos

La base de datos PostgreSQL se estructura de la siguiente manera para soportar las funcionalidades de la API. Esta sección es crucial para entender el modelo de datos.

### Tabla: `usuarios`

Representa a los usuarios del sistema.

| Columna     | Tipo      | Descripción                                   |
| :---------- | :-------- | :-------------------------------------------- |
| `id`        | `UUID`    | Identificador único del usuario (clave primaria) |
| `email`     | `VARCHAR` | Correo electrónico del usuario (único)        |
| `hashed_pwd`| `VARCHAR` | Contraseña hasheada con Argon2                |
| `full_name` | `VARCHAR` | Nombre completo del usuario                   |
| `is_active` | `BOOLEAN` | Indica si la cuenta del usuario está activa   |
| `created_at`| `TIMESTAMP`| Fecha y hora de creación del registro        |
| `updated_at`| `TIMESTAMP`| Fecha y hora de la última actualización del registro |

### Tabla: `roles`

Define los diferentes roles disponibles en el sistema.

| Columna     | Tipo      | Descripción                                   |
| :---------- | :-------- | :-------------------------------------------- |
| `id`        | `UUID`    | Identificador único del rol (clave primaria)   |
| `name`      | `VARCHAR` | Nombre único del rol (ej. "admin", "empleador") |
| `description`| `TEXT`    | Descripción detallada del rol                 |
| `created_at`| `TIMESTAMP`| Fecha y hora de creación del registro        |

### Tabla: `user_roles`

Tabla intermedia para la relación **muchos a muchos** entre `usuarios` y `roles`. Un usuario puede tener múltiples roles, y un rol puede ser asignado a múltiples usuarios.

| Columna       | Tipo      | Descripción                                   |
| :------------ | :-------- | :-------------------------------------------- |
| `user_id`     | `UUID`    | Clave foránea que referencia `usuarios.id`    |
| `role_id`     | `UUID`    | Clave foránea que referencia `roles.id`       |
| `assigned_at` | `TIMESTAMP`| Fecha y hora de la asignación del rol        |

**Nota**: La clave primaria de esta tabla debe ser una **clave compuesta** formada por `(user_id, role_id)`.

### Tabla: `contacts`

Almacena la información de contacto de personas interesadas que se comunican a través de la web.

| Columna     | Tipo      | Descripción                                   |
| :---------- | :-------- | :-------------------------------------------- |
| `id`        | `UUID`    | Identificador único del contacto (clave primaria) |
| `name`      | `VARCHAR` | Nombre de la persona que realiza el contacto   |
| `email`     | `VARCHAR` | Correo electrónico de la persona de contacto  |
| `phone`     | `VARCHAR` | Número de teléfono de contacto (opcional)     |
| `message`   | `TEXT`    | Contenido del mensaje o consulta              |
| `is_read`   | `BOOLEAN` | Indica si el contacto ha sido revisado por un administrador |
| `created_at`| `TIMESTAMP`| Fecha y hora de creación del registro        |
| `updated_at`| `TIMESTAMP`| Fecha y hora de la última actualización del registro |

---



