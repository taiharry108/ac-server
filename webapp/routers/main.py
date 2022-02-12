from logging import getLogger
from typing import Dict, List, Tuple
from fastapi import APIRouter, Depends
from fastapi import Response, status
from fastapi.responses import StreamingResponse
from webapp.containers import Container

from dependency_injector.wiring import inject, Provider, Provide
from dependency_injector import providers
from webapp.models.chapter import Chapter
from webapp.models.manga import Manga, MangaBase
from webapp.models.manga_index_type_enum import MangaIndexTypeEnum
from webapp.models.manga_site_enum import MangaSiteEnum
from webapp.services.abstract_manga_site_scraping_service import AbstractMangaSiteScrapingService
from webapp.services.crud_service import CRUDService

from webapp.models.db_models import Manga as DBManga, MangaSite as DBMangaSite, Chapter as DBChapter, Page as DBPage

router = APIRouter()


logger = getLogger(__name__)


def get_manga_site_id(site: MangaSiteEnum, crud_service: CRUDService) -> int:
    return crud_service.get_id_by_attr(
        DBMangaSite, "name", site.value)


def save_chapters(crud_service: CRUDService, chapters: List[Chapter], manga_id: int, index_type: MangaIndexTypeEnum) -> bool:
    chapters = [
        {
            "title": chapter.title,
            "page_url": chapter.page_url,
            "manga_id": manga_id,
            "type": index_type.value
        } for chapter in chapters]
    return crud_service.bulk_create_objs_with_unique_key(
        DBChapter, chapters, "page_url")


def save_pages(crud_service: CRUDService, pages: List[Dict], chapter_id: int) -> bool:
    num_pages = len(pages)

    pages = [{
        "pic_path": page["pic_path"],
        "idx": page["idx"],
        "chapter_id": chapter_id,
        "total": num_pages
    } for page in pages]

    return crud_service.bulk_create_objs_with_unique_key(
        DBPage, pages, "pic_path")


def get_chapter_precheck(response: Response, chapter_id: int, crud_service: CRUDService) -> Tuple[DBChapter, DBManga]:
    db_chapter = crud_service.get_item_by_id(DBChapter, chapter_id)

    if not db_chapter:
        response.status_code = status.HTTP_406_NOT_ACCEPTABLE
        return None, None

    db_manga = crud_service.get_item_by_id(DBManga, db_chapter.manga_id)

    if not db_manga:
        response.status_code = status.HTTP_406_NOT_ACCEPTABLE

    return db_chapter, db_manga


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
    logger.info(mangas)
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
        save_chapters(crud_service, chapters, manga_id, index_type)

        manga.chapters[index_type] = crud_service.get_items_by_attrs(
            DBChapter, "page_url", page_urls)

    return manga


@router.get('/chapter/{site}/{chapter_id}')
@inject
async def get_chapter(response: Response,
                      site: MangaSiteEnum,
                      chapter_id: int,
                      scraping_service_factory: providers.FactoryAggregate = Depends(
                          Provider[Container.scraping_service_factory]),
                      crud_service: CRUDService = Depends(Provide[Container.crud_service])):

    pages = crud_service.get_items_by_same_attr(
        DBPage, "chapter_id", chapter_id, "idx")

    if pages:
        logger.info("found pages in db")
        return pages

    scraping_service: AbstractMangaSiteScrapingService = scraping_service_factory(
        site)

    db_chapter, db_manga = get_chapter_precheck(
        response, chapter_id, crud_service)

    if not db_chapter or not db_manga:
        return {"success": "failed"}

    manga = MangaBase.from_orm(db_manga)
    chapter = Chapter.from_orm(db_chapter)

    result = []
    async for img_dict in scraping_service.download_chapter(manga, chapter):
        result.append(img_dict)

    save_pages(crud_service, result, chapter_id)

    all_urls = [item["pic_path"] for item in result]
    result = crud_service.get_items_by_attrs(DBPage, "pic_path", all_urls)

    return result
