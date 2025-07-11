# app/servicios/autenticacion_servicio.py
from app.servicios.usuario_servicio import UsuarioServicio
from app.core.seguridad.jwt import JWTHandler
from app.dominio.excepciones.dominio_excepciones import CredencialesInvalidasError


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

    async def autenticar_usuario_y_crear_token(self, email: str, password: str) -> str:
        """
        Verifica las credenciales y, si son válidas, genera un token de acceso.

        Args:
            email (str): El correo electrónico del usuario.
            password (str): La contraseña del usuario.

        Returns:
            str: El token de acceso JWT.

        Raises:
            CredencialesInvalidasError: Si el email o la contraseña son incorrectos.
        """
        usuario = await self.usuario_servicio.verificar_credenciales(email, password)
        access_token = self.jwt_handler.create_access_token(data={"sub": str(usuario.id)})
        return access_token