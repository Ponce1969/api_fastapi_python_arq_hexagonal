# Rate Limiting con Redis en FastAPI

## 📚 Introducción

El rate limiting es un patrón de diseño crucial para proteger APIs contra abusos, ataques de denegación de servicio (DoS) y uso excesivo de recursos. En nuestra API de FastAPI, implementamos rate limiting utilizando Redis como almacén de datos en memoria para un rendimiento óptimo y una gestión eficiente de los límites de solicitudes.

## 🔧 Implementación

Nuestra implementación utiliza la biblioteca `fastapi-limiter` junto con Redis para proporcionar un sistema robusto de rate limiting basado en direcciones IP, tokens de autenticación u otros identificadores.

### Componentes Principales

1. **Redis**: Base de datos en memoria que almacena los contadores de solicitudes y sus tiempos de expiración.
2. **fastapi-limiter**: Biblioteca que proporciona decoradores para limitar las solicitudes a endpoints específicos.
3. **Middleware de FastAPI**: Configura el rate limiting a nivel de aplicación o de router.

### Configuración

El rate limiting se configura en el archivo `main.py` durante la inicialización de la aplicación:

```python
from fastapi import FastAPI, Depends
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
from app.core.config import settings

app = FastAPI()

@app.on_event("startup")
async def startup():
    # Inicializar el limitador con la conexión a Redis
    redis_connection = await redis.from_url(settings.REDIS_URL)
    await FastAPILimiter.init(redis_connection)
```

### Aplicación a Endpoints

El rate limiting se puede aplicar a endpoints individuales utilizando el decorador `@limiter.limit()`:

```python
from fastapi import APIRouter, Depends
from fastapi_limiter.depends import RateLimiter

router = APIRouter()

@router.post("/login")
@limiter.limit("5/minute")  # Limita a 5 solicitudes por minuto por IP
async def login(user_credentials: UserCredentials):
    # Lógica de inicio de sesión
    pass
```

## 🐳 Configuración en Entornos Docker

Para el correcto funcionamiento del rate limiting con Redis en entornos Docker, se deben tener en cuenta las siguientes consideraciones:

### 1. Configuración de Puertos

En `docker-compose.yml`, mapeamos el puerto de Redis del contenedor (6379) al puerto 6380 del host para evitar conflictos con posibles instancias de Redis locales:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
```

### 2. URL de Conexión

En entornos Docker, la variable `REDIS_URL` en el archivo `.env` debe usar el nombre del servicio como host en lugar de localhost:

```
# Configuración correcta para Docker
REDIS_URL=redis://redis:6379/0

# Configuración incorrecta para Docker (pero correcta para desarrollo local)
# REDIS_URL=redis://localhost:6380/0
```

### 3. Dependencias

Es fundamental asegurar que `fastapi-limiter` y `redis` estén incluidos en el archivo `requirements.lock` para que se instalen correctamente en el contenedor Docker:

```
fastapi-limiter==0.1.6
redis==6.2.0
```

### 4. Warning de Memoria en Producción

En entornos de producción, Redis puede mostrar un warning: "Memory overcommit must be enabled". Para solucionarlo:

**Opción 1**: Añadir la siguiente línea a `/etc/sysctl.conf` en el host:
```
vm.overcommit_memory = 1
```

**Opción 2**: Ejecutar el siguiente comando en el host:
```bash
sudo sysctl vm.overcommit_memory=1
```

**Nota**: La configuración `sysctls` en Docker Compose no es compatible en todos los entornos.

## 🛡️ Mejores Prácticas

1. **Límites Graduales**: Implementar diferentes límites según el tipo de endpoint y su criticidad.
2. **Respuestas Informativas**: Incluir en las respuestas HTTP cabeceras que indiquen los límites y el estado actual.
3. **Monitoreo**: Supervisar los patrones de uso para ajustar los límites según sea necesario.
4. **Whitelist**: Permitir excepciones para ciertos clientes o IPs de confianza.

## 📊 Ejemplo de Cabeceras de Respuesta

Cuando se aplica rate limiting, las respuestas HTTP incluyen cabeceras informativas:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1625097600
```

## 🔍 Resolución de Problemas

Si experimentas problemas con el rate limiting:

1. Verifica que Redis esté funcionando correctamente: `docker-compose exec redis redis-cli ping`
2. Asegúrate de que la URL de conexión sea correcta según el entorno (desarrollo local vs. Docker)
3. Revisa los logs de la aplicación para mensajes relacionados con la conexión a Redis
4. Confirma que las dependencias `fastapi-limiter` y `redis` estén instaladas en el contenedor

## 📚 Referencias

- [Documentación de fastapi-limiter](https://github.com/long2ice/fastapi-limiter)
- [Documentación de Redis](https://redis.io/documentation)
- [Mejores prácticas de rate limiting](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
