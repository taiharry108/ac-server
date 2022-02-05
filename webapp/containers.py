"""Containers module."""

from dependency_injector import containers, providers

from webapp.services.download_service import DownloadService


from .database import Database


class Container(containers.DeclarativeContainer):

    config = providers.Configuration(yaml_files=["config.yml"])

    db = providers.Singleton(Database, db_url=config.db.url)

    download_service = providers.Factory(
        DownloadService
    )
