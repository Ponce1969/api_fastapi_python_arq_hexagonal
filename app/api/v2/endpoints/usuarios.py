"""Endpoints para gestión de usuarios (CRUD básico) y asignación de roles"""
from uuid import UUID
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.core.deps import (
    get_current_user,
    get_usuario_servicio,
    get_rol_servicio,
    UsuarioServicio,
    RolServicio,
    DBSession
)
from app.dominio.entidades.usuario import Usuario
from app.dominio.excepciones.dominio_excepciones import UsuarioNoEncontradoError, EmailYaRegistradoError
from app.esquemas.usuario import UsuarioLeer, UsuarioActualizar

# Importación del rate limiter
from app.infraestructura.seguridad.rate_limiter import rate_limit, DEFAULT_RATE_LIMIT, SENSITIVE_RATE_LIMIT

router = APIRouter()



@router.get(
    "/usuarios",
    response_model=List[UsuarioLeer],
    summary="Listar usuarios",
)
async def listar_usuarios(
    skip: int = 0,
    limit: int = 100,
    _current_user: Usuario = Depends(get_current_user),
    usuario_servicio: UsuarioServicio = Depends(get_usuario_servicio),
):
    return await usuario_servicio.obtener_todos_los_usuarios(skip=skip, limit=limit)


@router.get(
    "/usuarios/{user_id}",
    response_model=UsuarioLeer,
    responses={
        404: {"description": "Usuario no encontrado"}
    },
    summary="Obtener usuario por ID",
)
async def obtener_usuario(
    user_id: UUID,
    _current_user: Usuario = Depends(get_current_user),
    usuario_servicio: UsuarioServicio = Depends(get_usuario_servicio),
):
    """Obtiene un usuario por su ID.
    
    Utiliza el manejador global de excepciones para gestionar UsuarioNoEncontradoError.
    """
    return await usuario_servicio.obtener_usuario_por_id(user_id)


@router.put(
    "/usuarios/{user_id}",
    response_model=UsuarioLeer,
    responses={
        404: {"description": "Usuario no encontrado"},
        409: {"description": "Email ya registrado para otro usuario"}
    },
    summary="Actualizar datos de usuario",
)
@rate_limit(SENSITIVE_RATE_LIMIT)  # Limita a 50 solicitudes por minuto
async def actualizar_usuario(
    _request: Request,  # Necesario para el rate limiter (usado por el decorador)
    user_id: UUID,
    usuario_in: UsuarioActualizar,
    current_user: Usuario = Depends(get_current_user),
    usuario_servicio: UsuarioServicio = Depends(get_usuario_servicio),
):
    """Actualiza los datos de un usuario existente.
    
    Utiliza el manejador global de excepciones para gestionar:
    - UsuarioNoEncontradoError (404)
    - EmailYaRegistradoError (409)
    
    TODO: Implementar verificación de permisos (solo admin o el mismo usuario)
    """
    return await usuario_servicio.actualizar_usuario(
        user_id=user_id,
        email=usuario_in.email,
        full_name=usuario_in.full_name,
        is_active=usuario_in.is_active,
    )


@router.delete(
    "/usuarios/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Usuario no encontrado"}
    },
    summary="Eliminar usuario",
)
@rate_limit(SENSITIVE_RATE_LIMIT)  # Limita a 50 solicitudes por minuto
async def eliminar_usuario(
    _request: Request,  # Necesario para el rate limiter (usado por el decorador)
    user_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    usuario_servicio: UsuarioServicio = Depends(get_usuario_servicio),
):
    """Elimina un usuario por su ID.
    
    Utiliza el manejador global de excepciones para gestionar UsuarioNoEncontradoError (404).
    
    TODO: Implementar verificación de permisos (solo admin o el mismo usuario)
    """
    await usuario_servicio.eliminar_usuario(user_id)


# --------------------------------------------------------------
# Asignación y remoción de roles a usuarios
# --------------------------------------------------------------
@router.post(
    "/usuarios/{user_id}/roles/{rol_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Usuario o rol no encontrado"}
    },
    summary="Asignar un rol a un usuario",
)
@rate_limit(SENSITIVE_RATE_LIMIT)  # Limita a 50 solicitudes por minuto
async def asignar_rol_a_usuario(
    _request: Request,  # Necesario para el rate limiter (usado por el decorador)
    user_id: UUID,
    rol_id: UUID,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    rol_servicio: Annotated[RolServicio, Depends(get_rol_servicio)],
):
    """Añade el rol indicado al usuario si no lo tiene ya.
    
    Utiliza el manejador global de excepciones para gestionar:
    - UsuarioNoEncontradoError (404)
    - RolNoEncontradoError (404)
    """
    await rol_servicio.asignar_rol_a_usuario(user_id=user_id, rol_id=rol_id)


@router.delete(
    "/usuarios/{user_id}/roles/{rol_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Usuario o rol no encontrado"}
    },
    summary="Remover un rol de un usuario",
)
@rate_limit(SENSITIVE_RATE_LIMIT)  # Limita a 50 solicitudes por minuto
async def remover_rol_de_usuario(
    _request: Request,  # Necesario para el rate limiter (usado por el decorador)
    user_id: UUID,
    rol_id: UUID,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    rol_servicio: Annotated[RolServicio, Depends(get_rol_servicio)],
):
    """Quita el rol indicado del usuario si lo tiene.
    
    Utiliza el manejador global de excepciones para gestionar:
    - UsuarioNoEncontradoError (404)
    - RolNoEncontradoError (404)
    """
    await rol_servicio.remover_rol_de_usuario(user_id=user_id, rol_id=rol_id)
