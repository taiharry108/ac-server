from logging import getLogger
from typing import List
from fastapi import APIRouter, Depends
from webapp.containers import Container

from dependency_injector.wiring import inject, Provider, Provide
from dependency_injector import providers
from webapp.models.manga import Manga, MangaBase
from webapp.models.manga_site_enum import MangaSiteEnum
from webapp.services.abstract_manga_site_scraping_service import AbstractMangaSiteScrapingService
from webapp.services.crud_service import CRUDService

from webapp.models.db_models import Manga as DBManga

router = APIRouter()


logger = getLogger(__name__)


@router.get("/search/{site}/{search_keyword}", response_model=List[MangaBase])
@inject
async def search_manga(site: MangaSiteEnum,
                       search_keyword: str,
                       scraping_service_factory: providers.FactoryAggregate = Depends(Provider[Container.scraping_service_factory])):

    scraping_service: AbstractMangaSiteScrapingService = scraping_service_factory(
        site)
    mangas = await scraping_service.search_manga(search_keyword)
    return mangas


@router.get("/test/{manga_id}")
@inject
async def test(manga_id: int, crud_service: CRUDService = Depends(Provide[Container.crud_service])):
    result = crud_service.get_item_by_id(DBManga, manga_id)
    return result
