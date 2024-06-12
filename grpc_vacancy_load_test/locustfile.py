import grpc
import json
import random
import time
import logging
from locust import HttpUser, task, between, events
from grpc_vacancy_load_test.models import Config, UserCredentials
from grpc_vacancy_load_test.rpc_signin_user_pb2 import SignInUserInput
from grpc_vacancy_load_test.rpc_signup_user_pb2 import SignUpUserInput
from grpc_vacancy_load_test.rpc_create_vacancy_pb2 import CreateVacancyRequest
from grpc_vacancy_load_test.rpc_update_vacancy_pb2 import UpdateVacancyRequest
from grpc_vacancy_load_test.vacancy_service_pb2 import GetVacanciesRequest, VacancyRequest
from grpc_vacancy_load_test.vacancy_service_pb2_grpc import VacancyServiceStub
from grpc_vacancy_load_test.auth_service_pb2_grpc import AuthServiceStub

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VacancyTestUser(HttpUser):
    wait_time = between(1, 2)

    def __init__(self, parent):
        super().__init__(parent)
        self.channel = None
        self.auth_stub = None
        self.vacancy_stub = None
        self.token = None
        self.user_index = 0
        self.config = None
        self.vacancy_id = None

    def on_start(self):
        self.setup()
        self.background_fetch_all_vacancies()

    def on_stop(self):
        if self.channel:
            self.channel.close()

    def setup(self):
        self.load_config()
        self.setup_grpc_channel()
        self.login()

    def load_config(self):
        try:
            with open('credentials.json', 'r') as f:
                config_data = json.load(f)
                self.config = Config(**config_data)
            logger.info("Configuration loaded")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")

    def setup_grpc_channel(self):
        try:
            self.channel = grpc.insecure_channel(self.config.server_address)
            self.auth_stub = AuthServiceStub(self.channel)
            self.vacancy_stub = VacancyServiceStub(self.channel)
            logger.info("gRPC channel and stubs initialized")
        except Exception as e:
            logger.error(f"Error initializing gRPC channel and stubs: {e}")

    def login(self):
        if not self.auth_stub:
            logger.error("auth_stub is not initialized")
            return
        
        creds = self.config.user_credentials[self.user_index]
        signin_request = SignInUserInput(
            email=creds.email,
            password=creds.password
        )
        start_time = time.time()
        try:
            response = self.auth_stub.SignInUser(signin_request)
            self.token = response.access_token
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name="SignInUser",
                response_time=total_time,
                response_length=0
            )
            logger.info("User logged in successfully")
        except grpc.RpcError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name="SignInUser",
                response_time=total_time,
                exception=e
            )
            logger.error(f"Login failed: {e}")
        self.user_index = (self.user_index + 1) % len(self.config.user_credentials)

    @task
    def recurring_task(self):
        self.create_vacancy()
        self.update_vacancy()
        self.fetch_vacancy()
        self.delete_vacancy()

    def create_vacancy(self):
        if not self.vacancy_stub:
            logger.error("vacancy_stub is not initialized")
            return
        
        metadata = (('authorization', f'Bearer {self.token}'),)
        create_request = CreateVacancyRequest(
            Title='Test Vacancy ' + str(random.randint(1, 1000)),
            Description='Test Description',
            Country='Test Country'
        )
        start_time = time.time()
        try:
            create_response = self.vacancy_stub.CreateVacancy(create_request, metadata=metadata)
            self.vacancy_id = create_response.id
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name="CreateVacancy",
                response_time=total_time,
                response_length=0
            )
            logger.info("Vacancy created successfully")
        except grpc.RpcError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name="CreateVacancy",
                response_time=total_time,
                exception=e
            )
            logger.error(f"CreateVacancy failed: {e}")

    def update_vacancy(self):
        if self.vacancy_id is None:
            return
        
        metadata = (('authorization', f'Bearer {self.token}'),)
        update_request = UpdateVacancyRequest(
            id=self.vacancy_id,
            title='Updated Test Vacancy ' + str(random.randint(1, 1000)),
            description='Updated Description'
        )
        start_time = time.time()
        try:
            self.vacancy_stub.UpdateVacancy(update_request, metadata=metadata)
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name="UpdateVacancy",
                response_time=total_time,
                response_length=0
            )
            logger.info("Vacancy updated successfully")
        except grpc.RpcError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name="UpdateVacancy",
                response_time=total_time,
                exception=e
            )
            logger.error(f"UpdateVacancy failed: {e}")

    def fetch_vacancy(self):
        if self.vacancy_id is None:
            return
        
        metadata = (('authorization', f'Bearer {self.token}'),)
        fetch_request = VacancyRequest(id=self.vacancy_id)
        start_time = time.time()
        try:
            self.vacancy_stub.GetVacancy(fetch_request, metadata=metadata)
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name="GetVacancy",
                response_time=total_time,
                response_length=0
            )
            logger.info("Vacancy fetched successfully")
        except grpc.RpcError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name="GetVacancy",
                response_time=total_time,
                exception=e
            )
            logger.error(f"GetVacancy failed: {e}")

    def delete_vacancy(self):
        if self.vacancy_id is None:
            return
        
        metadata = (('authorization', f'Bearer {self.token}'),)
        delete_request = VacancyRequest(id=self.vacancy_id)
        start_time = time.time()
        try:
            self.vacancy_stub.DeleteVacancy(delete_request, metadata=metadata)
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name="DeleteVacancy",
                response_time=total_time,
                response_length=0
            )
            logger.info("Vacancy deleted successfully")
        except grpc.RpcError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name="DeleteVacancy",
                response_time=total_time,
                exception=e
            )
            logger.error(f"DeleteVacancy failed: {e}")

    @task
    def fetch_all_vacancies(self):
        if not self.vacancy_stub:
            logger.error("vacancy_stub is not initialized")
            return

        metadata = (('authorization', f'Bearer {self.token}'),)
        fetch_all_request = GetVacanciesRequest()
        start_time = time.time()
        try:
            self.vacancy_stub.GetVacancies(fetch_all_request, metadata=metadata)
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name="GetVacancies",
                response_time=total_time,
                response_length=0
            )
            logger.info("All vacancies fetched successfully")
        except grpc.RpcError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name="GetVacancies",
                response_time=total_time,
                exception=e
            )
            logger.error(f"GetVacancies failed: {e}")

    @task
    def recurring_fetch_all_vacancies(self):
        while True:
            time.sleep(45)
            self.fetch_all_vacancies()

    def background_fetch_all_vacancies(self):
        import threading
        thread = threading.Thread(target=self.recurring_fetch_all_vacancies)
        thread.daemon = True
        thread.start()
