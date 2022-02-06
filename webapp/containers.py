"""Containers module."""

from dependency_injector import containers, providers

from webapp.services.download_service import DownloadService


from .database import Database


class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(modules=[".routers.user"])

    config = providers.Configuration(yaml_files=["config.yml"])

    # db = providers.Singleton(Database, db_url=config.db.url)

    download_service = providers.Singleton(
        DownloadService,
        max_connections=config.httpx.max_connections,
        max_keepalive_connections=config.httpx.max_keepalive_connections,
    )
