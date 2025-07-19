"""
Tests unitarios para el servicio de autenticación.

Este módulo contiene pruebas para validar el funcionamiento del servicio
de autenticación, incluyendo la verificación de credenciales y la generación
de tokens JWT.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Importamos las clases necesarias para las pruebas
from app.servicios.autenticacion_servicio import AutenticacionServicio
from app.dominio.entidades.usuario import Usuario
from app.dominio.excepciones.dominio_excepciones import CredencialesInvalidasError
from app.dominio.interfaces.jwt_handler import IJWTHandler


@pytest.fixture
def usuario_servicio_mock():
    """Fixture que proporciona un mock del servicio de usuario."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def jwt_handler_mock():
    """Fixture que proporciona un mock del manejador JWT."""
    mock = MagicMock()
    mock.create_access_token.return_value = "mock_access_token"
    return mock


@pytest.fixture
def autenticacion_servicio(usuario_servicio_mock, jwt_handler_mock):
    """Fixture que proporciona una instancia del servicio de autenticación con dependencias mockeadas."""
    return AutenticacionServicio(usuario_servicio_mock, jwt_handler_mock)


@pytest.fixture
def usuario_mock():
    """Fixture que proporciona un mock de un usuario."""
    return Usuario(
        id=1,
        email="test@example.com",
        hashed_pwd="hashed_password",
        full_name="Test User",
        is_active=True
    )


class TestAutenticacionServicio:
    """Tests para el servicio de autenticación."""

    @pytest.mark.asyncio
    async def test_autenticar_usuario_y_crear_token_credenciales_validas(
        self, autenticacion_servicio, usuario_servicio_mock, jwt_handler_mock, usuario_mock
    ):
        """
        Test para verificar que se genera un token cuando las credenciales son válidas.
        """
        # Configurar el mock del servicio de usuario para devolver un usuario válido
        usuario_servicio_mock.verificar_credenciales.return_value = usuario_mock

        # Ejecutar el método a probar
        token = await autenticacion_servicio.autenticar_usuario_y_crear_token(
            "test@example.com", "password123"
        )

        # Verificar que se llamó al método verificar_credenciales con los parámetros correctos
        usuario_servicio_mock.verificar_credenciales.assert_called_once_with(
            "test@example.com", "password123"
        )

        # Verificar que se llamó al método create_access_token con los datos correctos
        jwt_handler_mock.create_access_token.assert_called_once_with(
            subject=1
        )

        # Verificar que se devolvió el token esperado
        assert token == "mock_access_token"

    @pytest.mark.asyncio
    async def test_autenticar_usuario_y_crear_token_credenciales_invalidas(
        self, autenticacion_servicio, usuario_servicio_mock
    ):
        """
        Test para verificar que se lanza una excepción cuando las credenciales son inválidas.
        """
        # Configurar el mock del servicio de usuario para lanzar una excepción
        usuario_servicio_mock.verificar_credenciales.side_effect = CredencialesInvalidasError(
            "Email o contraseña incorrectos"
        )

        # Verificar que se lanza la excepción esperada
        with pytest.raises(CredencialesInvalidasError) as excinfo:
            await autenticacion_servicio.autenticar_usuario_y_crear_token(
                "test@example.com", "wrong_password"
            )

        # Verificar el mensaje de la excepción
        assert "Email o contraseña incorrectos" in str(excinfo.value)

        # Verificar que se llamó al método verificar_credenciales con los parámetros correctos
        usuario_servicio_mock.verificar_credenciales.assert_called_once_with(
            "test@example.com", "wrong_password"
        )

    @pytest.mark.asyncio
    async def test_autenticar_usuario_y_crear_token_usuario_inactivo(
        self, autenticacion_servicio, usuario_servicio_mock
    ):
        """
        Test para verificar que se lanza una excepción cuando el usuario está inactivo.
        """
        # Configurar el mock del servicio de usuario para lanzar una excepción específica
        usuario_servicio_mock.verificar_credenciales.side_effect = CredencialesInvalidasError(
            "Usuario inactivo"
        )

        # Verificar que se lanza la excepción esperada
        with pytest.raises(CredencialesInvalidasError) as excinfo:
            await autenticacion_servicio.autenticar_usuario_y_crear_token(
                "inactive@example.com", "password123"
            )

        # Verificar el mensaje de la excepción
        assert "Usuario inactivo" in str(excinfo.value)

        # Verificar que se llamó al método verificar_credenciales con los parámetros correctos
        usuario_servicio_mock.verificar_credenciales.assert_called_once_with(
            "inactive@example.com", "password123"
        )
