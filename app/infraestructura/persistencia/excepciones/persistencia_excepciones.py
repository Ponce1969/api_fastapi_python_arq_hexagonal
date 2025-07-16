"""
Módulo para el mapeo de excepciones técnicas de SQLAlchemy a excepciones de dominio.

Este módulo proporciona un mapeador que traduce las excepciones técnicas generadas
por SQLAlchemy y otros componentes de la capa de infraestructura a excepciones
de dominio que son significativas para la lógica de negocio.
"""
import re
import traceback
from typing import Optional, Type

from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError

from app.dominio.excepciones.dominio_excepciones import (
    DominioExcepcion,
    EmailYaRegistradoError,
    UsuarioNoEncontradoError,
)


class ExcepcionesMapper:
    """
    Clase que mapea excepciones técnicas de SQLAlchemy a excepciones de dominio.
    
    Esta clase proporciona métodos para traducir las excepciones generadas por
    SQLAlchemy y otros componentes de la capa de infraestructura a excepciones
    de dominio que son significativas para la lógica de negocio.
    """
    
    # Patrones de error comunes para PostgreSQL
    PATRON_UNIQUE_VIOLATION = r"duplicate key value violates unique constraint \"([^\"]+)\""
    PATRON_EMAIL_COLUMN = r"Key \(email\)=\(([^)]+)\)"
    
    @classmethod
    def map_exception(cls, exception: Exception) -> DominioExcepcion:
        """
        Mapea una excepción técnica a una excepción de dominio.
        
        Args:
            exception: La excepción técnica a mapear.
            
        Returns:
            Una excepción de dominio que representa el error de manera significativa
            para la lógica de negocio.
        """
        if isinstance(exception, IntegrityError):
            return cls._map_integrity_error(exception)
        elif isinstance(exception, NoResultFound):
            return cls._map_no_result_found(exception)
        elif isinstance(exception, SQLAlchemyError):
            return cls._map_sqlalchemy_error(exception)
        elif isinstance(exception, DominioExcepcion):
            # Si ya es una excepción de dominio, la devolvemos tal cual
            return exception
        else:
            # Para cualquier otra excepción, creamos una excepción de dominio genérica
            return DominioExcepcion(f"Error inesperado: {str(exception)}")
    
    @classmethod
    def _map_integrity_error(cls, exception: IntegrityError) -> DominioExcepcion:
        """
        Mapea un error de integridad de SQLAlchemy a una excepción de dominio.
        
        Args:
            exception: El error de integridad a mapear.
            
        Returns:
            Una excepción de dominio que representa el error de integridad.
        """
        error_message = str(exception)
        
        # Detectar violaciones de restricciones únicas
        unique_match = re.search(cls.PATRON_UNIQUE_VIOLATION, error_message)
        if unique_match:
            constraint_name = unique_match.group(1)
            
            # Manejar violación de unicidad en email
            if "email" in constraint_name.lower() or "correo" in constraint_name.lower():
                email_match = re.search(cls.PATRON_EMAIL_COLUMN, error_message)
                email = email_match.group(1) if email_match else "desconocido"
                return EmailYaRegistradoError(email)
        
        # Si no podemos determinar el tipo específico de error de integridad
        return DominioExcepcion(f"Error de integridad de datos: {error_message}")
    
    @classmethod
    def _map_no_result_found(cls, exception: NoResultFound) -> DominioExcepcion:
        """
        Mapea un error de resultado no encontrado de SQLAlchemy a una excepción de dominio.
        
        Args:
            exception: El error de resultado no encontrado a mapear.
            
        Returns:
            Una excepción de dominio que representa el error de resultado no encontrado.
        """
        # Por defecto, mapeamos a UsuarioNoEncontradoError, pero esto podría refinarse
        # según el contexto en el que se produjo la excepción
        return UsuarioNoEncontradoError("La entidad solicitada no existe")
    
    @classmethod
    def _map_sqlalchemy_error(cls, exception: SQLAlchemyError) -> DominioExcepcion:
        """
        Mapea un error general de SQLAlchemy a una excepción de dominio.
        
        Args:
            exception: El error de SQLAlchemy a mapear.
            
        Returns:
            Una excepción de dominio que representa el error de SQLAlchemy.
        """
        return DominioExcepcion(f"Error de base de datos: {str(exception)}")
    
    @classmethod
    def wrap_exception(cls, exception: Exception) -> DominioExcepcion:
        """
        Mapea una excepción técnica a una excepción de dominio y preserva el traceback.
        
        Args:
            exception: La excepción técnica a mapear.
            
        Returns:
            Una excepción de dominio con el traceback original preservado.
        """
        domain_exception = cls.map_exception(exception)
        
        # Preservar el traceback original
        tb = traceback.extract_tb(exception.__traceback__)
        tb_str = ''.join(traceback.format_list(tb))
        
        # Añadir información del traceback original como nota en la excepción de dominio
        domain_exception.__notes__ = [f"Excepción original: {exception.__class__.__name__}: {str(exception)}",
                                     f"Traceback original:\n{tb_str}"]
        
        return domain_exception
