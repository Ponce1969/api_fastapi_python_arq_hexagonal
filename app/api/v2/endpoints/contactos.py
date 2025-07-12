from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import (
    get_contacto_servicio,
    get_current_user,
    ContactoServicio,
)
from app.dominio.entidades.usuario import Usuario
from app.esquemas.contacto import ContactoCreate, ContactoRead
from app.dominio.excepciones.dominio_excepciones import ContactoNoEncontradoError

router = APIRouter()


# ---------------------------------------------------------
# Operaciones de contacto para el usuario autenticado
# ---------------------------------------------------------

@router.get("/me/contacto", response_model=ContactoRead, summary="Obtener mi perfil de contacto")
async def obtener_mi_contacto(
    current_user: Usuario = Depends(get_current_user),
    contacto_servicio: ContactoServicio = Depends(get_contacto_servicio),
):
    """Devuelve el perfil de contacto asociado al usuario autenticado."""
    try:
        return await contacto_servicio.obtener_contacto_por_usuario_id(current_user.id)
    except ContactoNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/me/contacto",
    response_model=ContactoRead,
    summary="Crear o actualizar mi perfil de contacto",
    status_code=status.HTTP_201_CREATED,
)
async def crear_o_actualizar_mi_contacto(
    contacto_in: ContactoCreate,
    current_user: Usuario = Depends(get_current_user),
    contacto_servicio: ContactoServicio = Depends(get_contacto_servicio),
):
    """Crea o actualiza el perfil de contacto del usuario autenticado."""
    return await contacto_servicio.guardar_datos_contacto(
        user_id=current_user.id,
        phone=contacto_in.phone,
        address=contacto_in.address,
        city=contacto_in.city,
        country=contacto_in.country,
        zip_code=contacto_in.zip_code,
    )


# ---------------------------------------------------------
# Endpoints administrativos / para otros usuarios
# ---------------------------------------------------------

@router.get(
    "/contactos/{contacto_id}",
    response_model=ContactoRead,
    summary="Obtener contacto por ID",
)
async def obtener_contacto_por_id(
    contacto_id: UUID,
    _current_user: Usuario = Depends(get_current_user),  # puede añadirse verificación de rol aquí
    contacto_servicio: ContactoServicio = Depends(get_contacto_servicio),
):
    """Devuelve un contacto por su UUID."""
    try:
        return await contacto_servicio.obtener_contacto_por_id(contacto_id)
    except ContactoNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
