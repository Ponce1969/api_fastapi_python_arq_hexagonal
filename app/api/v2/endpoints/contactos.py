from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.core.deps import (
    get_contacto_servicio,
    get_current_user,
    ContactoServicio,
)
from app.dominio.entidades.usuario import Usuario
from app.esquemas.contacto import ContactoCreate, ContactoRead, ContactoUpdate
from app.dominio.excepciones.dominio_excepciones import ContactoNoEncontradoError

# Importación del rate limiter
from app.infraestructura.seguridad.rate_limiter import rate_limit, DEFAULT_RATE_LIMIT, SENSITIVE_RATE_LIMIT

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
@rate_limit(SENSITIVE_RATE_LIMIT)  # Limita a 50 solicitudes por minuto
async def crear_o_actualizar_mi_contacto(
    _request: Request,  # Necesario para el rate limiter (usado por el decorador)
    contacto_in: ContactoCreate,
    current_user: Usuario = Depends(get_current_user),
    contacto_servicio: ContactoServicio = Depends(get_contacto_servicio),
):
    """Crea o actualiza el perfil de contacto del usuario autenticado."""
    return await contacto_servicio.guardar_datos_contacto(
        user_id=current_user.id,
        name=contacto_in.name,
        email=contacto_in.email,
        phone=contacto_in.phone,
        message=contacto_in.message,
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


@router.patch(
    "/contactos/{contacto_id}/marcar",
    response_model=ContactoRead,
    summary="Marcar contacto como leído o no leído",
)
@rate_limit(DEFAULT_RATE_LIMIT)  # Limita a 100 solicitudes por minuto
async def marcar_contacto(
    _request: Request,  # Necesario para el rate limiter (usado por el decorador)
    contacto_id: UUID,
    contacto_update: ContactoUpdate,
    _current_user: Usuario = Depends(get_current_user),  # puede añadirse verificación de rol aquí
    contacto_servicio: ContactoServicio = Depends(get_contacto_servicio),
):
    """Marca un contacto como leído o no leído."""
    try:
        return await contacto_servicio.marcar_contacto_como_leido(
            contacto_id=contacto_id,
            leido=contacto_update.is_read
        )
    except ContactoNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
