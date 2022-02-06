"""Application module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.logger import logger as fastapi_logger

from .containers import Container
from .routers import user


from logging import config

# setup loggers
config.fileConfig('logging.conf', disable_existing_loggers=False)


async def on_start_up():
    fastapi_logger.info("on_start_up")


async def on_shutdown():
    fastapi_logger.info("on_shutdown")


def create_app() -> FastAPI:
    container = Container()

    # db = container.db()
    # db.create_database()

    app = FastAPI(on_startup=[on_start_up], on_shutdown=[on_shutdown])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=container.config.cors.allow_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    setattr(app, 'container', container)
    app.include_router(user.router, prefix="/user")
    return app


app = create_app()
