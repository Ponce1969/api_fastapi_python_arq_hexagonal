# API de FastAPI v2

## 📚 Documentación

Bienvenido a la documentación de la API de FastAPI v2. Este proyecto implementa una API RESTful siguiendo los principios de Arquitectura Limpia y Domain-Driven Design.

### Índice de Documentación

#### 📐 Arquitectura y Diseño
- [Visión General del Proyecto](/docs/arquitectura/proyecto_overview.md) - Descripción detallada de la arquitectura, tecnologías y estructura del proyecto.
- [Patrón Unit of Work](/docs/patrones/unit_of_work.md) - Documentación completa sobre la implementación del patrón Unit of Work y el sistema de mapeo de excepciones.
- [Rate Limiting con Redis](/docs/patrones/rate_limiting.md) - Documentación sobre la implementación de rate limiting usando Redis y fastapi-limiter.

#### 📋 Guías y Tutoriales
- [Guía de Implementación](/docs/guias/implementacion.md) - Lista de verificación paso a paso para el desarrollo de nuevas funcionalidades.

## 🚀 Inicio Rápido

### Requisitos Previos
- Python 3.12+
- PostgreSQL
- Redis (para rate limiting)
- Docker y Docker Compose (opcional)

### Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd app_v2
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

4. Ejecutar migraciones:
```bash
alembic upgrade head
```

5. Iniciar el servidor:
```bash
uvicorn app.main:app --reload
```

6. Acceder a la documentación de la API:
```
http://localhost:8000/api/docs
```

## 🛠️ Desarrollo

Para contribuir al proyecto, por favor sigue la [Guía de Implementación](/docs/guias/implementacion.md) que detalla el proceso paso a paso para añadir nuevas funcionalidades manteniendo la integridad de la arquitectura.

### 🔍 Verificación de Tipos con Mypy

Este proyecto utiliza Mypy para verificación estática de tipos, garantizando la estabilidad de la API para el equipo frontend:

```bash
# Verificar tipos en todo el proyecto
mypy app/ --config-file mypy.ini

# Verificar solo esquemas (más rápido durante desarrollo)
mypy app/esquemas/ --config-file mypy.ini
```

### 🔄 CI/CD Pipeline

Cada push ejecuta automáticamente:
- ✅ Verificación de tipos con Mypy
- ✅ 117 tests de la suite completa
- ✅ Validación de migraciones de base de datos
- 📄 Generación automática de documentación OpenAPI
- 🦕 Generación de tipos TypeScript para Deno Fresh
- 🔗 Validación de contratos API-Frontend

Esto garantiza que el equipo frontend (Deno Fresh) siempre reciba una API estable con tipos TypeScript actualizados automáticamente.

### 🦕 Integración con Deno Fresh

Este backend está optimizado para trabajar con el frontend Deno Fresh:

```bash
# Generar tipos TypeScript desde OpenAPI
python -c "from app.main import app; import json; json.dump(app.openapi(), open('openapi.json', 'w'), indent=2)"
deno run --allow-read --allow-write https://deno.land/x/openapi_fetch/scripts/openapi-typescript.ts openapi.json --output api-types.ts
```

**Beneficios de la integración:**
- 🎯 **Tipos automáticos**: Los esquemas Pydantic se convierten automáticamente en tipos TypeScript
- 🔒 **Contratos garantizados**: Mypy + TypeScript = validación en ambos extremos
- 📚 **Documentación sincronizada**: OpenAPI mantiene frontend y backend alineados
- 🚀 **Desarrollo ágil**: Cambios en el backend se reflejan automáticamente en tipos del frontend

## 📝 Licencia

Este proyecto está licenciado bajo [Licencia] - ver el archivo LICENSE para más detalles.
