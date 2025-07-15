# app/servicios/contacto_servicio.py
from typing import List, Optional
from uuid import UUID

from app.dominio.entidades.contacto import Contacto
from app.dominio.repositorios.contacto_repositorio import IContactoRepositorio
from app.dominio.excepciones.dominio_excepciones import ContactoNoEncontradoError


class ContactoServicio:
    """
    Servicio de aplicación para la gestión de contactos.
    """

    def __init__(self, contacto_repositorio: IContactoRepositorio):
        self.contacto_repositorio = contacto_repositorio

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
        contacto_existente = await self.contacto_repositorio.get_by_user_id(user_id)

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
            return await self.contacto_repositorio.save(contacto_existente)
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
            return await self.contacto_repositorio.save(nuevo_perfil_contacto)

    async def obtener_contacto_por_id(self, contacto_id: UUID) -> Contacto:
        """Obtiene un contacto por su ID."""
        contacto = await self.contacto_repositorio.get_by_id(contacto_id)
        if not contacto:
            raise ContactoNoEncontradoError(str(contacto_id))
        return contacto

    async def obtener_contacto_por_usuario_id(self, user_id: UUID) -> Contacto:
        """Obtiene el perfil de contacto de un usuario específico."""
        contacto = await self.contacto_repositorio.get_by_user_id(user_id)
        if not contacto:
            raise ContactoNoEncontradoError(f"para el usuario con ID '{user_id}'")
        return contacto

    async def obtener_todos_los_contactos(self, skip: int = 0, limit: int = 100) -> List[Contacto]:
        """Obtiene una lista paginada de todos los contactos."""
        return await self.contacto_repositorio.get_all(skip=skip, limit=limit)

    async def marcar_contacto_como_leido(self, contacto_id: UUID, leido: bool = True) -> Contacto:
        """Marca un contacto como leído o no leído."""
        contacto = await self.obtener_contacto_por_id(contacto_id)
        contacto.marcar_como_leido(leido)
        return await self.contacto_repositorio.save(contacto)
        
    async def eliminar_contacto(self, contacto_id: UUID) -> None:
        """Elimina un contacto por su ID."""
        await self.obtener_contacto_por_id(contacto_id)
        await self.contacto_repositorio.delete(contacto_id)