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

    # OpenAI
    openai_api_key: str = ""

    # Hugging Face
    huggingface_api_key: str = ""

    # Database (PGVector)
    database_url: str = " "

    # Whisper
    whisper_model_size: str = "base"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
