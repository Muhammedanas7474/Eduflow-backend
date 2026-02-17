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

    # AWS
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "eu-north-1"
    aws_storage_bucket_name: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
