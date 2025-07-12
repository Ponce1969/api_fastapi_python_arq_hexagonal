from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import (
    get_current_user,
    get_rol_servicio,
    RolServicio,
)
from app.dominio.entidades.usuario import Usuario
from app.dominio.excepciones.dominio_excepciones import (
    RolNoEncontradoError,
    RolYaExisteError,
)
from app.esquemas.rol import RolCreate, RolRead, RolUpdate

router = APIRouter()


@router.post(
    "/roles",
    response_model=RolRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo rol",
)
async def crear_rol(
    rol_in: RolCreate,
    _current_user: Usuario = Depends(get_current_user),  # agregar verificación de permiso si corresponde
    rol_servicio: RolServicio = Depends(get_rol_servicio),
):
    try:
        return await rol_servicio.crear_rol(name=rol_in.name, description=rol_in.description)
    except RolYaExisteError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/roles", response_model=List[RolRead], summary="Listar roles")
async def listar_roles(
    skip: int = 0,
    limit: int = 100,
    _current_user: Usuario = Depends(get_current_user),
    rol_servicio: RolServicio = Depends(get_rol_servicio),
):
    return await rol_servicio.obtener_todos_los_roles(skip=skip, limit=limit)


@router.get("/roles/{rol_id}", response_model=RolRead, summary="Obtener rol por ID")
async def obtener_rol(
    rol_id: UUID,
    _current_user: Usuario = Depends(get_current_user),
    rol_servicio: RolServicio = Depends(get_rol_servicio),
):
    try:
        return await rol_servicio.obtener_rol_por_id(rol_id)
    except RolNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/roles/{rol_id}", response_model=RolRead, summary="Actualizar rol")
async def actualizar_rol(
    rol_id: UUID,
    rol_in: RolUpdate,
    _current_user: Usuario = Depends(get_current_user),
    rol_servicio: RolServicio = Depends(get_rol_servicio),
):
    try:
        return await rol_servicio.actualizar_rol(
            rol_id=rol_id, name=rol_in.name, description=rol_in.description
        )
    except (RolNoEncontradoError, RolYaExisteError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/roles/{rol_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar rol"
)
async def eliminar_rol(
    rol_id: UUID,
    _current_user: Usuario = Depends(get_current_user),
    rol_servicio: RolServicio = Depends(get_rol_servicio),
):
    try:
        await rol_servicio.eliminar_rol(rol_id)
    except RolNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
