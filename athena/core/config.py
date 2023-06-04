from typing import Literal
from pydantic import BaseSettings


class ApiSettings(BaseSettings):
    env_state: Literal["dev", "prod"]
    logger_file: str

    class Config:
        env_file = ".api.env"


class AzureSettings(BaseSettings):
    storage_account: str
    storage_connection_string: str
    storage_account_key: str
    storage_container: str
    search_service: str
    search_index: str
    search_keys: str
    semantic_configuration: str
    formrecognizer_endpoint: str
    formrecognizer_key: str

    class Config:
        env_file = ".azure.env"


class OpenAISettings(BaseSettings):
    api_key: str

    class Config:
        env_file = ".openapi.env"
