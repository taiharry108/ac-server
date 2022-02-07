"""Containers module."""

from pathlib import Path
from dependency_injector import containers, providers
from webapp.services.async_service import AsyncService

from webapp.services.download_service import DownloadService
from webapp.services.manhuagui_scraping_service import ManhuaguiScrapingService
from webapp.services.manhuaren_scraping_service import ManhuarenScrapingService



from .database import Database


class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(
        modules=[],
        packages=[".tests", ".routers"])

    config = providers.Configuration(yaml_files=["config.yml"])

    db = providers.Singleton(Database, db_url=config.db.url)

    async_service = providers.Singleton(AsyncService, num_workers=5, delay=0.3)

    download_service = providers.Singleton(
        DownloadService,
        max_connections=config.download_service.max_connections,
        max_keepalive_connections=config.download_service.max_keepalive_connections,
        headers=config.download_service.headers,
        download_dir=config.download_service.download_dir
    )

    scraping_service_factory = providers.FactoryAggregate(
        manhuaren=providers.Singleton(
            ManhuarenScrapingService, download_service, async_service),
        manhuagui=providers.Singleton(
            ManhuaguiScrapingService, download_service, async_service)
    )

