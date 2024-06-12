from pydantic import BaseModel, SecretStr
from typing import List

class UserCredentials(BaseModel):
    name: str
    email: str
    password: str
    verification_code: str

class Config(BaseModel):
    server_address: str
    user_credentials: List[UserCredentials]
