# app/servicios/rol_servicio.py
from typing import List, Optional, Tuple
from uuid import UUID

from app.dominio.entidades.rol import Rol
from app.dominio.entidades.usuario import Usuario
from app.dominio.interfaces.unit_of_work import IUnitOfWork
from app.dominio.excepciones.dominio_excepciones import RolNoEncontradoError, RolYaExisteError, UsuarioNoEncontradoError

class RolServicio:
    """
    Servicio de aplicación para la gestión de roles.
    Contiene la lógica de negocio para operaciones con roles.
    """
    def __init__(self, uow: IUnitOfWork):
        """
        Inicializa el servicio de roles con un Unit of Work.
        
        Args:
            uow: Unit of Work que proporciona acceso transaccional a los repositorios
        """
        self.uow = uow

    async def crear_rol(self, name: str, description: Optional[str] = None) -> Rol:
        """
        Crea un nuevo rol, asegurándose de que el nombre no esté ya en uso.
        
        Args:
            name: Nombre del rol
            description: Descripción opcional del rol
            
        Returns:
            El rol creado
            
        Raises:
            RolYaExisteError: Si ya existe un rol con el mismo nombre
        """
        async with self.uow as uow:
            rol_existente = await uow.roles.get_by_name(name)
            if rol_existente:
                raise RolYaExisteError(name)

            nuevo_rol = Rol(name=name, description=description)
            rol_guardado = await uow.roles.save(nuevo_rol)
            return rol_guardado

    async def obtener_rol_por_id(self, rol_id: UUID) -> Rol:
        """Obtiene un rol por su ID, lanzando un error si no se encuentra."""
        async with self.uow as uow:
            rol = await uow.roles.get_by_id(rol_id)
            if not rol:
                raise RolNoEncontradoError(str(rol_id))
            return rol

    async def obtener_todos_los_roles(self, skip: int = 0, limit: int = 100) -> List[Rol]:
        """Obtiene una lista paginada de todos los roles."""
        async with self.uow as uow:
            roles = await uow.roles.get_all(skip=skip, limit=limit)
            return roles

    async def actualizar_rol(
        self, rol_id: UUID, name: Optional[str] = None, description: Optional[str] = None
    ) -> Rol:
        """Actualiza los datos de un rol existente."""
        async with self.uow as uow:
            rol_a_actualizar = await uow.roles.get_by_id(rol_id)
            if not rol_a_actualizar:
                raise RolNoEncontradoError(str(rol_id))

            if name is not None and name != rol_a_actualizar.name:
                rol_existente = await uow.roles.get_by_name(name)
                if rol_existente and rol_existente.id != rol_id:
                    raise RolYaExisteError(name)
                rol_a_actualizar.actualizar_nombre(name)

            if description is not None:
                rol_a_actualizar.actualizar_descripcion(description)

            # El método `actualizar` de la entidad ya se encarga de `updated_at`
            rol_actualizado = await uow.roles.save(rol_a_actualizar)
            return rol_actualizado

    async def eliminar_rol(self, rol_id: UUID) -> None:
        """
        Elimina un rol por su ID.
        Primero verifica que el rol exista.
        """
        async with self.uow as uow:
            rol = await uow.roles.get_by_id(rol_id)
            if not rol:
                raise RolNoEncontradoError(str(rol_id))
            await uow.roles.delete(rol_id)
        
    async def asignar_rol_a_usuario(self, user_id: UUID, rol_id: UUID) -> Tuple[Usuario, Rol]:
        """
        Asigna un rol a un usuario.
        
        Args:
            user_id: UUID del usuario
            rol_id: UUID del rol a asignar
            
        Returns:
            Tupla con el usuario y el rol
            
        Raises:
            UsuarioNoEncontradoError: Si no se encuentra el usuario
            RolNoEncontradoError: Si no se encuentra el rol
        """
        async with self.uow as uow:
            # Obtener entidades de dominio para validación
            rol = await uow.roles.get_by_id(rol_id)
            if not rol:
                raise RolNoEncontradoError(str(rol_id))
                
            usuario = await uow.usuarios.get_by_id(user_id)
            if not usuario:
                raise UsuarioNoEncontradoError(str(user_id))
                
            # Asignar rol al usuario usando el método del repositorio
            await uow.usuarios.asignar_rol(user_id, rol_id)
            
            # Volver a obtener las entidades actualizadas
            usuario = await uow.usuarios.get_by_id(user_id)
            rol = await uow.roles.get_by_id(rol_id)
            
            return usuario, rol
    
    async def remover_rol_de_usuario(self, user_id: UUID, rol_id: UUID) -> Tuple[Usuario, Rol]:
        """
        Remueve un rol de un usuario.
        
        Args:
            user_id: UUID del usuario
            rol_id: UUID del rol a remover
            
        Returns:
            Tupla con el usuario y el rol
            
        Raises:
            UsuarioNoEncontradoError: Si no se encuentra el usuario
            RolNoEncontradoError: Si no se encuentra el rol
        """
        async with self.uow as uow:
            # Obtener entidades de dominio para validación
            rol = await uow.roles.get_by_id(rol_id)
            if not rol:
                raise RolNoEncontradoError(str(rol_id))
                
            usuario = await uow.usuarios.get_by_id(user_id)
            if not usuario:
                raise UsuarioNoEncontradoError(str(user_id))
                
            # Remover rol del usuario usando el método del repositorio
            await uow.usuarios.remover_rol(user_id, rol_id)
            
            # Volver a obtener las entidades actualizadas
            usuario = await uow.usuarios.get_by_id(user_id)
            rol = await uow.roles.get_by_id(rol_id)
            
            return usuario, rol
