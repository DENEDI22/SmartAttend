from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Security
    secret_key: str

    # Database
    database_url: str = "sqlite:////app/data/smartattend.db"

    # MQTT
    mqtt_broker: str = "mqtt"
    mqtt_port: int = 1883

    # Network
    server_ip: str = "localhost"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
