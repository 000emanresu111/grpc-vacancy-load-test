import grpc
import json
import random
import time
from locust import HttpUser, task, between, events
from grpc_vacancy_load_test.models import Config
from compiled_proto.auth_service_pb2 import SignInUserRequest
from compiled_proto.auth_service_pb2_grpc import AuthServiceStub
from compiled_proto.vacancy_service_pb2 import CreateVacancyRequest, UpdateVacancyRequest, GetVacancyRequest, DeleteVacancyRequest, ListVacanciesRequest
from compiled_proto.vacancy_service_pb2_grpc import VacancyServiceStub

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

    def setup(self):
        self.load_config()
        self.setup_grpc_channel()
        self.login()

    def teardown(self):
        if self.channel:
            self.channel.close()

    def load_config(self):
        with open('user_credentials.json', 'r') as f:
            config_data = json.load(f)
            self.config = Config(**config_data)

    def setup_grpc_channel(self):
        self.channel = grpc.insecure_channel(self.config.server_address)
        self.auth_stub = AuthServiceStub(self.channel)
        self.vacancy_stub = VacancyServiceStub(self.channel)

    def login(self):
        creds = self.config.user_credentials[self.user_index]
        signin_request = SignInUserRequest(
            email=creds.email,
            password=creds.password.get_secret_value()
        )
        start_time = time.time()
        try:
            response = self.auth_stub.SignInUser(signin_request)
            self.token = response.token
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(
                request_type="gRPC",
                name="SignInUser",
                response_time=total_time,
                response_length=0
            )
        except grpc.RpcError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(
                request_type="gRPC",
                name="SignInUser",
                response_time=total_time,
                exception=e
            )
        self.user_index = (self.user_index + 1) % len(self.config.user_credentials)

    @task
    def recurring_task(self):
        self.create_vacancy()
        self.update_vacancy()
        self.fetch_vacancy()
        self.delete_vacancy()

    def create_vacancy(self):
        metadata = (('authorization', f'Bearer {self.token}'),)
        create_request = CreateVacancyRequest(
            title='Test Vacancy ' + str(random.randint(1, 1000)),
            description='Test Description'
        )
        start_time = time.time()
        try:
            create_response = self.vacancy_stub.CreateVacancy(create_request, metadata=metadata)
            self.vacancy_id = create_response.id
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(
                request_type="gRPC",
                name="CreateVacancy",
                response_time=total_time,
                response_length=0
            )
        except grpc.RpcError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(
                request_type="gRPC",
                name="CreateVacancy",
                response_time=total_time,
                exception=e
            )

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
            events.request_success.fire(
                request_type="gRPC",
                name="UpdateVacancy",
                response_time=total_time,
                response_length=0
            )
        except grpc.RpcError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(
                request_type="gRPC",
                name="UpdateVacancy",
                response_time=total_time,
                exception=e
            )

    def fetch_vacancy(self):
        if self.vacancy_id is None:
            return
        metadata = (('authorization', f'Bearer {self.token}'),)
        fetch_request = GetVacancyRequest(id=self.vacancy_id)
        start_time = time.time()
        try:
            self.vacancy_stub.GetVacancy(fetch_request, metadata=metadata)
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(
                request_type="gRPC",
                name="GetVacancy",
                response_time=total_time,
                response_length=0
            )
        except grpc.RpcError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(
                request_type="gRPC",
                name="GetVacancy",
                response_time=total_time,
                exception=e
            )

    def delete_vacancy(self):
        if self.vacancy_id is None:
            return
        metadata = (('authorization', f'Bearer {self.token}'),)
        delete_request = DeleteVacancyRequest(id=self.vacancy_id)
        start_time = time.time()
        try:
            self.vacancy_stub.DeleteVacancy(delete_request, metadata=metadata)
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(
                request_type="gRPC",
                name="DeleteVacancy",
                response_time=total_time,
                response_length=0
            )
        except grpc.RpcError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(
                request_type="gRPC",
                name="DeleteVacancy",
                response_time=total_time,
                exception=e
            )

    @task
    def fetch_all_vacancies(self):
        metadata = (('authorization', f'Bearer {self.token}'),)
        fetch_all_request = ListVacanciesRequest()
        start_time = time.time()
        try:
            self.vacancy_stub.ListVacancies(fetch_all_request, metadata=metadata)
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(
                request_type="gRPC",
                name="ListVacancies",
                response_time=total_time,
                response_length=0
            )
        except grpc.RpcError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(
                request_type="gRPC",
                name="ListVacancies",
                response_time=total_time,
                exception=e
            )

    @task
    def recurring_fetch_all_vacancies(self):
        metadata = (('authorization', f'Bearer {self.token}'),)
        while True:
            time.sleep(45)
            start_time = time.time()
            try:
                fetch_all_request = ListVacanciesRequest()
                self.vacancy_stub.ListVacancies(fetch_all_request, metadata=metadata)
                total_time = int((time.time() - start_time) * 1000)
                events.request_success.fire(
                    request_type="gRPC",
                    name="ListVacancies",
                    response_time=total_time,
                    response_length=0
                )
            except grpc.RpcError as e:
                total_time = int((time.time() - start_time) * 1000)
                events.request_failure.fire(
                    request_type="gRPC",
                    name="ListVacancies",
                    response_time=total_time,
                    exception=e
                )

    def on_start(self):
        self.background_fetch_all_vacancies()

    def background_fetch_all_vacancies(self):
        import threading
        thread = threading.Thread(target=self.recurring_fetch_all_vacancies)
        thread.daemon = True
        thread.start()
