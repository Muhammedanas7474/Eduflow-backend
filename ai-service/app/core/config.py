from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str
    environment: str
    service_port: int

    jwt_secret_key: str
    jwt_algorithm: str

    class Config:
        env_file = ".env"


settings = Settings()
