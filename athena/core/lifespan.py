import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager
from athena.core.config import AzureSettings
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

logger = logging.getLogger()


def get_blob_container_connection(azure_config: AzureSettings) -> ContainerClient:
    blob_client = BlobServiceClient.from_connection_string(
        conn_str=azure_config.storage_connection_string,
        credential=azure_config.storage_account_key,
    )
    blob_container = blob_client.get_container_client(azure_config.storage_container)
    logger.info("Created azure blob container client")
    return blob_container


def get_formrecognizer_connection(
    azure_config: AzureSettings,
) -> DocumentAnalysisClient:
    form_recognizer_client = DocumentAnalysisClient(
        endpoint=azure_config.formrecognizer_endpoint,
        credential=AzureKeyCredential(azure_config.formrecognizer_key),
    )
    logger.info("Created azure form recognizer client")
    return form_recognizer_client


def get_cognitive_search_connection(azure_config: AzureSettings) -> SearchClient:
    search_client = SearchClient(
        endpoint=f"https://{azure_config.search_service}.search.windows.net/",
        index_name=azure_config.search_index,
        credential=AzureKeyCredential(azure_config.search_keys),
    )
    logger.info("Created azure cognitive search client")
    return search_client


@asynccontextmanager
async def azure_resource_connections(app: FastAPI):
    config = AzureSettings()
    app.state.blob_container = get_blob_container_connection(config)
    app.state.formrecognizer = get_formrecognizer_connection(config)
    app.state.cognitive_search = get_cognitive_search_connection(config)
    yield
    app.state.blob_container.close()
    app.state.formrecognizer.close()
    app.state.cognitive_search.close()
