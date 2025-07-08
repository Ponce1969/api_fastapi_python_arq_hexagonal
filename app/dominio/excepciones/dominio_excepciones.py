# app/dominio/excepciones/dominio_excepciones.py

class DominioExcepcion(Exception):
    """Clase base para excepciones específicas del dominio."""
    pass

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
# Aquí puedes añadir otras excepciones de dominio que necesites.
# Por ejemplo:
# class ContrasenaInvalidaError(DominioExcepcion):
#     """Se lanza cuando una contraseña no cumple con los criterios de seguridad."""
#     pass