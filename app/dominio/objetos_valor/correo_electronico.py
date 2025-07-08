# app/dominio/objetos_valor/correo_electronico.py
import re
from dataclasses import dataclass
from app.dominio.excepciones.dominio_excepciones import EmailInvalidoError

# La opción frozen=True hace que la clase sea inmutable.
# Si intentas cambiar el valor de un atributo después de la creación, lanzará una excepción.
@dataclass(frozen=True, slots=True)
class CorreoElectronico:
    """
    Objeto de valor inmutable para representar una dirección de correo electrónico válida.
    Utiliza @dataclass para un código más conciso y seguro.
    """
    valor: str

    def __post_init__(self):
        """
        Realiza la validación después de que el objeto ha sido inicializado por el decorador.
        """
        if not self._es_valido(self.valor):
            raise EmailInvalidoError(f"La dirección de correo electrónico '{self.valor}' no es válida.")

    @staticmethod
    def _es_valido(email: str) -> bool:
        """
        Valida el formato de una dirección de correo electrónico.
        Esta es una validación básica, puedes usar librerías más robustas si lo necesitas.
        """
        if not isinstance(email, str):
            return False
        # Expresión regular para una validación de email más rigurosa (ejemplo)
        # Puedes simplificarla o usar una librería como 'email_validator'
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(email_regex, email) is not None

    def __str__(self) -> str:
        return self.valor
    # __eq__, __hash__ y __repr__ son generados automáticamente por @dataclass