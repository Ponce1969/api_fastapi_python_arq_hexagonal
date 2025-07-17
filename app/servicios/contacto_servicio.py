# app/servicios/contacto_servicio.py
from typing import List, Optional
from uuid import UUID

from app.dominio.entidades.contacto import Contacto
from app.dominio.interfaces.unit_of_work import IUnitOfWork
from app.dominio.excepciones.dominio_excepciones import ContactoNoEncontradoError


class ContactoServicio:
    """
    Servicio de aplicación para la gestión de contactos.
    Utiliza el patrón UnitOfWork para garantizar la atomicidad de las transacciones.
    """

    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def guardar_datos_contacto(
        self,
        user_id: UUID,
        name: str,
        email: str,
        phone: str,
        message: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        zip_code: Optional[str] = None,
    ) -> Contacto:
        """
        Crea o actualiza el perfil de contacto de un usuario.
        Esta es la lógica de negocio clave: "un perfil por usuario".
        """
        async with self.uow as uow:
            contacto_existente = await uow.contactos.get_by_user_id(user_id)

            if contacto_existente:
                # Si existe, actualizarlo usando el método de la entidad.
                contacto_existente.actualizar_datos(
                    name=name,
                    email=email,
                    phone=phone,
                    message=message,
                    address=address,
                    city=city,
                    country=country,
                    zip_code=zip_code,
                )
                resultado = await uow.contactos.save(contacto_existente)
                await uow.commit()
                return resultado
            else:
                # Si no existe, crear una nueva entidad de perfil de contacto.
                nuevo_perfil_contacto = Contacto(
                    user_id=user_id,
                    name=name,
                    email=email,
                    phone=phone,
                    message=message,
                    address=address,
                    city=city,
                    country=country,
                    zip_code=zip_code,
                )
                resultado = await uow.contactos.save(nuevo_perfil_contacto)
                await uow.commit()
                return resultado

    async def obtener_contacto_por_id(self, contacto_id: UUID) -> Contacto:
        """Obtiene un contacto por su ID."""
        async with self.uow as uow:
            contacto = await uow.contactos.get_by_id(contacto_id)
            if not contacto:
                raise ContactoNoEncontradoError(str(contacto_id))
            await uow.commit()
            return contacto

    async def obtener_contacto_por_usuario_id(self, user_id: UUID) -> Contacto:
        """Obtiene el perfil de contacto de un usuario específico."""
        async with self.uow as uow:
            contacto = await uow.contactos.get_by_user_id(user_id)
            if not contacto:
                raise ContactoNoEncontradoError(f"para el usuario con ID '{user_id}'")
            await uow.commit()
            return contacto

    async def obtener_todos_los_contactos(self, skip: int = 0, limit: int = 100) -> List[Contacto]:
        """Obtiene una lista paginada de todos los contactos."""
        async with self.uow as uow:
            contactos = await uow.contactos.get_all(skip=skip, limit=limit)
            await uow.commit()
            return contactos

    async def marcar_contacto_como_leido(self, contacto_id: UUID, leido: bool = True) -> Contacto:
        """Marca un contacto como leído o no leído."""
        async with self.uow as uow:
            contacto = await uow.contactos.get_by_id(contacto_id)
            if not contacto:
                raise ContactoNoEncontradoError(str(contacto_id))
            contacto.marcar_como_leido(leido)
            resultado = await uow.contactos.save(contacto)
            await uow.commit()
            return resultado
        
    async def eliminar_contacto(self, contacto_id: UUID) -> None:
        """Elimina un contacto por su ID."""
        async with self.uow as uow:
            contacto = await uow.contactos.get_by_id(contacto_id)
            if not contacto:
                raise ContactoNoEncontradoError(str(contacto_id))
            await uow.contactos.delete(contacto_id)
            await uow.commit()