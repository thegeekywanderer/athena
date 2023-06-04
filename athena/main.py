import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from athena.routers import file_handler, chat
from athena.core.logger import setup_rich_logger
from athena.core.lifespan import azure_resource_connections
from athena.core.config import ApiSettings


config = ApiSettings()


def init() -> FastAPI:
    app = FastAPI(lifespan=azure_resource_connections)
    app.include_router(file_handler.router)
    app.include_router(chat.router)
    setup_rich_logger()
    origins = [config.cors_origin]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = init()


def start():
    uvicorn.run("athena.main:app", host="0.0.0.0", port=8000, reload=True)
