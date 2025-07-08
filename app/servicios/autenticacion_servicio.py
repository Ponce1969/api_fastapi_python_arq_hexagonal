# app/servicios/autenticacion_servicio.py
from app.servicios.usuario_servicio import UsuarioServicio
from app.core.seguridad.jwt import JWTHandler


class AutenticacionServicio:
    """
    Servicio de aplicación para la autenticación de usuarios.
    Orquesta la verificación de credenciales y la generación de tokens.
    """

    def __init__(self, usuario_servicio: UsuarioServicio, jwt_handler: JWTHandler):
        """
        Inicializa el servicio de autenticación.
        Depende del servicio de usuarios para validar credenciales y de un
        manejador de JWT para crear los tokens.
        """
        self.usuario_servicio = usuario_servicio
        self.jwt_handler = jwt_handler

    async def iniciar_sesion(self, email: str, password: str) -> dict:
        """
        Verifica las credenciales y, si son válidas, genera un token de acceso.
        """
        usuario = await self.usuario_servicio.verificar_credenciales(email, password)
        access_token = self.jwt_handler.create_access_token(data={"sub": str(usuario.id)})
        return {"access_token": access_token, "token_type": "bearer"}