# app/dominio/excepciones/dominio_excepciones.py

class DominioExcepcion(Exception):
    """Clase base para excepciones específicas del dominio."""
    pass


# Excepciones relacionadas con la persistencia
class PersistenciaError(DominioExcepcion):
    """Clase base para excepciones relacionadas con la persistencia de datos."""
    pass


class ConexionDBError(PersistenciaError):
    """Se lanza cuando hay problemas de conexión con la base de datos."""
    def __init__(self, mensaje: str = "Error de conexión con la base de datos"):
        self.mensaje = mensaje
        super().__init__(mensaje)


class TimeoutDBError(PersistenciaError):
    """Se lanza cuando una operación de base de datos excede el tiempo límite."""
    def __init__(self, operacion: str = "desconocida"):
        self.operacion = operacion
        mensaje = f"La operación '{operacion}' ha excedido el tiempo límite"
        super().__init__(mensaje)


class PermisosDBError(PersistenciaError):
    """Se lanza cuando hay problemas de permisos en la base de datos."""
    def __init__(self, mensaje: str = "Permisos insuficientes para realizar la operación"):
        self.mensaje = mensaje
        super().__init__(mensaje)


class ClaveForaneaError(PersistenciaError):
    """Se lanza cuando se viola una restricción de clave foránea."""
    def __init__(self, entidad: str, clave: str):
        self.entidad = entidad
        self.clave = clave
        mensaje = f"No existe la entidad '{entidad}' con identificador '{clave}'"
        super().__init__(mensaje)


class RestriccionCheckError(PersistenciaError):
    """Se lanza cuando se viola una restricción de verificación (check constraint)."""
    def __init__(self, campo: str, valor: str, restriccion: str = ""):
        self.campo = campo
        self.valor = valor
        self.restriccion = restriccion
        mensaje = f"El valor '{valor}' para el campo '{campo}' no cumple con las restricciones"
        if restriccion:
            mensaje += f": {restriccion}"
        super().__init__(mensaje)

class EmailInvalidoError(DominioExcepcion):
    """Se lanza cuando una dirección de correo electrónico no tiene un formato válido."""
    pass

class EmailYaRegistradoError(DominioExcepcion):
    """Se lanza cuando se intenta registrar un email que ya existe."""
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"El correo electrónico '{email}' ya está registrado.")

class UsuarioNoEncontradoError(DominioExcepcion):
    """Se lanza cuando no se encuentra un usuario por su identificador."""
    def __init__(self, identificador: str):
        self.identificador = identificador
        super().__init__(f"No se encontró ningún usuario con el identificador '{identificador}'.")

class CredencialesInvalidasError(DominioExcepcion):
    """Se lanza cuando el email o la contraseña son incorrectos, o el usuario está inactivo."""
    pass

class RolNoEncontradoError(DominioExcepcion):
    """Se lanza cuando no se encuentra un rol por su identificador."""
    def __init__(self, identificador: str):
        self.identificador = identificador
        super().__init__(f"No se encontró ningún rol con el identificador '{identificador}'.")

class RolYaExisteError(DominioExcepcion):
    """Se lanza cuando se intenta crear un rol con un nombre que ya existe."""
    def __init__(self, nombre: str):
        self.nombre = nombre
        super().__init__(f"El rol con el nombre '{nombre}' ya existe.")

class ContactoNoEncontradoError(DominioExcepcion):
    """Se lanza cuando no se encuentra un contacto por su identificador."""
    def __init__(self, identificador: str):
        self.identificador = identificador
        super().__init__(f"No se encontró ningún contacto con el identificador '{identificador}'.")

class EntidadNoEncontradaError(DominioExcepcion):
    """Excepción genérica para cuando no se encuentra una entidad."""
    def __init__(self, tipo_entidad: str, identificador: str):
        self.tipo_entidad = tipo_entidad
        self.identificador = identificador
        super().__init__(f"No se encontró {tipo_entidad} con el identificador '{identificador}'.")

# Aquí puedes añadir otras excepciones de dominio que necesites.
# Por ejemplo:
# class ContrasenaInvalidaError(DominioExcepcion):
#     """Se lanza cuando una contraseña no cumple con los criterios de seguridad."""
#     pass