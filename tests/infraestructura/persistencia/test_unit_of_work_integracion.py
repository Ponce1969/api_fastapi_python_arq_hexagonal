"""
Pruebas de integración para el patrón Unit of Work y el mapeador de excepciones.

Este módulo contiene pruebas que verifican la correcta integración del patrón
Unit of Work con el mapeador de excepciones en escenarios reales de uso.
"""
import asyncio
import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, OperationalError
from unittest.mock import patch, MagicMock

from app.dominio.excepciones.dominio_excepciones import (
    EmailYaRegistradoError,
    ClaveForaneaError,
    EntidadNoEncontradaError,
    PersistenciaError,
    RolNoEncontradoError,
    ContactoNoEncontradoError,
    DominioExcepcion,
    TimeoutDBError,
    PermisosDBError,
    RestriccionCheckError
)
from app.infraestructura.persistencia.unit_of_work import SQLAlchemyUnitOfWork
from app.infraestructura.persistencia.base import Base
from app.infraestructura.persistencia.modelos_orm import UsuarioORM, RolORM
from app.dominio.entidades.usuario import Usuario
from app.dominio.entidades.rol import Rol
from app.infraestructura.persistencia.implementaciones_repositorios.usuario_repositorio_impl import UsuarioRepositorioImpl
from app.infraestructura.persistencia.implementaciones_repositorios.rol_repositorio_impl import RolRepositorioImpl


# Configuración para pruebas
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    """Crea un motor de base de datos en memoria para las pruebas."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    """Crea una fábrica de sesiones para las pruebas."""
    async_session_factory = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    
    # Crear las tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield async_session_factory
    
    # Limpiar las tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def unit_of_work(session_factory):
    """Crea una instancia de UnitOfWork para las pruebas."""
    return SQLAlchemyUnitOfWork(session_factory)


@pytest_asyncio.fixture
async def rol_admin(unit_of_work):
    """Crea un rol de administrador para las pruebas."""
    async with unit_of_work as uow:
        rol = Rol(
            name="admin",
            description="Rol de administrador"
        )
        await uow.roles.save(rol)
        await uow.commit()
        return rol


@pytest.mark.asyncio
async def test_unit_of_work_commit_exitoso(unit_of_work):
    """Prueba que el UnitOfWork realiza commit correctamente."""
    # Crear un usuario
    usuario = Usuario(
        email="test_fk@example.com",
        hashed_pwd="hashed_password",
        full_name="Test FK User",
        is_active=True
    )
    
    # Guardar el usuario usando UnitOfWork
    async with unit_of_work as uow:
        await uow.usuarios.save(usuario)
        await uow.commit()
    
    # Verificar que el usuario se guardó correctamente
    async with unit_of_work as uow:
        usuario_guardado = await uow.usuarios.get_by_email("test_fk@example.com")
        assert usuario_guardado is not None
        assert usuario_guardado.email == "test_fk@example.com"
        assert usuario_guardado.full_name == "Test FK User"


@pytest.mark.asyncio
async def test_unit_of_work_rollback_automatico(unit_of_work):
    """Prueba que el UnitOfWork realiza rollback automáticamente si hay una excepción."""
    # Crear un usuario
    usuario = Usuario(
        email="test_rollback@example.com",
        hashed_pwd="hashed_password",
        full_name="Test Rollback User",
        is_active=True
    )
    
    # Intentar guardar el usuario y luego lanzar una excepción
    with pytest.raises(DominioExcepcion) as excinfo:
        async with unit_of_work as uow:
            await uow.usuarios.save(usuario)
            # Simular un error
            raise ValueError("Error simulado para probar rollback")
    
    # Verificar que la excepción contiene el mensaje original
    assert "Error simulado para probar rollback" in str(excinfo.value)
    
    # Verificar que el usuario NO se guardó debido al rollback automático
    async with unit_of_work as uow:
        usuario_db = await uow.usuarios.get_by_email("test_rollback@example.com")
        assert usuario_db is None


@pytest.mark.asyncio
async def test_mapeo_email_duplicado(unit_of_work):
    """Prueba que el mapeador de excepciones maneja correctamente emails duplicados."""
    # Crear un usuario
    usuario1 = Usuario(
        email="duplicate@example.com",
        hashed_pwd="hashed_password",
        full_name="Original User",
        is_active=True
    )
    
    # Guardar el primer usuario
    async with unit_of_work as uow:
        await uow.usuarios.save(usuario1)
        await uow.commit()
    
    # Crear otro usuario con el mismo email
    usuario2 = Usuario(
        email="duplicate@example.com",  # Email duplicado
        hashed_pwd="hashed_password2",
        full_name="Duplicate User",
        is_active=True
    )
    
    # Intentar guardar el segundo usuario con el mismo email
    with pytest.raises(DominioExcepcion) as excinfo:
        async with unit_of_work as uow:
            await uow.usuarios.save(usuario2)
            await uow.commit()
    
    # Verificar que se lanzó la excepción correcta
    assert "integridad" in str(excinfo.value).lower() or "integrity" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_entidad_no_encontrada_rol(unit_of_work):
    """Prueba que el repositorio devuelve None cuando una entidad no existe."""
    # Crear un rol falso con un ID que no existe
    rol_falso_id = uuid.uuid4()
    
    # Intentar obtener un rol que no existe
    async with unit_of_work as uow:
        # Intentar obtener un rol que no existe
        rol = await uow.roles.get_by_id(rol_falso_id)
        # Verificar que el resultado es None
        assert rol is None
        await uow.commit()


@pytest.mark.asyncio
async def test_entidad_no_encontrada_usuario(unit_of_work):
    """Prueba que el repositorio devuelve None cuando un usuario no existe."""
    # Intentar obtener un usuario que no existe
    async with unit_of_work as uow:
        # Intentar obtener un usuario que no existe
        usuario = await uow.usuarios.get_by_id(uuid.uuid4())
        # Verificar que el resultado es None
        assert usuario is None
        await uow.commit()


@pytest.mark.asyncio
async def test_transaccion_atomica(unit_of_work, rol_admin):
    """Prueba que las transacciones son atómicas con UnitOfWork."""
    # Crear dos usuarios en la misma transacción
    usuario1 = Usuario(
        email="user1@example.com",
        hashed_pwd="hashed_password1",
        full_name="User 1",
        is_active=True
    )
    
    usuario2 = Usuario(
        email="user2@example.com",
        hashed_pwd="hashed_password2",
        full_name="User 2",
        is_active=True
    )
    
    # Intentar guardar ambos usuarios, pero el segundo tendrá un error
    with pytest.raises(DominioExcepcion):
        async with unit_of_work as uow:
            await uow.usuarios.save(usuario1)
            
            # Simular un error al guardar el segundo usuario
            usuario2.email = None  # Esto causará un error
            await uow.usuarios.save(usuario2)
            
            # No debería llegar a este punto
            await uow.commit()
    
    # Verificar que ninguno de los dos usuarios se guardó (atomicidad)
    async with unit_of_work as uow:
        usuario1_db = await uow.usuarios.get_by_email("user1@example.com")
        usuario2_db = await uow.usuarios.get_by_email("user2@example.com")
        
        assert usuario1_db is None
        assert usuario2_db is None


@pytest.mark.asyncio
async def test_violacion_clave_foranea(unit_of_work):
    """Prueba que el UnitOfWork maneja correctamente violaciones de clave foránea."""
    # Crear un usuario con un rol_id que no existe
    usuario = Usuario(
        email="foreign_key_test@example.com",
        hashed_pwd="hashed_password",
        full_name="FK Test User",
        is_active=True
    )
    
    # Intentar asignar un rol que no existe
    rol_id_inexistente = uuid.uuid4()
    
    # Simular una violación de clave foránea
    with patch('app.infraestructura.persistencia.implementaciones_repositorios.usuario_repositorio_impl.UsuarioRepositorioImpl.save') as mock_save:
        # Simular que el método save lanza una IntegrityError por violación de clave foránea
        error_message = f'insert or update on table "usuarios_roles" violates foreign key constraint "usuarios_roles_rol_id_fkey"\nDETAIL:  Key (rol_id)=({rol_id_inexistente}) is not present in table "roles"'
        mock_save.side_effect = IntegrityError(
            statement="INSERT INTO usuarios_roles (usuario_id, rol_id) VALUES (1, 999)",
            params={},
            orig=Exception(error_message)
        )
        
        # Intentar guardar el usuario con el rol inexistente
        with pytest.raises(ClaveForaneaError) as excinfo:
            async with unit_of_work as uow:
                await uow.usuarios.save(usuario)
                await uow.commit()
        
        # Verificar que se lanzó la excepción correcta del tipo ClaveForaneaError
        assert isinstance(excinfo.value, ClaveForaneaError)
        # Verificar que el mensaje contiene el nombre de la entidad
        assert "roles" in str(excinfo.value).lower() or "rol" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_timeout_db(unit_of_work):
    """Prueba que el UnitOfWork maneja correctamente timeouts de base de datos."""
    # Crear un usuario
    usuario = Usuario(
        email="timeout_test@example.com",
        hashed_pwd="hashed_password",
        full_name="Timeout Test User",
        is_active=True
    )
    
    # Simular un timeout de base de datos
    with patch('app.infraestructura.persistencia.implementaciones_repositorios.usuario_repositorio_impl.UsuarioRepositorioImpl.save') as mock_save:
        # Simular que el método save lanza un TimeoutError
        mock_save.side_effect = asyncio.TimeoutError("Database operation timed out")
        
        # Intentar guardar el usuario
        with pytest.raises(TimeoutDBError) as excinfo:
            async with unit_of_work as uow:
                await uow.usuarios.save(usuario)
                await uow.commit()
        
        # Verificar que se lanzó la excepción correcta del tipo TimeoutDBError
        assert isinstance(excinfo.value, TimeoutDBError)
        # Verificar que el mensaje contiene información sobre tiempo límite
        assert "tiempo límite" in str(excinfo.value).lower() or "excedido" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_error_permisos_db(unit_of_work):
    """Prueba que el UnitOfWork maneja correctamente errores de permisos de base de datos."""
    # Crear un usuario
    usuario = Usuario(
        email="permisos_test@example.com",
        hashed_pwd="hashed_password",
        full_name="Permisos Test User",
        is_active=True
    )
    
    # Simular un error de permisos
    with patch('app.infraestructura.persistencia.implementaciones_repositorios.usuario_repositorio_impl.UsuarioRepositorioImpl.save') as mock_save:
        # Simular que el método save lanza un OperationalError por permisos
        error_message = "permission denied for table usuarios"
        mock_save.side_effect = OperationalError(
            statement="INSERT INTO usuarios (email, hashed_pwd, full_name, is_active) VALUES (...)",
            params={},
            orig=Exception(error_message)
        )
        
        # Intentar guardar el usuario
        with pytest.raises(PermisosDBError) as excinfo:
            async with unit_of_work as uow:
                await uow.usuarios.save(usuario)
                await uow.commit()
        
        # Verificar que se lanzó la excepción correcta
        assert "permiso" in str(excinfo.value).lower() or "permission" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_transacciones_anidadas(unit_of_work):
    """Prueba que el UnitOfWork maneja correctamente transacciones anidadas."""
    # Crear usuarios para la prueba
    usuario1 = Usuario(
        email="nested1@example.com",
        hashed_pwd="hashed_password1",
        full_name="Nested User 1",
        is_active=True
    )
    
    usuario2 = Usuario(
        email="nested2@example.com",
        hashed_pwd="hashed_password2",
        full_name="Nested User 2",
        is_active=True
    )
    
    # Probar transacciones anidadas
    async with unit_of_work as uow_outer:
        # Guardar el primer usuario en la transacción externa
        await uow_outer.usuarios.save(usuario1)
        
        # Iniciar una transacción anidada
        async with unit_of_work as uow_inner:
            # Guardar el segundo usuario en la transacción interna
            await uow_inner.usuarios.save(usuario2)
            await uow_inner.commit()
        
        # Confirmar la transacción externa
        await uow_outer.commit()
    
    # Verificar que ambos usuarios se guardaron correctamente
    async with unit_of_work as uow:
        usuario1_db = await uow.usuarios.get_by_email("nested1@example.com")
        usuario2_db = await uow.usuarios.get_by_email("nested2@example.com")
        
        assert usuario1_db is not None
        assert usuario2_db is not None
        assert usuario1_db.email == "nested1@example.com"
        assert usuario2_db.email == "nested2@example.com"
