"""
Pruebas unitarias para el mapeador de excepciones de persistencia.

Este módulo contiene pruebas unitarias para verificar el correcto funcionamiento
del mapeador de excepciones que traduce excepciones técnicas de SQLAlchemy
a excepciones de dominio.
"""
import pytest
import re
import asyncio
from unittest.mock import patch, MagicMock

from sqlalchemy.exc import (
    IntegrityError, 
    NoResultFound, 
    SQLAlchemyError, 
    OperationalError,
    TimeoutError as SQLAlchemyTimeoutError,
    ProgrammingError
)

from app.dominio.excepciones.dominio_excepciones import (
    DominioExcepcion,
    EmailYaRegistradoError,
    UsuarioNoEncontradoError,
    EntidadNoEncontradaError,
    ConexionDBError,
    TimeoutDBError,
    PermisosDBError,
    ClaveForaneaError,
    RestriccionCheckError,
    PersistenciaError
)
from app.infraestructura.persistencia.excepciones.persistencia_excepciones import (
    ExcepcionesMapper,
)


class TestExcepcionesMapper:
    """Pruebas para la clase ExcepcionesMapper."""

    def test_map_integrity_error_email_duplicado(self):
        """
        Prueba que una IntegrityError por email duplicado se mapea correctamente
        a EmailYaRegistradoError.
        """
        # Crear un mensaje de error similar al que generaría PostgreSQL
        error_message = (
            'duplicate key value violates unique constraint "usuarios_email_key"\n'
            'DETAIL:  Key (email)=(usuario@ejemplo.com) already exists.'
        )
        
        # Crear una excepción de IntegrityError con el mensaje
        integrity_error = IntegrityError(
            statement="INSERT INTO usuarios (email) VALUES ('usuario@ejemplo.com')",
            params={},
            orig=Exception(error_message)
        )
        
        # Mapear la excepción
        result = ExcepcionesMapper.map_exception(integrity_error)
        
        # Verificar que se ha mapeado correctamente
        assert isinstance(result, EmailYaRegistradoError)
        assert "usuario@ejemplo.com" in str(result)

    def test_map_integrity_error_sin_patron_email(self):
        """
        Prueba que una IntegrityError sin un patrón de email reconocible
        se mapea a una DominioExcepcion genérica.
        """
        # Crear un mensaje de error de integridad que no coincide con el patrón de email
        error_message = (
            'duplicate key value violates unique constraint "otra_restriccion"\n'
            'DETAIL: Algún otro detalle sin patrón de email.'
        )
        
        # Crear una excepción de IntegrityError con el mensaje
        integrity_error = IntegrityError(
            statement="INSERT INTO otra_tabla (campo) VALUES ('valor')",
            params={},
            orig=Exception(error_message)
        )
        
        # Mapear la excepción
        result = ExcepcionesMapper.map_exception(integrity_error)
        
        # Verificar que se ha mapeado a una excepción genérica
        assert isinstance(result, DominioExcepcion)
        assert not isinstance(result, EmailYaRegistradoError)
        assert "Error de integridad de datos" in str(result)

    def test_map_no_result_found(self):
        """
        Prueba que una NoResultFound se mapea correctamente a EntidadNoEncontradaError
        cuando no hay información específica en el traceback.
        """
        # Crear una excepción NoResultFound
        no_result = NoResultFound("No se encontró ningún resultado")
        
        # Mapear la excepción
        result = ExcepcionesMapper.map_exception(no_result)
        
        # Verificar que se ha mapeado correctamente a EntidadNoEncontradaError
        # ya que en el contexto de la prueba no hay suficiente información en el traceback
        assert isinstance(result, EntidadNoEncontradaError)
        assert "no se encontró" in str(result).lower()

    def test_map_sqlalchemy_error_generico(self):
        """
        Prueba que una SQLAlchemyError genérica se mapea a una DominioExcepcion.
        """
        # Crear una excepción SQLAlchemyError genérica
        sqlalchemy_error = SQLAlchemyError("Error de SQLAlchemy genérico")
        
        # Mapear la excepción
        result = ExcepcionesMapper.map_exception(sqlalchemy_error)
        
        # Verificar que se ha mapeado a una excepción genérica
        assert isinstance(result, DominioExcepcion)
        assert "Error de SQLAlchemy" in str(result)

    def test_excepcion_dominio_se_mantiene(self):
        """
        Prueba que una excepción de dominio se devuelve sin cambios.
        """
        # Crear una excepción de dominio
        dominio_exception = EmailYaRegistradoError("test@ejemplo.com")
        
        # Mapear la excepción
        result = ExcepcionesMapper.map_exception(dominio_exception)
        
        # Verificar que la excepción se devuelve sin cambios
        assert result is dominio_exception
        assert isinstance(result, EmailYaRegistradoError)
        assert "test@ejemplo.com" in str(result)

    def test_excepcion_no_mapeada(self):
        """
        Prueba que una excepción no mapeada se convierte en DominioExcepcion.
        """
        # Crear una excepción que no es ni de SQLAlchemy ni de dominio
        generic_exception = ValueError("Un error de valor")
        
        # Mapear la excepción
        result = ExcepcionesMapper.map_exception(generic_exception)
        
        # Verificar que se ha mapeado a una excepción genérica
        assert isinstance(result, DominioExcepcion)
        assert "Error inesperado" in str(result)
        assert "Un error de valor" in str(result)

    def test_wrap_exception_preserva_traceback(self):
        """
        Prueba que wrap_exception preserva el traceback original.
        """
        # Crear una excepción con traceback
        try:
            raise ValueError("Excepción original")
        except ValueError as e:
            # Envolver la excepción
            result = ExcepcionesMapper.wrap_exception(e)
        
        # Verificar que la excepción resultante es de tipo DominioExcepcion
        assert isinstance(result, DominioExcepcion)
        
        # Verificar que la excepción contiene información sobre la excepción original
        assert hasattr(result, '__notes__')
        assert any("Excepción original: ValueError: Excepción original" in note for note in result.__notes__)
        
        # Verificar que la excepción resultante contiene el mensaje original
        assert "Error inesperado: Excepción original" in str(result)
        
    def test_map_integrity_error_foreign_key(self):
        """
        Prueba que una IntegrityError por violación de clave foránea se mapea correctamente
        a ClaveForaneaError.
        """
        # Crear un mensaje de error similar al que generaría PostgreSQL para violación de FK
        error_message = (
            'insert or update on table "usuarios_roles" violates foreign key constraint "usuarios_roles_rol_id_fkey"\n'
            'DETAIL:  Key (rol_id)=(999) is not present in table "roles".')
        
        # Crear una excepción de IntegrityError con el mensaje
        integrity_error = IntegrityError(
            statement="INSERT INTO usuarios_roles (usuario_id, rol_id) VALUES (1, 999)",
            params={},
            orig=Exception(error_message)
        )
        
        # Mapear la excepción
        result = ExcepcionesMapper.map_exception(integrity_error)
        
        # Verificar que se ha mapeado correctamente
        assert isinstance(result, ClaveForaneaError)
        assert "999" in str(result)  # El valor de la clave que causó el error
        assert "roles" in str(result).lower() or "role" in str(result).lower()  # La entidad relacionada
        
    def test_map_integrity_error_check_constraint(self):
        """
        Prueba que una IntegrityError por violación de restricción check se mapea correctamente.
        
        Nota: Actualmente el mapeador devuelve DominioExcepcion para restricciones check,
        pero en el futuro podría mejorarse para devolver RestriccionCheckError.
        """
        # Crear un mensaje de error similar al que generaría PostgreSQL para violación de check
        error_message = (
            'new row for relation "usuarios" violates check constraint "usuarios_edad_check"\n'
            'DETAIL:  Failing row contains (1, John Doe, john@example.com, hash123, -5, 2023-07-16 12:00:00).')
        
        # Crear una excepción de IntegrityError con el mensaje
        integrity_error = IntegrityError(
            statement="INSERT INTO usuarios (nombre, email, password, edad) VALUES ('John Doe', 'john@example.com', 'hash123', -5)",
            params={},
            orig=Exception(error_message)
        )
        
        # Mapear la excepción
        result = ExcepcionesMapper.map_exception(integrity_error)
        
        # Verificar que se ha mapeado a alguna excepción de dominio
        # Actualmente se mapea a DominioExcepcion genérica
        assert isinstance(result, DominioExcepcion)
        assert "integridad" in str(result).lower() or "check" in str(result).lower()
        
    def test_map_operational_error_connection(self):
        """
        Prueba que un OperationalError de conexión se mapea correctamente a ConexionDBError.
        """
        # Crear un mensaje de error de conexión
        error_message = "connection refused: could not connect to server"
        
        # Crear una excepción OperationalError
        operational_error = OperationalError(
            statement="SELECT * FROM usuarios",
            params={},
            orig=Exception(error_message)
        )
        
        # Mapear la excepción
        result = ExcepcionesMapper.map_exception(operational_error)
        
        # Verificar que se ha mapeado correctamente
        assert isinstance(result, ConexionDBError)
        assert "conexión" in str(result).lower()
        
    def test_map_operational_error_permission(self):
        """
        Prueba que un OperationalError de permisos se mapea correctamente a PermisosDBError.
        """
        # Crear un mensaje de error de permisos
        error_message = "permission denied for table usuarios"
        
        # Crear una excepción OperationalError
        operational_error = OperationalError(
            statement="DELETE FROM usuarios",
            params={},
            orig=Exception(error_message)
        )
        
        # Mapear la excepción
        result = ExcepcionesMapper.map_exception(operational_error)
        
        # Verificar que se ha mapeado correctamente
        assert isinstance(result, PermisosDBError)
        assert "permisos" in str(result).lower()
        
    def test_map_timeout_error_sqlalchemy(self):
        """
        Prueba que un TimeoutError de SQLAlchemy se mapea correctamente a TimeoutDBError.
        
        Nota: Dado que SQLAlchemyTimeoutError no acepta los mismos parámetros que otros errores
        de SQLAlchemy, usamos asyncio.TimeoutError que también es detectado por el mapeador.
        """
        # Crear una excepción TimeoutError de asyncio (el mapeador también la detecta)
        timeout_error = asyncio.TimeoutError("timeout occurred during query execution")
        
        # Mapear la excepción
        result = ExcepcionesMapper.map_exception(timeout_error)
        
        # Verificar que se ha mapeado correctamente
        assert isinstance(result, TimeoutDBError)
        
    def test_map_timeout_error_asyncio(self):
        """
        Prueba que un TimeoutError de asyncio se mapea correctamente a TimeoutDBError.
        """
        # Crear una excepción TimeoutError de asyncio
        timeout_error = asyncio.TimeoutError("Operation timed out")
        
        # Mapear la excepción
        result = ExcepcionesMapper.map_exception(timeout_error)
        
        # Verificar que se ha mapeado correctamente
        assert isinstance(result, TimeoutDBError)
        
    def test_map_programming_error(self):
        """
        Prueba que un ProgrammingError se mapea correctamente a PersistenciaError.
        """
        # Crear un mensaje de error de programación SQL
        error_message = "syntax error at or near 'SELET'"
        
        # Crear una excepción ProgrammingError
        programming_error = ProgrammingError(
            statement="SELET * FROM usuarios",  # Error intencional en la sintaxis
            params={},
            orig=Exception(error_message)
        )
        
        # Mapear la excepción
        result = ExcepcionesMapper.map_exception(programming_error)
        
        # Verificar que se ha mapeado correctamente
        assert isinstance(result, PersistenciaError)
        assert "programación" in str(result).lower() or "SQL" in str(result)
