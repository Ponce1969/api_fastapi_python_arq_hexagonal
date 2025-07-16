# app/servicios/usuario_servicio.py
from typing import List, Optional
from uuid import UUID

from app.dominio.entidades.usuario import Usuario
from app.dominio.excepciones.dominio_excepciones import EmailYaRegistradoError, UsuarioNoEncontradoError, CredencialesInvalidasError
from app.dominio.objetos_valor.correo_electronico import CorreoElectronico
from app.dominio.interfaces.unit_of_work import IUnitOfWork
from app.core.seguridad.hashing import Hasher # Necesitarás crear esta clase/función en core/seguridad/hashing.py


class UsuarioServicio:
    """
    Servicio de aplicación para la gestión de usuarios.
    Contiene la lógica de negocio para operaciones CRUD de usuarios.
    
    Utiliza el patrón Unit of Work para garantizar la atomicidad de las transacciones
    y el acceso coordinado a múltiples repositorios cuando sea necesario.
    """
    def __init__(self, uow: IUnitOfWork, hasher: Hasher):
        # El servicio depende de la INTERFAZ del Unit of Work, no de la implementación concreta
        self.uow = uow
        self.hasher = hasher

    async def crear_usuario(self, email: str, password: str, full_name: str) -> Usuario:
        """
        Crea un nuevo usuario en el sistema.
        Valida que el email no esté ya registrado y hashea la contraseña.
        """
        # Paso 1: Validar el email usando el objeto de valor
        email_obj = CorreoElectronico(email) # Esto lanzará EmailInvalidoError si el formato es incorrecto

        async with self.uow as uow:
            # Paso 2: Verificar si el usuario ya existe por email (lógica de negocio)
            usuario_existente = await uow.usuarios.get_by_email(email_obj.valor)
            if usuario_existente:
                raise EmailYaRegistradoError(email_obj.valor)

            # Paso 3: Hashear la contraseña (utilidad de seguridad)
            hashed_password = self.hasher.hash_password(password)

            # Paso 4: Crear la entidad de dominio Usuario
            nuevo_usuario = Usuario(
                email=email_obj.valor,
                hashed_pwd=hashed_password,
                full_name=full_name,
                is_active=True # Los nuevos usuarios están activos por defecto
            )

            # Paso 5: Persistir la entidad usando el repositorio (abstracción)
            usuario_creado = await uow.usuarios.save(nuevo_usuario)
            # El commit se realizará automáticamente al salir del contexto si no hay excepciones
            
            return usuario_creado

    async def obtener_usuario_por_id(self, user_id: UUID) -> Usuario:
        """Obtiene un usuario por su ID, lanzando un error si no existe."""
        async with self.uow as uow:
            usuario = await uow.usuarios.get_by_id(user_id)
            if not usuario:
                raise UsuarioNoEncontradoError(str(user_id))
            return usuario

    async def obtener_todos_los_usuarios(self, skip: int = 0, limit: int = 100) -> List[Usuario]:
        """Obtiene una lista paginada de todos los usuarios."""
        async with self.uow as uow:
            return await uow.usuarios.get_all(skip=skip, limit=limit)

    async def actualizar_usuario(
        self, user_id: UUID, email: Optional[str] = None, full_name: Optional[str] = None, is_active: Optional[bool] = None
    ) -> Usuario:
        """
        Actualiza los datos de un usuario existente.
        Utiliza los métodos de la entidad de dominio para aplicar los cambios.
        """
        async with self.uow as uow:
            # Obtenemos el usuario dentro del contexto de la transacción
            usuario = await uow.usuarios.get_by_id(user_id)
            if not usuario:
                raise UsuarioNoEncontradoError(str(user_id))
                
            updated_at_original = usuario.updated_at

            if email is not None:
                email_obj = CorreoElectronico(email)
                if email_obj.valor != usuario.email:
                    otro_usuario = await uow.usuarios.get_by_email(email_obj.valor)
                    if otro_usuario and otro_usuario.id != user_id:
                        raise EmailYaRegistradoError(email_obj.valor)
                    usuario.actualizar_email(email_obj.valor)

            if full_name is not None:
                usuario.actualizar_nombre(full_name)

            if is_active is not None:
                if is_active:
                    usuario.activar()
                else:
                    usuario.desactivar()

            # Solo guardamos en la base de datos si la entidad ha sido modificada
            if usuario.updated_at != updated_at_original:
                return await uow.usuarios.save(usuario)

            return usuario

    async def eliminar_usuario(self, user_id: UUID) -> None:
        """Elimina un usuario por su ID."""
        async with self.uow as uow:
            # Nos aseguramos de que el usuario exista antes de intentar borrarlo
            usuario = await uow.usuarios.get_by_id(user_id)
            if not usuario:
                raise UsuarioNoEncontradoError(str(user_id))
                
            await uow.usuarios.delete(user_id)

    async def verificar_credenciales(self, email: str, password: str) -> Usuario:
        """
        Verifica las credenciales del usuario (email y contraseña) para el inicio de sesión.
        """
        email_obj = CorreoElectronico(email)
        
        async with self.uow as uow:
            usuario = await uow.usuarios.get_by_email(email_obj.valor)

            if not usuario:
                raise CredencialesInvalidasError("Correo electrónico o contraseña incorrectos.")

            if not self.hasher.verify_password(password, usuario.hashed_pwd):
                raise CredencialesInvalidasError("Correo electrónico o contraseña incorrectos.")

            if not usuario.is_active:
                raise CredencialesInvalidasError("La cuenta de usuario está inactiva.")

            return usuario

    async def cambiar_contrasena(self, user_id: UUID, contrasena_actual: str, nueva_contrasena: str) -> None:
        """
        Permite a un usuario cambiar su contraseña, verificando primero la actual.
        """
        async with self.uow as uow:
            usuario = await uow.usuarios.get_by_id(user_id)
            if not usuario:
                raise UsuarioNoEncontradoError(str(user_id))

            if not self.hasher.verify_password(contrasena_actual, usuario.hashed_pwd):
                raise CredencialesInvalidasError("La contraseña actual es incorrecta.")

            nueva_contrasena_hasheada = self.hasher.hash_password(nueva_contrasena)
            usuario.cambiar_contrasena(nueva_contrasena_hasheada)

            await uow.usuarios.save(usuario)