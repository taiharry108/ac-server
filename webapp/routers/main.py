from logging import getLogger
from typing import List
from fastapi import APIRouter, Depends
from fastapi import Response, status
from webapp.containers import Container

from dependency_injector.wiring import inject, Provider, Provide
from dependency_injector import providers
from webapp.models.manga import Manga, MangaBase
from webapp.models.manga_site_enum import MangaSiteEnum
from webapp.services.abstract_manga_site_scraping_service import AbstractMangaSiteScrapingService
from webapp.services.crud_service import CRUDService

from webapp.models.db_models import Manga as DBManga, MangaSite as DBMangaSite, Chapter as DBChapter

router = APIRouter()


logger = getLogger(__name__)


def get_manga_site_id(site: MangaSiteEnum, crud_service: CRUDService) -> int:
    return crud_service.get_id_by_attr(
        DBMangaSite, "name", site.value)


@router.get("/search/{site}/{search_keyword}", response_model=List[MangaBase])
@inject
async def search_manga(site: MangaSiteEnum,
                       search_keyword: str,
                       scraping_service_factory: providers.FactoryAggregate = Depends(
                           Provider[Container.scraping_service_factory]),
                       crud_service: CRUDService = Depends(Provide[Container.crud_service])):

    scraping_service: AbstractMangaSiteScrapingService = scraping_service_factory(
        site)
    mangas = await scraping_service.search_manga(search_keyword)

    manga_site_id = crud_service.get_id_by_attr(
        DBMangaSite, "name", site.value)

    all_urls = [manga.url for manga in mangas]
    mangas = [{"name": manga.name, "url": str(manga.url), "manga_site_id": manga_site_id}
              for manga in mangas]
    crud_service.bulk_create_objs_with_unique_key(DBManga, mangas, "url")

    return crud_service.get_items_by_attrs(DBManga, "url", all_urls)


@router.get('/index/{site}/{manga_id}')
@inject
async def get_index(response: Response,
                    site: MangaSiteEnum,
                    manga_id: int,
                    scraping_service_factory: providers.FactoryAggregate = Depends(
                        Provider[Container.scraping_service_factory]),
                    crud_service: CRUDService = Depends(Provide[Container.crud_service])) -> Manga:

    scraping_service: AbstractMangaSiteScrapingService = scraping_service_factory(
        site)
    # check if manga exsits
    db_manga = crud_service.get_item_by_id(DBManga, manga_id)

    if db_manga is None:
        response.status_code = status.HTTP_406_NOT_ACCEPTABLE
        return {"success": "failed"}

    manga = Manga(name=db_manga.name, url=db_manga.url, id=db_manga.id)

    manga = await scraping_service.get_index_page(manga)

    for index_type in manga.chapters:
        chapters = manga.chapters[index_type]
        page_urls = [chapter.page_url for chapter in chapters]
        chapters = [
            {
                "title": chapter.title,
                "page_url": chapter.page_url,
                "manga_id": manga_id,
                "type": index_type.value
            } for chapter in chapters]
        crud_service.bulk_create_objs_with_unique_key(
            DBChapter, chapters, "page_url")

        manga.chapters[index_type] = crud_service.get_items_by_attrs(
            DBChapter, "page_url", page_urls)

    return manga

