import uvicorn

from fastapi import FastAPI
from athena.routers import file_handler, chat
from athena.core.logger import setup_rich_logger
from athena.core.lifespan import azure_resource_connections


def init() -> FastAPI:
    app = FastAPI(lifespan=azure_resource_connections)
    app.include_router(file_handler.router)
    app.include_router(chat.router)
    setup_rich_logger()

    return app


app = init()


def start():
    uvicorn.run("athena.main:app", host="0.0.0.0", port=8000, reload=True)
