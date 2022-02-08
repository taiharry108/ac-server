"""Containers module."""

from dependency_injector import containers, providers
from webapp.services.async_service import AsyncService
from webapp.services.crud_service import CRUDService

from webapp.services.download_service import DownloadService
from webapp.services.manhuagui_scraping_service import ManhuaguiScrapingService
from webapp.services.manhuaren_scraping_service import ManhuarenScrapingService
from webapp.services.store_services.fs_store_service import FSStoreService
from webapp.services.database import Database


class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(
        modules=[],
        packages=["webapp.routers", "webapp.tests"])

    config = providers.Configuration(yaml_files=["config.yml"])

    db = providers.Singleton(Database, db_url=config.db.url)

    async_service = providers.Singleton(AsyncService, num_workers=5, delay=0.3)

    store_service_factory = providers.FactoryAggregate(
        fs=providers.Singleton(
            FSStoreService,
            base_dir=config.store_service.base_dir
        )
    )

    download_service = providers.Singleton(
        DownloadService,
        max_connections=config.download_service.max_connections,
        max_keepalive_connections=config.download_service.max_keepalive_connections,
        headers=config.download_service.headers,
        store_service_factory=store_service_factory,
        store=config.download_service.store
    )

    scraping_service_factory = providers.FactoryAggregate(
        manhuaren=providers.Singleton(
            ManhuarenScrapingService, download_service, async_service),
        manhuagui=providers.Singleton(
            ManhuaguiScrapingService, download_service, async_service)
    )

    crud_service = providers.Singleton(
        CRUDService,
        database=db
    )
