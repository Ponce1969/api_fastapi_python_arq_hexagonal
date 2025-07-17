"""
Tests unitarios para el servicio de contacto.

Este módulo contiene pruebas para validar el funcionamiento del servicio
de contacto, incluyendo la creación, actualización, lectura y eliminación
de contactos.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock

from app.dominio.entidades.contacto import Contacto
from app.dominio.excepciones.dominio_excepciones import ContactoNoEncontradoError

# Importamos el servicio real para asegurar que se incluya en la cobertura
from app.servicios.contacto_servicio import ContactoServicio

# Creamos una clase mock para el UnitOfWork
class UnitOfWorkMock:
    """Mock del UnitOfWork para pruebas unitarias."""
    
    def __init__(self, contacto_repositorio):
        self._contacto_repositorio = contacto_repositorio
        self.committed = False
        self.rolled_back = False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
        return False
    
    async def commit(self):
        self.committed = True
    
    async def rollback(self):
        self.rolled_back = True
        
    @property
    def contactos(self):
        """Propiedad que expone el repositorio de contactos."""
        return self._contacto_repositorio


@pytest.fixture
def contacto_repositorio_mock():
    """Fixture que proporciona un mock del repositorio de contactos."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def unit_of_work_mock(contacto_repositorio_mock):
    """Fixture que proporciona un mock del UnitOfWork."""
    return UnitOfWorkMock(contacto_repositorio_mock)


@pytest.fixture
def contacto_servicio(unit_of_work_mock):
    """Fixture que proporciona una instancia del servicio de contacto con dependencias mockeadas."""
    # Ahora pasamos el UnitOfWork al servicio, ya que el servicio ha sido actualizado
    # para usar el patrón UnitOfWork correctamente
    return ContactoServicio(unit_of_work_mock)


@pytest.fixture
def contacto_mock():
    """Fixture que proporciona un mock de un contacto."""
    return Contacto(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Test User",
        email="test@example.com",
        phone="123456789",
        message="Test message",
        address="Test address",
        city="Test city",
        country="Test country",
        zip_code="12345",
        is_read=False
    )


class TestContactoServicio:
    """Tests para el servicio de contacto."""

    @pytest.mark.asyncio
    async def test_guardar_datos_contacto_nuevo(self, contacto_servicio, contacto_repositorio_mock, unit_of_work_mock):
        """Test para verificar la creación de un nuevo contacto."""
        # Configurar el mock para simular que no existe un contacto previo
        contacto_repositorio_mock.get_by_user_id.return_value = None
        
        # Configurar el mock para devolver un contacto al guardar
        contacto_guardado = Contacto(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Nuevo Usuario",
            email="nuevo@example.com",
            phone="987654321",
            message="Nuevo mensaje",
            is_read=False
        )
        contacto_repositorio_mock.save.return_value = contacto_guardado
        
        # Ejecutar el método a probar
        resultado = await contacto_servicio.guardar_datos_contacto(
            user_id=contacto_guardado.user_id,
            name=contacto_guardado.name,
            email=contacto_guardado.email,
            phone=contacto_guardado.phone,
            message=contacto_guardado.message
        )
        
        # Verificar que se llamaron los métodos correctos
        contacto_repositorio_mock.get_by_user_id.assert_called_once_with(contacto_guardado.user_id)
        contacto_repositorio_mock.save.assert_called_once()
        
        # Verificar que se hizo commit en el UnitOfWork
        assert unit_of_work_mock.committed is True
        
        # Verificar el resultado
        assert resultado == contacto_guardado
        assert resultado.name == "Nuevo Usuario"
        assert resultado.email == "nuevo@example.com"

    @pytest.mark.asyncio
    async def test_guardar_datos_contacto_existente(self, contacto_servicio, contacto_repositorio_mock, contacto_mock, unit_of_work_mock):
        """Test para verificar la actualización de un contacto existente."""
        # Configurar el mock para simular que existe un contacto previo
        contacto_repositorio_mock.get_by_user_id.return_value = contacto_mock
        
        # Configurar el mock para devolver el contacto actualizado al guardar
        contacto_actualizado = Contacto(
            id=contacto_mock.id,
            user_id=contacto_mock.user_id,
            name="Nombre Actualizado",
            email="actualizado@example.com",
            phone="123456789",
            message="Mensaje actualizado",
            is_read=contacto_mock.is_read
        )
        contacto_repositorio_mock.save.return_value = contacto_actualizado
        
        # Ejecutar el método a probar
        resultado = await contacto_servicio.guardar_datos_contacto(
            user_id=contacto_mock.user_id,
            name="Nombre Actualizado",
            email="actualizado@example.com",
            phone="123456789",
            message="Mensaje actualizado"
        )
        
        # Verificar que se llamaron los métodos correctos
        contacto_repositorio_mock.get_by_user_id.assert_called_once_with(contacto_mock.user_id)
        contacto_repositorio_mock.save.assert_called_once()
        
        # Verificar que se hizo commit en el UnitOfWork
        assert unit_of_work_mock.committed is True
        
        # Verificar el resultado
        assert resultado == contacto_actualizado
        assert resultado.name == "Nombre Actualizado"
        assert resultado.email == "actualizado@example.com"
        assert resultado.message == "Mensaje actualizado"

    @pytest.mark.asyncio
    async def test_obtener_contacto_por_id_existente(self, contacto_servicio, contacto_repositorio_mock, contacto_mock, unit_of_work_mock):
        """Test para verificar la obtención de un contacto existente por ID."""
        # Configurar el mock para devolver un contacto
        contacto_repositorio_mock.get_by_id.return_value = contacto_mock
        
        # Ejecutar el método a probar
        resultado = await contacto_servicio.obtener_contacto_por_id(contacto_mock.id)
        
        # Verificar que se llamó al método correcto
        contacto_repositorio_mock.get_by_id.assert_called_once_with(contacto_mock.id)
        
        # Verificar que se hizo commit en el UnitOfWork
        assert unit_of_work_mock.committed is True
        
        # Verificar el resultado
        assert resultado == contacto_mock

    @pytest.mark.asyncio
    async def test_obtener_contacto_por_id_no_existente(self, contacto_servicio, contacto_repositorio_mock, unit_of_work_mock):
        """Test para verificar que se lanza una excepción al buscar un contacto que no existe."""
        # Configurar el mock para devolver None
        contacto_id = uuid.uuid4()
        contacto_repositorio_mock.get_by_id.return_value = None
        
        # Verificar que se lanza la excepción esperada
        with pytest.raises(ContactoNoEncontradoError) as excinfo:
            await contacto_servicio.obtener_contacto_por_id(contacto_id)
        
        # Verificar el mensaje de la excepción
        assert str(contacto_id) in str(excinfo.value)
        
        # Verificar que se llamó al método correcto
        contacto_repositorio_mock.get_by_id.assert_called_once_with(contacto_id)
        
        # Verificar que se hizo rollback en el UnitOfWork debido a la excepción
        assert unit_of_work_mock.rolled_back is True

    @pytest.mark.asyncio
    async def test_obtener_contacto_por_usuario_id_existente(self, contacto_servicio, contacto_repositorio_mock, contacto_mock, unit_of_work_mock):
        """Test para verificar la obtención de un contacto existente por ID de usuario."""
        # Configurar el mock para devolver un contacto
        contacto_repositorio_mock.get_by_user_id.return_value = contacto_mock
        
        # Ejecutar el método a probar
        resultado = await contacto_servicio.obtener_contacto_por_usuario_id(contacto_mock.user_id)
        
        # Verificar que se llamó al método correcto
        contacto_repositorio_mock.get_by_user_id.assert_called_once_with(contacto_mock.user_id)
        
        # Verificar que se hizo commit en el UnitOfWork
        assert unit_of_work_mock.committed is True
        
        # Verificar el resultado
        assert resultado == contacto_mock

    @pytest.mark.asyncio
    async def test_obtener_contacto_por_usuario_id_no_existente(self, contacto_servicio, contacto_repositorio_mock, unit_of_work_mock):
        """Test para verificar que se lanza una excepción al buscar un contacto por ID de usuario que no existe."""
        # Configurar el mock para devolver None
        user_id = uuid.uuid4()
        contacto_repositorio_mock.get_by_user_id.return_value = None
        
        # Verificar que se lanza la excepción esperada
        with pytest.raises(ContactoNoEncontradoError) as excinfo:
            await contacto_servicio.obtener_contacto_por_usuario_id(user_id)
        
        # Verificar el mensaje de la excepción
        assert str(user_id) in str(excinfo.value)
        
        # Verificar que se llamó al método correcto
        contacto_repositorio_mock.get_by_user_id.assert_called_once_with(user_id)
        
        # Verificar que se hizo rollback en el UnitOfWork debido a la excepción
        assert unit_of_work_mock.rolled_back is True

    @pytest.mark.asyncio
    async def test_obtener_todos_los_contactos(self, contacto_servicio, contacto_repositorio_mock, contacto_mock, unit_of_work_mock):
        """Test para verificar la obtención de todos los contactos."""
        # Configurar el mock para devolver una lista de contactos
        contactos = [contacto_mock, Contacto(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Otro Usuario",
            email="otro@example.com",
            phone="999999999",
            is_read=True
        )]
        contacto_repositorio_mock.get_all.return_value = contactos
        
        # Ejecutar el método a probar
        resultado = await contacto_servicio.obtener_todos_los_contactos(skip=0, limit=10)
        
        # Verificar que se llamó al método correcto
        contacto_repositorio_mock.get_all.assert_called_once_with(skip=0, limit=10)
        
        # Verificar que se hizo commit en el UnitOfWork
        assert unit_of_work_mock.committed is True
        
        # Verificar el resultado
        assert resultado == contactos
        assert len(resultado) == 2

    @pytest.mark.asyncio
    async def test_marcar_contacto_como_leido(self, contacto_servicio, contacto_repositorio_mock, contacto_mock, unit_of_work_mock):
        """Test para verificar que se marca un contacto como leído."""
        # Configurar el mock para devolver un contacto al buscar por ID
        contacto_repositorio_mock.get_by_id.return_value = contacto_mock
        
        # Configurar el mock para devolver el contacto actualizado al guardar
        contacto_actualizado = Contacto(
            id=contacto_mock.id,
            user_id=contacto_mock.user_id,
            name=contacto_mock.name,
            email=contacto_mock.email,
            phone=contacto_mock.phone,
            message=contacto_mock.message,
            address=contacto_mock.address,
            city=contacto_mock.city,
            country=contacto_mock.country,
            zip_code=contacto_mock.zip_code,
            is_read=True
        )
        contacto_repositorio_mock.save.return_value = contacto_actualizado
        
        # Ejecutar el método a probar
        resultado = await contacto_servicio.marcar_contacto_como_leido(contacto_mock.id, True)
        
        # Verificar que se llamaron los métodos correctos
        contacto_repositorio_mock.get_by_id.assert_called_once_with(contacto_mock.id)
        contacto_repositorio_mock.save.assert_called_once()
        
        # Verificar que se hizo commit en el UnitOfWork
        assert unit_of_work_mock.committed is True
        
        # Verificar el resultado
        assert resultado == contacto_actualizado
        assert resultado.is_read is True

    @pytest.mark.asyncio
    async def test_eliminar_contacto(self, contacto_servicio, contacto_repositorio_mock, contacto_mock, unit_of_work_mock):
        """Test para verificar la eliminación de un contacto."""
        # Configurar el mock para devolver un contacto al buscar por ID
        contacto_repositorio_mock.get_by_id.return_value = contacto_mock
        
        # Ejecutar el método a probar
        await contacto_servicio.eliminar_contacto(contacto_mock.id)
        
        # Verificar que se llamaron los métodos correctos
        contacto_repositorio_mock.get_by_id.assert_called_once_with(contacto_mock.id)
        contacto_repositorio_mock.delete.assert_called_once_with(contacto_mock.id)
        
        # Verificar que se hizo commit en el UnitOfWork
        assert unit_of_work_mock.committed is True

    @pytest.mark.asyncio
    async def test_eliminar_contacto_no_existente(self, contacto_servicio, contacto_repositorio_mock, unit_of_work_mock):
        """Test para verificar que se lanza una excepción al eliminar un contacto que no existe."""
        # Configurar el mock para devolver None
        contacto_id = uuid.uuid4()
        contacto_repositorio_mock.get_by_id.return_value = None
        
        # Verificar que se lanza la excepción esperada
        with pytest.raises(ContactoNoEncontradoError) as excinfo:
            await contacto_servicio.eliminar_contacto(contacto_id)
        
        # Verificar el mensaje de la excepción
        assert str(contacto_id) in str(excinfo.value)
        
        # Verificar que se llamó al método correcto
        contacto_repositorio_mock.get_by_id.assert_called_once_with(contacto_id)
        contacto_repositorio_mock.delete.assert_not_called()
        
        # Verificar que se hizo rollback en el UnitOfWork debido a la excepción
        assert unit_of_work_mock.rolled_back is True
