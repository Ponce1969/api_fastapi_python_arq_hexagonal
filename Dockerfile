# usar Python 3.12 como imagen base
FROM python:3.12-slim

# Establecer directorio de trabajo
WORKDIR /app

# Evitar que Python genere archivos .pyc
ENV PYTHONPYTHONDONTWRITEBYTECODE=1
# Asegurar que la salida de Python se envia directamente a la terminal
ENV PYTHONUNBUFFERED=1

# Instalar UV para gestion de dependencias
# Se instala globalmente en el contenedor para que 'uv' esté disponible
RUN pip install --no-cache-dir uv

# Copiar el archivo de dependencias congeladas (generado localmente con 'uv pip freeze > requirements.lock')
# Este archivo debe existir en la raíz de tu proyecto
COPY requirements.lock .

# Instalar dependencias con UV (usando --system para instalar globalmente en el entorno del contenedor)
# --no-cache-dir para reducir el tamaño de la imagen final del contenedor
RUN uv pip install --system --no-cache-dir -r requirements.lock

# Copiar el resto del codigo de la aplicacion
# Esto debe hacerse DESPUES de instalar las dependencias para aprovechar el cache de Docker.
# Si cambias el código, Docker solo reconstruirá desde este paso.
COPY . .

# Exponer el puerto que usa la aplicacion
EXPOSE 8000

# Comando para ejecutar la aplicacion
# Asegúrate de que 'app.main:app' es la ruta correcta a tu instancia de FastAPI
# (es decir, el objeto 'app' en el archivo 'main.py' dentro de la carpeta 'app')
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

