# app/servicios/rol_servicio.py
from typing import List, Optional
from uuid import UUID

from app.dominio.entidades.rol import Rol
from app.dominio.repositorios.rol_repositorio import IRolRepositorio
from app.dominio.excepciones.dominio_excepciones import RolNoEncontradoError, RolYaExisteError

class RolServicio:
    """
    Servicio de aplicación para la gestión de roles.
    Contiene la lógica de negocio para operaciones con roles.
    """
    def __init__(self, rol_repositorio: IRolRepositorio):
        self.rol_repositorio = rol_repositorio

    async def crear_rol(self, name: str, description: Optional[str] = None) -> Rol:
        """
        Crea un nuevo rol, asegurándose de que el nombre no esté ya en uso.
        """
        rol_existente = await self.rol_repositorio.get_by_name(name)
        if rol_existente:
            raise RolYaExisteError(name)

        nuevo_rol = Rol(name=name, description=description)
        return await self.rol_repositorio.save(nuevo_rol)

    async def obtener_rol_por_id(self, rol_id: UUID) -> Rol:
        """Obtiene un rol por su ID, lanzando un error si no se encuentra."""
        rol = await self.rol_repositorio.get_by_id(rol_id)
        if not rol:
            raise RolNoEncontradoError(str(rol_id))
        return rol

    async def obtener_todos_los_roles(self, skip: int = 0, limit: int = 100) -> List[Rol]:
        """Obtiene una lista paginada de todos los roles."""
        return await self.rol_repositorio.get_all(skip=skip, limit=limit)

    async def actualizar_rol(
        self, rol_id: UUID, name: Optional[str] = None, description: Optional[str] = None
    ) -> Rol:
        """Actualiza los datos de un rol existente."""
        rol_a_actualizar = await self.obtener_rol_por_id(rol_id)

        if name is not None and name != rol_a_actualizar.name:
            rol_existente = await self.rol_repositorio.get_by_name(name)
            if rol_existente and rol_existente.id != rol_id:
                raise RolYaExisteError(name)
            rol_a_actualizar.actualizar_nombre(name)

        if description is not None:
            rol_a_actualizar.actualizar_descripcion(description)

        # El método `actualizar` de la entidad ya se encarga de `updated_at`
        return await self.rol_repositorio.save(rol_a_actualizar)

    async def eliminar_rol(self, rol_id: UUID) -> None:
        """
        Elimina un rol por su ID.
        Primero verifica que el rol exista.
        """
        await self.obtener_rol_por_id(rol_id)
        await self.rol_repositorio.delete(rol_id)
