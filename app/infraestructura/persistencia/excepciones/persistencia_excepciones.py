"""
Módulo para el mapeo de excepciones técnicas de SQLAlchemy a excepciones de dominio.

Este módulo proporciona un mapeador que traduce las excepciones técnicas generadas
por SQLAlchemy y otros componentes de la capa de infraestructura a excepciones
de dominio que son significativas para la lógica de negocio.
"""
import re
import asyncio
import traceback
from typing import Optional, Type

from sqlalchemy.exc import (
    IntegrityError,
    NoResultFound,
    SQLAlchemyError,
    DBAPIError,
    OperationalError,
    TimeoutError as SQLAlchemyTimeoutError,
    ProgrammingError,
    DataError
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
    PATRON_FOREIGN_KEY_VIOLATION = r"violates foreign key constraint \"([^\"]+)\""
    PATRON_FOREIGN_KEY_DETAILS = r"Key \(([^)]+)\)=\(([^)]+)\) is not present in table \"([^\"]+)\""
    PATRON_CHECK_CONSTRAINT = r"violates check constraint \"([^\"]+)\""
    PATRON_CHECK_DETAILS = r"Key \(([^)]+)\)=\(([^)]+)\)"
    PATRON_PERMISSION_ERROR = r"permission denied"
    
    # Patrones de error para timeouts y conexiones
    PATRON_TIMEOUT = r"timeout"
    PATRON_CONNECTION_ERROR = r"(connection|network|server|host)\s+(error|refused|closed|unavailable)"
    PATRON_OPERATIONAL_ERROR = r"(operational error|database is locked)"
    
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
        elif isinstance(exception, OperationalError):
            return cls._map_operational_error(exception)
        elif isinstance(exception, SQLAlchemyTimeoutError):
            return cls._map_timeout_error(exception)
        elif isinstance(exception, asyncio.TimeoutError):
            # Manejar también los TimeoutError de asyncio
            return cls._map_timeout_error(exception)
        elif isinstance(exception, ProgrammingError):
            return cls._map_programming_error(exception)
        elif isinstance(exception, DataError):
            return cls._map_data_error(exception)
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
        
        # Usar el código SQLSTATE si está disponible (más robusto que regex)
        if hasattr(exception.orig, 'pgcode'):
            pg_code = exception.orig.pgcode
            
            if pg_code == '23505':  # Unique Violation
                # Todavía podemos usar regex para extraer detalles específicos
                unique_match = re.search(cls.PATRON_UNIQUE_VIOLATION, error_message)
                constraint_name = unique_match.group(1) if unique_match else "desconocido"
                
                if "email" in constraint_name.lower() or "correo" in constraint_name.lower():
                    email_match = re.search(cls.PATRON_EMAIL_COLUMN, error_message)
                    email = email_match.group(1) if email_match else "desconocido"
                    return EmailYaRegistradoError(email)
                return DominioExcepcion(f"Violación de unicidad: {constraint_name}")
                
            elif pg_code == '23503':  # Foreign Key Violation
                fk_details_match = re.search(cls.PATRON_FOREIGN_KEY_DETAILS, error_message)
                if fk_details_match:
                    campo = fk_details_match.group(1)
                    valor = fk_details_match.group(2)
                    tabla = fk_details_match.group(3)
                    entidad = tabla.replace("_", " ").title()
                    return ClaveForaneaError(entidad, valor)
                
                # Intentar extraer al menos el nombre de la restricción para dar un mensaje más informativo
                fk_match = re.search(cls.PATRON_FOREIGN_KEY_VIOLATION, error_message)
                constraint_name = fk_match.group(1) if fk_match else "desconocida"
                return ClaveForaneaError(
                    "Entidad referenciada", 
                    "no encontrada", 
                    f"Violación de clave foránea en restricción: {constraint_name}"
                )
                
            elif pg_code == '23514':  # Check Violation
                check_match = re.search(cls.PATRON_CHECK_CONSTRAINT, error_message)
                constraint_name = check_match.group(1) if check_match else "desconocido"
                check_details_match = re.search(cls.PATRON_CHECK_DETAILS, error_message)
                if check_details_match:
                    campo = check_details_match.group(1)
                    valor = check_details_match.group(2)
                    return RestriccionCheckError(campo, valor, constraint_name)
                
                # Si no podemos extraer los detalles específicos, dar un mensaje más descriptivo
                # basado en el nombre de la restricción
                return RestriccionCheckError(
                    "valor proporcionado", 
                    "no cumple con las restricciones", 
                    f"Violación de restricción de verificación: {constraint_name}"
                )
        
        # Fallback a la lógica basada en regex si no hay pgcode disponible
        # Detectar violaciones de restricciones únicas
        unique_match = re.search(cls.PATRON_UNIQUE_VIOLATION, error_message)
        if unique_match:
            constraint_name = unique_match.group(1)
            
            # Manejar violación de unicidad en email
            if "email" in constraint_name.lower() or "correo" in constraint_name.lower():
                email_match = re.search(cls.PATRON_EMAIL_COLUMN, error_message)
                email = email_match.group(1) if email_match else "desconocido"
                return EmailYaRegistradoError(email)
        
        # Detectar violaciones de clave foránea
        fk_match = re.search(cls.PATRON_FOREIGN_KEY_VIOLATION, error_message)
        if fk_match:
            constraint_name = fk_match.group(1)
            fk_details_match = re.search(cls.PATRON_FOREIGN_KEY_DETAILS, error_message)
            
            if fk_details_match:
                campo = fk_details_match.group(1)
                valor = fk_details_match.group(2)
                tabla = fk_details_match.group(3)
                # Convertir nombre de tabla a una entidad de dominio más amigable
                entidad = tabla.replace("_", " ").title()
                return ClaveForaneaError(entidad, valor)
        
        # Detectar violaciones de restricciones de verificación (check constraints)
        check_match = re.search(cls.PATRON_CHECK_CONSTRAINT, error_message)
        if check_match:
            constraint_name = check_match.group(1)
            check_details_match = re.search(cls.PATRON_CHECK_DETAILS, error_message)
            
            if check_details_match:
                campo = check_details_match.group(1)
                valor = check_details_match.group(2)
                return RestriccionCheckError(campo, valor, constraint_name)
        
        # Si no podemos determinar el tipo específico de error de integridad
        return DominioExcepcion(f"Error de integridad de datos: {error_message}")
    
    @classmethod
    def _map_data_error(cls, exception: DataError) -> DominioExcepcion:
        """
        Mapea un error de datos de SQLAlchemy a una excepción de dominio.
        
        Los errores de datos (DataError) ocurren cuando los datos proporcionados no son
        compatibles con el tipo de columna, como valores demasiado largos para un campo,
        valores numéricos fuera de rango, o formatos de fecha/hora inválidos.
        
        Args:
            exception: La excepción DataError de SQLAlchemy a mapear.
            
        Returns:
            DominioExcepcion: Una excepción de dominio que describe el problema de datos
            de manera significativa para la lógica de negocio.
        """
        error_message = str(exception)
        
        # Usar el código SQLSTATE si está disponible
        if hasattr(exception.orig, 'pgcode'):
            pg_code = exception.orig.pgcode
            
            # Códigos comunes de DataError
            if pg_code == '22001':  # string_data_right_truncation
                return DominioExcepcion(f"Error de datos: El valor es demasiado largo para el campo. Detalles: {error_message}")
            elif pg_code == '22003':  # numeric_value_out_of_range
                return DominioExcepcion(f"Error de datos: El valor numérico está fuera de rango. Detalles: {error_message}")
            elif pg_code == '22007':  # invalid_datetime_format
                return DominioExcepcion(f"Error de datos: Formato de fecha/hora inválido. Detalles: {error_message}")
            elif pg_code == '22P02':  # invalid_text_representation
                return DominioExcepcion(f"Error de datos: Formato de texto inválido para el tipo de datos. Detalles: {error_message}")
        
        # Si no podemos determinar el tipo específico de error de datos
        return DominioExcepcion(f"Error de datos: El valor proporcionado no es válido para este campo. Detalles: {error_message}")
    
    @classmethod
    def _map_operational_error(cls, exception: OperationalError) -> DominioExcepcion:
        """
        Mapea un error operacional de SQLAlchemy a una excepción de dominio.
        
        Args:
            exception: El error operacional a mapear.
            
        Returns:
            Una excepción de dominio que representa el error operacional.
        """
        error_message = str(exception)
        
        # Usar el código SQLSTATE si está disponible (más robusto que regex)
        if hasattr(exception.orig, 'pgcode'):
            pg_code = exception.orig.pgcode
            
            # Códigos comunes de errores operacionales
            if pg_code.startswith('08'):  # Errores de conexión (08XXX)
                return ConexionDBError(f"Error de conexión a la base de datos: {error_message}")
            elif pg_code.startswith('42'):  # Errores de sintaxis/permisos (42XXX)
                if pg_code == '42501':  # insufficient_privilege
                    return PermisosDBError(f"Privilegios insuficientes para realizar la operación: {error_message}")
                else:
                    return PersistenciaError(f"Error de sintaxis SQL: {error_message}")
            elif pg_code.startswith('53'):  # Errores de recursos (53XXX)
                return RecursosDBError(f"Recursos insuficientes en la base de datos: {error_message}")
            elif pg_code.startswith('57'):  # Errores de operador (57XXX)
                return PersistenciaError(f"Error de operador en la base de datos: {error_message}")
            elif pg_code.startswith('58'):  # Errores de sistema (58XXX)
                return PersistenciaError(f"Error de sistema en la base de datos: {error_message}")
        
        # Fallback a la lógica basada en regex si no hay pgcode disponible
        # Detectar errores de conexión
        if re.search(cls.PATRON_CONNECTION_ERROR, error_message, re.IGNORECASE):
            return ConexionDBError(f"Error de conexión a la base de datos: {error_message}")
        
        # Detectar errores de permisos
        if re.search(cls.PATRON_PERMISSION_ERROR, error_message, re.IGNORECASE):
            return PermisosDBError(f"Error de permisos en la base de datos: {error_message}")
        
        # Otros errores operacionales
        return PersistenciaError(f"Error operacional en la base de datos: {error_message}")
    
    @classmethod
    def _map_timeout_error(cls, exception: Exception) -> DominioExcepcion:
        """
        Mapea un error de timeout a una excepción de dominio.
        
        Args:
            exception: El error de timeout a mapear.
            
        Returns:
            Una excepción de dominio que representa el error de timeout.
        """
        error_message = str(exception)
        operacion = "desconocida"
        
        # Intentar extraer información sobre la operación que causó el timeout
        if "query" in error_message.lower():
            operacion = "consulta"
        elif "update" in error_message.lower():
            operacion = "actualización"
        elif "insert" in error_message.lower():
            operacion = "inserción"
        elif "delete" in error_message.lower():
            operacion = "eliminación"
        
        return TimeoutDBError(operacion)
    
    @classmethod
    def _map_programming_error(cls, exception: ProgrammingError) -> DominioExcepcion:
        """
        Mapea un error de programación SQL a una excepción de dominio.
        
        Args:
            exception: El error de programación a mapear.
            
        Returns:
            Una excepción de dominio que representa el error de programación.
        """
        error_message = str(exception)
        
        # Detectar errores de permisos
        if re.search(cls.PATRON_PERMISSION_ERROR, error_message, re.IGNORECASE):
            return PermisosDBError(f"Error de permisos en la base de datos: {error_message}")
        
        return PersistenciaError(f"Error de programación SQL: {error_message}")
    
    @classmethod
    def _map_sqlalchemy_error(cls, exception: SQLAlchemyError) -> DominioExcepcion:
        """
        Mapea un error general de SQLAlchemy a una excepción de dominio.
        
        Args:
            exception: El error de SQLAlchemy a mapear.
            
        Returns:
            Una excepción de dominio que representa el error de SQLAlchemy.
        """
        return PersistenciaError(f"Error de base de datos: {str(exception)}")
    
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
