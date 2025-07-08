
# --- Creación de la estructura principal ---
echo "Creando estructura de directorios para app_v2..."

# Directorio principal de la aplicación
mkdir -p app

# --- Capa de API (Presentación) ---
mkdir -p app/api/v2/endpoints
touch app/api/__init__.py
touch app/api/v2/__init__.py
touch app/api/v2/api.py
touch app/api/v2/endpoints/__init__.py

# --- Core: Configuración y utilidades compartidas ---
mkdir -p app/core/seguridad
touch app/core/__init__.py
touch app/core/config.py
touch app/core/deps.py
touch app/core/eventos.py
touch app/core/excepciones.py
touch app/core/seguridad/__init__.py
touch app/core/seguridad/hashing.py
touch app/core/seguridad/jwt.py

# --- Capa de Dominio (El Corazón) ---
mkdir -p app/dominio/entidades
mkdir -p app/dominio/excepciones
mkdir -p app/dominio/interfaces
mkdir -p app/dominio/objetos_valor
mkdir -p app/dominio/repositorios
touch app/dominio/__init__.py
touch app/dominio/entidades/__init__.py
touch app/dominio/excepciones/__init__.py
touch app/dominio/interfaces/__init__.py
touch app/dominio/objetos_valor/__init__.py
touch app/dominio/repositorios/__init__.py

# --- Capa de Infraestructura (Adaptadores) ---
mkdir -p app/infraestructura/adaptadores/logging
mkdir -p app/infraestructura/adaptadores/http
mkdir -p app/infraestructura/correo_electronico
mkdir -p app/infraestructura/persistencia/implementaciones_repositorios
touch app/infraestructura/__init__.py
touch app/infraestructura/adaptadores/__init__.py
touch app/infraestructura/adaptadores/logging/__init__.py
touch app/infraestructura/adaptadores/http/__init__.py
touch app/infraestructura/correo_electronico/__init__.py
touch app/infraestructura/persistencia/__init__.py
touch app/infraestructura/persistencia/base.py
touch app/infraestructura/persistencia/modelos_orm.py
touch app/infraestructura/persistencia/sesion.py
touch app/infraestructura/persistencia/implementaciones_repositorios/__init__.py

# --- Capa de Servicios (Casos de Uso) ---
mkdir -p app/servicios
touch app/servicios/__init__.py
touch app/servicios/autenticacion_servicio.py
touch app/servicios/contacto_servicio.py
touch app/servicios/usuario_servicio.py
touch app/servicios/rol_servicio.py

# --- Esquemas (DTOs con Pydantic) ---
mkdir -p app/esquemas
touch app/esquemas/__init__.py
touch app/esquemas/contacto.py
touch app/esquemas/usuario.py
touch app/esquemas/rol.py
touch app/esquemas/token.py

# --- Punto de entrada de la App ---
touch app/main.py

# --- Estructura de Tests ---
mkdir -p tests/dominio
mkdir -p tests/infraestructura/persistencia/implementaciones_repositorios
mkdir -p tests/api/v2/endpoints
mkdir -p tests/core/seguridad
touch tests/__init__.py
touch tests/dominio/__init__.py
touch tests/infraestructura/__init__.py
touch tests/infraestructura/persistencia/__init__.py
touch tests/infraestructura/persistencia/implementaciones_repositorios/__init__.py
touch tests/api/__init__.py
touch tests/api/v2/__init__.py
touch tests/api/v2/endpoints/__init__.py
touch tests/core/__init__.py
touch tests/core/seguridad/__init__.py

echo "¡Estructura de directorios y archivos creada exitosamente!"
