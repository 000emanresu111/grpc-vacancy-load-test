import grpc
import json
import random
import time
from locust import HttpUser, task, between, events
import gevent
import logging
from grpc_vacancy_load_test.models import Config
from grpc_vacancy_load_test.rpc_signin_user_pb2 import SignInUserInput
from grpc_vacancy_load_test.rpc_create_vacancy_pb2 import CreateVacancyRequest
from grpc_vacancy_load_test.rpc_update_vacancy_pb2 import UpdateVacancyRequest
from grpc_vacancy_load_test.vacancy_service_pb2 import GetVacanciesRequest, VacancyRequest
from grpc_vacancy_load_test.vacancy_service_pb2_grpc import VacancyServiceStub
from grpc_vacancy_load_test.auth_service_pb2_grpc import AuthServiceStub

logging.basicConfig(level=logging.INFO)

class VacancyTestUser(HttpUser):
    wait_time = between(1, 2)

    def __init__(self, environment):
        super().__init__(environment)
        self.channel = None
        self.auth_stub = None
        self.vacancy_stub = None
        self.token = None
        self.user_index = 0
        self.config = None
        self.vacancy_id = None
        self.background_task = None

    def on_start(self) -> None:
        """Initialize the test user by setting up configurations and logging in."""
        self.setup()
        self.background_task = gevent.spawn(self.background_fetch_all_vacancies)
        self.schedule_recurring_tasks()

    def on_stop(self) -> None:
        """Close the gRPC channel and stop background tasks when the test user stops."""
        if self.channel:
            self.channel.close()
        if self.background_task:
            self.background_task.kill()

    def setup(self) -> None:
        """Load configurations, set up gRPC channel, and log in the user."""
        self.load_config()
        self.setup_grpc_channel()
        self.login()

    def load_config(self) -> None:
        """Load configurations from the credentials.json file."""
        try:
            with open('credentials.json', 'r') as f:
                config_data = json.load(f)
                self.config = Config(**config_data)
            logging.info("Configuration loaded")
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")

    def setup_grpc_channel(self) -> None:
        """Set up the gRPC channel and stubs for authentication and vacancy services."""
        if not self.config:
            logging.error("Configuration is not loaded")
            return

        try:
            self.channel = grpc.insecure_channel(self.config.server_address)
            self.auth_stub = AuthServiceStub(self.channel)
            self.vacancy_stub = VacancyServiceStub(self.channel)
            logging.info("gRPC channel and stubs initialized")
        except Exception as e:
            logging.error(f"Error initializing gRPC channel and stubs: {e}")

    def login(self) -> None:
        """Log in the user using the authentication service."""
        if not self.auth_stub:
            logging.error("auth_stub is not initialized")
            return

        creds = self.config.user_credentials[self.user_index]
        signin_request = SignInUserInput(
            email=creds.email,
            password=creds.password
        )
        start_time = time.time()
        try:
            response = self.auth_stub.SignInUser(signin_request, timeout=10)
            self.token = response.access_token
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name="SignInUser",
                response_time=total_time,
                response_length=len(response.access_token),
                exception=None,
                context={}
            )
            logging.info("User logged in successfully")
        except grpc.RpcError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name="SignInUser",
                response_time=total_time,
                response_length=0,
                exception=e,
                context={}
            )
            logging.error(f"Login failed: {e}")
        self.user_index = (self.user_index + 1) % len(self.config.user_credentials)

    def schedule_recurring_tasks(self) -> None:
        """Schedule recurring tasks to run every 30 seconds."""
        gevent.spawn_later(30, self.recurring_tasks)

    @task
    def recurring_tasks(self) -> None:
        """Execute the sequence of create, update, fetch, and delete vacancy tasks."""
        self.create_vacancy()
        self.update_vacancy()
        self.fetch_vacancy()
        self.delete_vacancy()
        self.schedule_recurring_tasks()

    def create_vacancy(self) -> None:
        """Create a new vacancy with pseudo-random data."""
        if not self.vacancy_stub:
            logging.error("vacancy_stub is not initialized")
            return

        metadata = (('authorization', f'Bearer {self.token}'),)
        create_request = CreateVacancyRequest(
            Title='Test Vacancy ' + str(random.randint(1, 1000)),
            Description='Test Description',
            Country='Test Country'
        )
        self._make_grpc_call(self.vacancy_stub.CreateVacancy, create_request, metadata, "CreateVacancy")

    def update_vacancy(self) -> None:
        """Update the vacancy with new data."""
        if not self.vacancy_id:
            return

        metadata = (('authorization', f'Bearer {self.token}'),)
        update_request = UpdateVacancyRequest(
            Id=self.vacancy_id,
            Title='Updated Test Vacancy ' + str(random.randint(1, 1000)),
            Description='Updated Description'
        )
        self._make_grpc_call(self.vacancy_stub.UpdateVacancy, update_request, metadata, "UpdateVacancy")

    def fetch_vacancy(self) -> None:
        """Fetch the details of the created vacancy."""
        if not self.vacancy_id:
            return

        metadata = (('authorization', f'Bearer {self.token}'),)
        fetch_request = VacancyRequest(Id=self.vacancy_id)
        self._make_grpc_call(self.vacancy_stub.GetVacancy, fetch_request, metadata, "GetVacancy")

    def delete_vacancy(self) -> None:
        """Delete the created vacancy."""
        if not self.vacancy_id:
            return

        metadata = (('authorization', f'Bearer {self.token}'),)
        delete_request = VacancyRequest(Id=self.vacancy_id)
        self._make_grpc_call(self.vacancy_stub.DeleteVacancy, delete_request, metadata, "DeleteVacancy")

    def background_fetch_all_vacancies(self) -> None:
        """Fetch all vacancies and reschedule the task."""
        if not self.vacancy_stub:
            logging.error("vacancy_stub is not initialized")
            return

        metadata = (('authorization', f'Bearer {self.token}'),)
        fetch_all_request = GetVacanciesRequest()
        self._make_grpc_call(self.vacancy_stub.GetVacancies, fetch_all_request, metadata, "GetAllVacancies")
        gevent.spawn_later(45, self.background_fetch_all_vacancies)

    def _make_grpc_call(self, stub_method, request, metadata, method_name):
        """Helper method to make a gRPC call and handle events and logging."""
        start_time = time.time()
        try:
            response = stub_method(request, metadata=metadata, timeout=2)
            total_time = int((time.time() - start_time) * 1000)
            response_length = len(str(response)) if response else 0
            events.request.fire(
                request_type="gRPC",
                name=method_name,
                response_time=total_time,
                response_length=response_length,
                exception=None,
                context={}
            )
            logging.info(f"{method_name} succeeded")
        except grpc.RpcError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name=method_name,
                response_time=total_time,
                response_length=0,
                exception=e,
                context={}
            )
            logging.error(f"{method_name} failed: {e}")
        gevent.sleep(0)
