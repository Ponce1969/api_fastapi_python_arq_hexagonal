# app/api/v2/endpoints/auth.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm # <-- ¡NUEVA IMPORTACIÓN!

# Importaciones de servicios y esquemas
from app.servicios.usuario_servicio import UsuarioServicio # Aunque no se usa directamente en login, se mantiene por register
from app.servicios.autenticacion_servicio import AutenticacionServicio # <-- ¡NUEVA IMPORTACIÓN!
from app.esquemas.usuario import UsuarioCrear, UsuarioLeer # Esquemas existentes para registro
from app.esquemas.token import Token # <-- ¡NUEVA IMPORTACIÓN! (Para la respuesta del token)
from app.dominio.entidades.usuario import Usuario

# Importaciones de dependencias y excepciones
from app.core.deps import get_usuario_servicio, get_autenticacion_servicio, get_current_user # <-- ¡ACTUALIZADA LA IMPORTACIÓN!
from app.dominio.excepciones.dominio_excepciones import EmailYaRegistradoError, CredencialesInvalidasError

# Importación del rate limiter
from app.infraestructura.seguridad.rate_limiter import rate_limit, AUTH_RATE_LIMIT

router = APIRouter()


@router.post(
    "/register",
    response_model=UsuarioLeer,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
    description="Crea una nueva cuenta de usuario en el sistema.",
)
@rate_limit(AUTH_RATE_LIMIT)  # Limita a 20 solicitudes por minuto (definido en rate_limiter.py)
async def register_user(
    _request: Request,  # Necesario para el rate limiter (usado por el decorador)
    usuario_in: UsuarioCrear,
    usuario_servicio: Annotated[UsuarioServicio, Depends(get_usuario_servicio)],
):
    """
    Endpoint para registrar un nuevo usuario.
    """
    try:
        usuario_creado = await usuario_servicio.crear_usuario(
            email=usuario_in.email, password=usuario_in.password, full_name=usuario_in.full_name
        )
        return usuario_creado
    except EmailYaRegistradoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/login",
    response_model=Token, # <-- El login devuelve un Token (access_token y token_type)
    summary="Iniciar sesión de usuario",
    description="Autentica a un usuario y devuelve un token de acceso JWT.",
    # Usa OAuth2PasswordRequestForm para un login estándar compatible con OpenAPI/Swagger UI
)
@rate_limit(AUTH_RATE_LIMIT)  # Limita a 20 solicitudes por minuto (definido en rate_limiter.py)
async def login_for_access_token(
    _request: Request,  # Necesario para el rate limiter (usado por el decorador)
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], # <-- FastAPI maneja la forma del formulario
    auth_servicio: Annotated[AutenticacionServicio, Depends(get_autenticacion_servicio)], # <-- Inyecta el servicio de autenticación
):
    """
    Endpoint para iniciar sesión.
    Recibe el nombre de usuario (email) y la contraseña como datos de formulario.
    """
    try:
        # Llama al servicio de autenticación para verificar las credenciales y obtener el token.
        access_token = await auth_servicio.autenticar_usuario_y_crear_token(
            email=form_data.username, # OAuth2PasswordRequestForm usa 'username' para el identificador
            password=form_data.password
        )
        # Devuelve el token en el formato esperado por el esquema Token
        return {"access_token": access_token, "token_type": "bearer"}
    except CredencialesInvalidasError as e:
        # Si las credenciales son inválidas, lanza una excepción HTTP 401 Unauthorized
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}, # Indica al cliente cómo autenticarse
        )


@router.get(
    "/me",
    response_model=UsuarioLeer,
    summary="Obtener datos del usuario actual",
    description="Devuelve la información del usuario que está actualmente autenticado. Requiere autenticación.",
)
async def read_users_me(current_user: Annotated[Usuario, Depends(get_current_user)]):
    """
    Endpoint protegido que devuelve los datos del usuario autenticado.
    La dependencia `get_current_user` se encarga de toda la validación del token.
    """
    return current_user