import os

from pydantic_settings import BaseSettings

INTERNAL_SERVICE_TOKEN = os.getenv("INTERNAL_SERVICE_TOKEN")


class Settings(BaseSettings):
    service_name: str
    environment: str
    service_port: int

    jwt_secret_key: str
    jwt_algorithm: str
    internal_service_token: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
