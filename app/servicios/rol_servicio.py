# app/servicios/rol_servicio.py
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.dominio.entidades.rol import Rol
from app.dominio.entidades.usuario import Usuario
from app.dominio.repositorios.rol_repositorio import IRolRepositorio
from app.dominio.repositorios.usuario_repositorio import IUsuarioRepositorio
from app.dominio.excepciones.dominio_excepciones import RolNoEncontradoError, RolYaExisteError, UsuarioNoEncontradoError

class RolServicio:
    """
    Servicio de aplicación para la gestión de roles.
    Contiene la lógica de negocio para operaciones con roles.
    """
    def __init__(self, rol_repositorio: IRolRepositorio, usuario_repositorio: Optional[IUsuarioRepositorio] = None, db_session: Optional[AsyncSession] = None):
        self.rol_repositorio = rol_repositorio
        self.usuario_repositorio = usuario_repositorio
        self.db_session = db_session

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
        if not self.usuario_repositorio or not self.db_session:
            raise ValueError("Se requiere usuario_repositorio y db_session para esta operación")
            
        # Importaciones locales para evitar dependencias circulares
        from app.infraestructura.persistencia.modelos_orm import UsuarioORM, RolORM
        
        # Obtener entidades de dominio para validación
        rol = await self.obtener_rol_por_id(rol_id)
        usuario = await self.usuario_repositorio.get_by_id(user_id)
        if not usuario:
            raise UsuarioNoEncontradoError(str(user_id))
            
        # Trabajar con los modelos ORM para la relación muchos-a-muchos
        usuario_orm: UsuarioORM = await self.db_session.get(UsuarioORM, user_id)
        rol_orm: RolORM = await self.db_session.get(RolORM, rol_id)
        
        if rol_orm not in usuario_orm.roles:
            usuario_orm.roles.append(rol_orm)
            await self.db_session.commit()
            
        # Volver a obtener las entidades actualizadas
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
        if not self.usuario_repositorio or not self.db_session:
            raise ValueError("Se requiere usuario_repositorio y db_session para esta operación")
            
        # Importaciones locales para evitar dependencias circulares
        from app.infraestructura.persistencia.modelos_orm import UsuarioORM, RolORM
        
        # Obtener entidades de dominio para validación
        rol = await self.obtener_rol_por_id(rol_id)
        usuario = await self.usuario_repositorio.get_by_id(user_id)
        if not usuario:
            raise UsuarioNoEncontradoError(str(user_id))
            
        # Trabajar con los modelos ORM para la relación muchos-a-muchos
        usuario_orm: UsuarioORM = await self.db_session.get(UsuarioORM, user_id)
        rol_orm: RolORM = await self.db_session.get(RolORM, rol_id)
        
        if rol_orm in usuario_orm.roles:
            usuario_orm.roles.remove(rol_orm)
            await self.db_session.commit()
            
        # Volver a obtener las entidades actualizadas
        return usuario, rol
