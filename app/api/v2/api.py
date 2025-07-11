# app/api/v2/api.py
from fastapi import APIRouter

from app.api.v2.endpoints import auth # Importamos el nuevo router de autenticación

api_router = APIRouter()

# Registramos el router de autenticación con un prefijo y una etiqueta para agruparlo en la documentación
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])

# Aquí registrarás otros routers a medida que los vayas creando (ej. usuarios, roles, etc.)