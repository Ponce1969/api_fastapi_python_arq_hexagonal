# app/api/v2/api.py
from fastapi import APIRouter

from app.api.v2.endpoints import auth, contactos, roles, usuarios  # Importamos routers

api_router = APIRouter()

# Registramos el router de autenticación con un prefijo y una etiqueta para agruparlo en la documentación
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(contactos.router, tags=["Contactos"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(usuarios.router, tags=["Usuarios"])

# Otros routers se registrarán aquí a medida que se implementen (usuarios, roles, etc.)