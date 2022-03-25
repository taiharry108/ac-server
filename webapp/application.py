"""Application module."""

from logging import config

# setup loggers


from .routers import user
from .containers import Container
from webapp.routers import main
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from mangum import Mangum


config.fileConfig('logging.conf', disable_existing_loggers=False)

async def on_start_up():
    pass


async def on_shutdown():
    pass


def create_app() -> FastAPI:
    container = Container()
    
    db = container.db()
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
    app.include_router(main.router, prefix="/api")
    return app


app = create_app()

@app.get("/")
async def root():
    return {"message": "hello world"}

handler = Mangum(app)