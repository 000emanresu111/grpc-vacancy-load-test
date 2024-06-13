# grpc-vacancy-load-test

This is a [locust](https://docs.locust.io/en/stable/) load testing script  that fetches vacancies from
a vacancy server.

### 1) Clone the Repository
```bash
$ git clone https://github.com/000emanresu111/grpc-vacancy-load-test.git
```
### 2) Navigate into the folder
```bash
$ cd grpc-vacancy-load-test
```
### 3) Import needed files
#### 3.1) Copy the proto/ folder in the project folder
```bash
$ cp -r <path-to-proto-folder> .
```
#### 3.2) Add a credentials.json file to the root folder
It should have the following structure.
```json
{
    "server_address": "bla.bla.net:8089",
    "user_credentials":   
    [
        {
            "name": "name_1",
            "email": "email_1",
            "password": "password_1",
            "verification_code": "verification_code_1"
        },
        ...
    ]
    
  }
  
```
### 4) Compile the proto files
```bash
$ poetry run python -m grpc_tools.protoc -I=proto --python_out=. --grpc_python_out=. proto/*.proto
```
### 5) Install deps with Poetry

Ensure you have [Poetry](https://python-poetry.org) installed.

```bash
$ poetry install
```

### 6) Start the load test script

```bash
$ poetry run locust -f grpc_vacancy_load_test/locustfile.py  
```
This will also run an instance of locust UI accessible via localhost:8089

```bash
[2024-06-13 10:33:34,082] noname/INFO/locust.main: Starting web interface at http://0.0.0.0:8089
[2024-06-13 10:33:34,096] noname/INFO/locust.main: Starting Locust 2.29.0
[2024-06-13 10:33:52,098] noname/INFO/locust.runners: Ramping to 10 users at a rate of 2.00 per second
[2024-06-13 10:33:52,100] noname/INFO/root: Configuration loaded
[2024-06-13 10:33:52,120] noname/INFO/root: gRPC channel and stubs initialized
[2024-06-13 10:33:52,295] noname/INFO/root: User logged in successfully
```

### 7) Run tests
```bash
$ poetry run pytest --cov=grpc_vacancy_load_test tests/ -vv 
```

### 8) Load test flow
- Every locust user logins with one of the user credentials created beforehand.
- In a recurring flow every locust user executes the following actions every 30
seconds:
  - Create a vacancy with pseudo-random data
  - Update one or more fields in that vacancy
  - Fetch that specific vacancy
  - Delete the vacancy
- In the background the locust user fetches a list of all vacancies available on the server
every 45 seconds.
