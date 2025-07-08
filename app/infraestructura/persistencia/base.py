# app/infraestructura/persistencia/base.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Clase base declarativa para los modelos ORM de SQLAlchemy 2.0.
    Todos los modelos ORM heredarán de esta clase.
    """
    pass