import json
from logging import getLogger
from typing import Dict, List, Tuple, Union
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Response, status
from fastapi.responses import StreamingResponse
from webapp.containers import Container

from dependency_injector.wiring import inject, Provider, Provide
from dependency_injector import providers
from webapp.models.anime import Anime
from webapp.models.episode import Episode
from webapp.models.chapter import Chapter
from webapp.models.manga import Manga, MangaBase
from webapp.models.manga_index_type_enum import MangaIndexTypeEnum
from webapp.models.manga_site_enum import MangaSiteEnum
from webapp.services.abstract_anime_site_scraping_service import AbstractAnimeSiteScrapingService
from webapp.services.abstract_manga_site_scraping_service import AbstractMangaSiteScrapingService
from webapp.services.crud_service import CRUDService

from webapp.models.db_models import Manga as DBManga, MangaSite as DBMangaSite
from webapp.models.db_models import Chapter as DBChapter, Page as DBPage, Anime as DBAnime, Episode as DBEpisode

router = APIRouter()


logger = getLogger(__name__)


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


def save_episodes(crud_service: CRUDService, episodes: List[Episode], anime_id: int) -> bool:
    episodes = [{
        "title": ep.title,
        "data": ep.data,
        "last_update": ep.last_update,
        "anime_id": anime_id,
        "manual_key": f"{anime_id}:{ep.title}"
    } for ep in episodes]

    return crud_service.bulk_create_objs_with_unique_key(
        DBEpisode, episodes, "manual_key", ["data"])


async def update_episode(db_anime: DBAnime,
                         scraping_service: AbstractAnimeSiteScrapingService,
                         crud_service: CRUDService):
    anime = Anime.from_orm(db_anime)
    eps = await scraping_service.get_index_page(anime)
    save_episodes(crud_service, eps, db_anime.id)


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


def get_chapter_precheck(chapter_id: int, crud_service: CRUDService) -> Tuple[DBChapter, DBManga]:
    db_chapter = crud_service.get_item_by_id(DBChapter, chapter_id)

    if not db_chapter:
        return None, None

    db_manga = crud_service.get_item_by_id(DBManga, db_chapter.manga_id)
    return db_chapter, db_manga


def get_episode_precheck(episode_id: int, crud_service: CRUDService) -> Tuple[DBChapter, DBManga]:
    db_ep = crud_service.get_item_by_id(DBEpisode, episode_id)

    if not db_ep:
        return None, None

    db_anime = crud_service.get_item_by_id(DBAnime, db_ep.anime_id)
    return db_ep, db_anime


def create_stream_response(pages: List[DBPage] = None,
                           scraping_service: Union[AbstractMangaSiteScrapingService, None] = None,
                           manga: Union[MangaBase, None] = None,
                           chapter: Union[Chapter, None] = None,
                           crud_service: Union[CRUDService, None] = None,
                           chapter_id: Union[int, None] = None):
    async def img_gen():
        if pages:
            for db_page in pages:
                page = {
                    "pic_path": db_page.pic_path,
                    "idx": db_page.idx,
                    "total": db_page.total
                }
                yield f'data: {json.dumps(page)}\n\n'
        else:
            result = []
            async for img_dict in scraping_service.download_chapter(manga, chapter):
                logger.info(img_dict)
                yield f'data: {json.dumps(img_dict)}\n\n'
                result.append(img_dict)
            logger.info("going to save to database")

            save_pages(crud_service, result, chapter_id)
        yield 'data: {}\n\n'

    return StreamingResponse(img_gen(), media_type="text/event-stream")


@router.get("/search_anime/{site}/{search_keyword}", response_model=List[Anime])
@inject
async def search_anime(site: MangaSiteEnum,
                       search_keyword: str,
                       scraping_service_factory: providers.FactoryAggregate = Depends(
                           Provider[Container.scraping_service_factory]),
                       crud_service: CRUDService = Depends(Provide[Container.crud_service])):
    scraping_service: AbstractAnimeSiteScrapingService = scraping_service_factory(
        site)
    site_id = crud_service.get_id_by_attr(
        DBMangaSite, "name", site.value)
    animes = await scraping_service.search_anime(search_keyword)

    all_urls = [anime.url for anime in animes]
    animes = [
        {
            "name": anime.name, "url": str(anime.url), "manga_site_id": site_id,
            "eps": anime.eps, "sub": anime.sub, "season": anime.season,
            "year": anime.year
        }
        for anime in animes]
    crud_service.bulk_create_objs_with_unique_key(DBAnime, animes, "url")
    db_animes = crud_service.get_items_by_attr(DBAnime, "url", all_urls)
    return db_animes


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

    return crud_service.get_items_by_attr(DBManga, "url", all_urls)


@router.get("/anime_index/{site}/{anime_id}")
@inject
async def get_anime_index(site: MangaSiteEnum,
                          anime_id: int,
                          scraping_service_factory: providers.FactoryAggregate = Depends(
                              Provider[Container.scraping_service_factory]),
                          crud_service: CRUDService = Depends(Provide[Container.crud_service])) -> List[Episode]:
    scraping_service: AbstractAnimeSiteScrapingService = scraping_service_factory(
        site)

    db_anime = crud_service.get_item_by_id(DBAnime, anime_id)

    if db_anime is None:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Anime does not exist"
        )
    await update_episode(db_anime, scraping_service, crud_service)
    return crud_service.get_items_by_same_attr(DBEpisode, "anime_id", anime_id)


@router.get('/index/{site}/{manga_id}')
@inject
async def get_index(site: MangaSiteEnum,
                    manga_id: int,
                    scraping_service_factory: providers.FactoryAggregate = Depends(
                        Provider[Container.scraping_service_factory]),
                    crud_service: CRUDService = Depends(Provide[Container.crud_service])) -> Manga:

    scraping_service: AbstractMangaSiteScrapingService = scraping_service_factory(
        site)
    db_manga = crud_service.get_item_by_id(DBManga, manga_id)

    if db_manga is None:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Manga does not exist"
        )

    manga = Manga(name=db_manga.name, url=db_manga.url, id=db_manga.id)

    manga = await scraping_service.get_index_page(manga)

    for index_type in manga.chapters:
        chapters = manga.chapters[index_type]
        page_urls = [chapter.page_url for chapter in chapters]
        save_chapters(crud_service, chapters, manga_id, index_type)

        manga.chapters[index_type] = crud_service.get_items_by_attr(
            DBChapter, "page_url", page_urls)

    meta_data = {
        "last_update": manga.last_update,
        "finished": manga.finished,
        "thum_img": manga.thum_img
    }

    crud_service.update_object(DBManga, manga_id, **meta_data)

    return manga


@router.get("/episode/{site}/{episode_id}")
@inject
async def get_episode(site: MangaSiteEnum,
                      episode_id: int,
                      scraping_service_factory: providers.FactoryAggregate = Depends(
                          Provider[Container.scraping_service_factory]),
                      crud_service: CRUDService = Depends(Provide[Container.crud_service])):
    scraping_service: AbstractAnimeSiteScrapingService = scraping_service_factory(
        site)

    db_ep, db_anime = get_episode_precheck(
        episode_id, crud_service)

    if not db_anime or not db_ep:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Anime or Episode does not exist"
        )

    await update_episode(db_anime, scraping_service, crud_service)

    async for result in scraping_service.download_episode(Anime.from_orm(db_anime), Episode.from_orm(db_ep)):
        return result


@router.get('/chapter/{site}/{chapter_id}')
@inject
async def get_chapter(site: MangaSiteEnum,
                      chapter_id: int,
                      scraping_service_factory: providers.FactoryAggregate = Depends(
                          Provider[Container.scraping_service_factory]),
                      crud_service: CRUDService = Depends(Provide[Container.crud_service])):
    pages = crud_service.get_items_by_same_attr(
        DBPage, "chapter_id", chapter_id, "idx")

    if pages:
        logger.info("found pages in db")
        return create_stream_response(pages, None, None, None, None, None)

    scraping_service: AbstractMangaSiteScrapingService = scraping_service_factory(
        site)
    logger.info("get_chapter_precheck")

    db_chapter, db_manga = get_chapter_precheck(
        chapter_id, crud_service)

    if not db_chapter or not db_manga:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Manga or Chapter does not exist"
        )

    manga = MangaBase.from_orm(db_manga)
    chapter = Chapter.from_orm(db_chapter)
    logger.info("creating response")

    return create_stream_response(pages, scraping_service, manga, chapter, crud_service, chapter_id)
