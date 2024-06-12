from pydantic import BaseModel, Field, EmailStr, SecretStr
from typing import List

class UserCredentials(BaseModel):
    email: EmailStr
    password: SecretStr
    token: str = Field(default="")

class Config(BaseModel):
    server_address: str
    credentials_file: str
    user_credentials: List[UserCredentials]