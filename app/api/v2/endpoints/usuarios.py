"""Endpoints para gestión de usuarios (CRUD básico) y asignación de roles"""
from uuid import UUID
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status

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
    summary="Obtener usuario por ID",
)
async def obtener_usuario(
    user_id: UUID,
    _current_user: Usuario = Depends(get_current_user),
    usuario_servicio: UsuarioServicio = Depends(get_usuario_servicio),
):
    try:
        return await usuario_servicio.obtener_usuario_por_id(user_id)
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put(
    "/usuarios/{user_id}",
    response_model=UsuarioLeer,
    summary="Actualizar usuario",
)
async def actualizar_usuario(
    user_id: UUID,
    usuario_in: UsuarioActualizar,
    current_user: Usuario = Depends(get_current_user),
    usuario_servicio: UsuarioServicio = Depends(get_usuario_servicio),
):
    # TODO: Implementar verificación de permisos (solo admin o el mismo usuario)
    try:
        return await usuario_servicio.actualizar_usuario(
            user_id=user_id,
            email=usuario_in.email,
            full_name=usuario_in.full_name,
            is_active=usuario_in.is_active,
        )
    except (UsuarioNoEncontradoError, EmailYaRegistradoError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/usuarios/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar usuario",
)
async def eliminar_usuario(
    user_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    usuario_servicio: UsuarioServicio = Depends(get_usuario_servicio),
):
    # TODO: Implementar verificación de permisos (solo admin o el mismo usuario)
    try:
        await usuario_servicio.eliminar_usuario(user_id)
    except UsuarioNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --------------------------------------------------------------
# Asignación y remoción de roles a usuarios
# --------------------------------------------------------------
@router.post(
    "/usuarios/{user_id}/roles/{rol_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Asignar un rol a un usuario",
)
async def asignar_rol_a_usuario(
    user_id: UUID,
    rol_id: UUID,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    rol_servicio: Annotated[RolServicio, Depends(get_rol_servicio)],
):
    """Añade el rol indicado al usuario si no lo tiene ya."""
    try:
        await rol_servicio.asignar_rol_a_usuario(user_id=user_id, rol_id=rol_id)
    except (UsuarioNoEncontradoError, RolNoEncontradoError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/usuarios/{user_id}/roles/{rol_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover un rol de un usuario",
)
async def remover_rol_de_usuario(
    user_id: UUID,
    rol_id: UUID,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    rol_servicio: Annotated[RolServicio, Depends(get_rol_servicio)],
):
    """Quita el rol indicado del usuario si lo tiene."""
    try:
        await rol_servicio.remover_rol_de_usuario(user_id=user_id, rol_id=rol_id)
    except (UsuarioNoEncontradoError, RolNoEncontradoError) as e:
        raise HTTPException(status_code=404, detail=str(e))
