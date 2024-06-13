import pytest
from unittest import mock
from unittest.mock import patch, MagicMock, mock_open
from locust.env import Environment
from grpc_vacancy_load_test.locustfile import VacancyTestUser 
import grpc
import gevent

@pytest.fixture
def environment():
    return Environment(user_classes=[])

@pytest.fixture
def user(environment):
    return VacancyTestUser(environment)

def test_on_start(user):
    with patch.object(user, 'setup') as mock_setup, \
         patch.object(gevent, 'spawn') as mock_spawn, \
         patch.object(user, 'schedule_recurring_tasks') as mock_schedule:
        user.on_start()
        mock_setup.assert_called_once()
        mock_spawn.assert_called_once_with(user.background_fetch_all_vacancies)
        mock_schedule.assert_called_once()

def test_on_stop(user):
    user.channel = MagicMock()
    user.background_task = MagicMock()
    user.on_stop()
    user.channel.close.assert_called_once()
    user.background_task.kill.assert_called_once()

def test_on_stop_no_background_task(user):
    user.channel = MagicMock()
    user.background_task = None
    user.on_stop()
    user.channel.close.assert_called_once()

def test_on_stop_no_channel(user):
    user.channel = None
    user.background_task = MagicMock()
    user.on_stop()
    user.background_task.kill.assert_called_once()

def test_load_config(user):
    config_data = """
    {
        "server_address": "localhost",
        "user_credentials": [
            {
                "email": "test@example.com",
                "password": "pass",
                "name": "Test User",
                "verification_code": "1234"
            }
        ]
    }
    """
    with patch('builtins.open', mock_open(read_data=config_data)):
        user.load_config()
        assert user.config.server_address == "localhost"
        assert user.config.user_credentials[0].email == "test@example.com"

def test_load_config_failure(user):
    with patch('builtins.open', side_effect=FileNotFoundError):
        user.load_config()
        assert user.config is None

def test_setup_grpc_channel(user):
    user.config = MagicMock(server_address="localhost")

    mock_channel = MagicMock(name='MockChannel')
    mock_auth_stub = MagicMock(name='MockAuthServiceStub')
    mock_vacancy_stub = MagicMock(name='MockVacancyServiceStub')

    with patch('grpc.insecure_channel', return_value=mock_channel) as mock_grpc_channel, \
         patch('auth_service_pb2_grpc.AuthServiceStub', return_value=mock_auth_stub) as mock_auth_service_stub, \
         patch('vacancy_service_pb2_grpc.VacancyServiceStub', return_value=mock_vacancy_stub) as mock_vacancy_service_stub:

        user.setup_grpc_channel()
        
        mock_grpc_channel.assert_called_once_with("localhost")
        
        assert user.channel == mock_channel






def test_setup_grpc_channel_no_config(user):
    user.config = None
    user.setup_grpc_channel()
    assert user.channel is None
    assert user.auth_stub is None
    assert user.vacancy_stub is None

def test_login_success(user):
    user.config = MagicMock(user_credentials=[MagicMock(email="test@example.com", password="pass")])
    user.auth_stub = MagicMock()
    mock_response = MagicMock(access_token="token")
    user.auth_stub.SignInUser.return_value = mock_response

    user.login()
    assert user.token == "token"

def test_login_failure(user):
    user.config = MagicMock(user_credentials=[MagicMock(email="test@example.com", password="pass")])
    user.auth_stub = MagicMock()
    user.auth_stub.SignInUser.side_effect = grpc.RpcError()

    user.login()
    assert user.token is None

def test_login_no_auth_stub(user):
    user.config = MagicMock(user_credentials=[MagicMock(email="test@example.com", password="pass")])
    user.auth_stub = None

    user.login()
    assert user.token is None

def test_schedule_recurring_tasks(user):
    with patch.object(gevent, 'spawn_later') as mock_spawn_later:
        user.schedule_recurring_tasks()
        mock_spawn_later.assert_called_once_with(30, user.recurring_tasks)

def test_create_vacancy(user):
    user.token = "token"
    user.vacancy_stub = MagicMock()
    metadata = (('authorization', 'Bearer token'),)

    user.create_vacancy()
    user.vacancy_stub.CreateVacancy.assert_called_once()

def test_create_vacancy_no_stub(user):
    user.token = "token"
    user.vacancy_stub = None
    user.create_vacancy()
    assert user.vacancy_stub is None

def test_create_vacancy_failure(user):
    user.token = "token"
    user.vacancy_stub = MagicMock()
    user.vacancy_stub.CreateVacancy.side_effect = grpc.RpcError()

    user.create_vacancy()
    user.vacancy_stub.CreateVacancy.assert_called_once()

def test_update_vacancy(user):
    user.token = "token"
    user.vacancy_id = "1"
    user.vacancy_stub = MagicMock()
    metadata = (('authorization', 'Bearer token'),)

    user.update_vacancy()
    user.vacancy_stub.UpdateVacancy.assert_called_once()

def test_update_vacancy_no_id(user):
    user.token = "token"
    user.vacancy_id = None
    user.update_vacancy()
    assert user.vacancy_id is None

def test_update_vacancy_failure(user):
    user.token = "token"
    user.vacancy_id = "1"
    user.vacancy_stub = MagicMock()
    user.vacancy_stub.UpdateVacancy.side_effect = grpc.RpcError()

    user.update_vacancy()
    user.vacancy_stub.UpdateVacancy.assert_called_once()

def test_fetch_vacancy(user):
    user.token = "token"
    user.vacancy_id = "1"
    user.vacancy_stub = MagicMock()
    metadata = (('authorization', 'Bearer token'),)

    user.fetch_vacancy()
    user.vacancy_stub.GetVacancy.assert_called_once()

def test_fetch_vacancy_no_id(user):
    user.token = "token"
    user.vacancy_id = None
    user.fetch_vacancy()
    assert user.vacancy_id is None

def test_fetch_vacancy_failure(user):
    user.token = "token"
    user.vacancy_id = "1"
    user.vacancy_stub = MagicMock()
    user.vacancy_stub.GetVacancy.side_effect = grpc.RpcError()

    user.fetch_vacancy()
    user.vacancy_stub.GetVacancy.assert_called_once()

def test_delete_vacancy(user):
    user.token = "token"
    user.vacancy_id = "1"
    user.vacancy_stub = MagicMock()
    metadata = (('authorization', 'Bearer token'),)

    user.delete_vacancy()
    user.vacancy_stub.DeleteVacancy.assert_called_once()

def test_delete_vacancy_no_id(user):
    user.token = "token"
    user.vacancy_id = None
    user.delete_vacancy()
    assert user.vacancy_id is None

def test_delete_vacancy_failure(user):
    user.token = "token"
    user.vacancy_id = "1"
    user.vacancy_stub = MagicMock()
    user.vacancy_stub.DeleteVacancy.side_effect = grpc.RpcError()

    user.delete_vacancy()
    user.vacancy_stub.DeleteVacancy.assert_called_once()

def test_background_fetch_all_vacancies(user):
    user.token = "token"
    user.vacancy_stub = MagicMock()
    metadata = (('authorization', 'Bearer token'),)

    with patch.object(gevent, 'spawn_later') as mock_spawn_later:
        user.background_fetch_all_vacancies()
        user.vacancy_stub.GetVacancies.assert_called_once()
        mock_spawn_later.assert_called_once_with(45, user.background_fetch_all_vacancies)

def test_background_fetch_all_vacancies_no_stub(user):
    user.token = "token"
    user.vacancy_stub = None

    with patch.object(gevent, 'spawn_later') as mock_spawn_later:
        user.background_fetch_all_vacancies()
        assert user.vacancy_stub is None
        mock_spawn_later.assert_not_called()

def test_make_grpc_call_success(user):
    mock_stub_method = MagicMock()
    mock_request = MagicMock()
    mock_metadata = MagicMock()

    with patch('locust.events.request.fire') as mock_fire, patch('time.time', side_effect=[1, 2, 3, 4]):
        user._make_grpc_call(mock_stub_method, mock_request, mock_metadata, "TestMethod")
        mock_stub_method.assert_called_once_with(mock_request, metadata=mock_metadata, timeout=2)
        mock_fire.assert_called_once()

def test_make_grpc_call_failure(user):
    mock_stub_method = MagicMock(side_effect=grpc.RpcError())
    mock_request = MagicMock()
    mock_metadata = MagicMock()

    with patch('locust.events.request.fire') as mock_fire, patch('time.time', side_effect=[1, 2, 3, 4]):
        user._make_grpc_call(mock_stub_method, mock_request, mock_metadata, "TestMethod")
        mock_stub_method.assert_called_once_with(mock_request, metadata=mock_metadata, timeout=2)
        mock_fire.assert_called_once()
