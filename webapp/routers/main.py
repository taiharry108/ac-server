from collections import defaultdict
import json
from logging import getLogger
from types import AsyncGeneratorType
from typing import Dict, List, Tuple, Union
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from fastapi.responses import StreamingResponse
from webapp.containers import Container

from dependency_injector.wiring import inject, Provider, Provide
from dependency_injector import providers
from webapp.models.anime import Anime
from webapp.models.episode import Episode
from webapp.models.chapter import Chapter
from webapp.models.manga import Manga, MangaBase
from webapp.models.manga_site_enum import MangaSiteEnum
from webapp.routers import get_session
from webapp.services.abstract_anime_site_scraping_service import AbstractAnimeSiteScrapingService
from webapp.services.abstract_manga_site_scraping_service import AbstractMangaSiteScrapingService
from webapp.services.crud_service import CRUDService

from webapp.models.db_models import Manga as DBManga, MangaSite as DBMangaSite
from webapp.models.db_models import Chapter as DBChapter, Page as DBPage, Anime as DBAnime, Episode as DBEpisode
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


logger = getLogger(__name__)


async def save_chapters(crud_service: CRUDService, session: AsyncSession, manga_id: int, manga: Manga) -> List[DBChapter]:
    all_chapters = []
    page_url_dict = {}
    for index_type in manga.chapters:
        chapters = manga.chapters[index_type]
        all_chapters += [
            {
                "title": chapter.title,
                "page_url": str(chapter.page_url),
                "manga_id": manga_id,
                "type": index_type.value
            } for chapter in chapters]
        for chapter in chapters:
            page_url_dict[chapter.page_url] = index_type

    logger.info(f"going to save chapter {len(all_chapters)=}")

    db_chapters = await crud_service.bulk_create_objs_with_unique_key(session,
                                                                      DBChapter,
                                                                      all_chapters,
                                                                      "page_url",
                                                                      auto_commit=False)

    db_chapter_dict = defaultdict(list)

    for db_chapter in db_chapters:
        page_url = db_chapter.page_url
        db_chapter_dict[page_url_dict[page_url]].append(db_chapter)

    return db_chapter_dict


async def save_episodes(session: AsyncSession, crud_service: CRUDService, episodes: List[Episode], anime_id: int) -> List[DBEpisode]:
    episodes = [{
        "title": ep.title,
        "data": ep.data,
        "last_update": ep.last_update,
        "anime_id": anime_id,
        "manual_key": f"{anime_id}:{ep.title}"
    } for ep in episodes]


    return await crud_service.bulk_create_objs_with_unique_key(
        session, DBEpisode, episodes, "manual_key", True, ["data"])


async def update_episode(session: AsyncSession,
                         db_anime: DBAnime,
                         scraping_service: AbstractAnimeSiteScrapingService,
                         crud_service: CRUDService) -> List[DBEpisode]:
    anime = Anime.from_orm(db_anime)
    eps = await scraping_service.get_index_page(anime)
    return await save_episodes(session, crud_service, eps, db_anime.id)


async def save_pages(session: AsyncSession, crud_service: CRUDService, pages: List[Dict], chapter_id: int) -> bool:
    num_pages = len(pages)

    pages = [{
        "pic_path": page["pic_path"],
        "idx": page["idx"],
        "chapter_id": chapter_id,
        "total": num_pages
    } for page in pages]
    return await crud_service.bulk_create_objs_with_unique_key(
        session, DBPage, pages, "pic_path")


async def get_chapter_precheck(session: AsyncSession, chapter_id: int, crud_service: CRUDService) -> Tuple[DBChapter, DBManga]:
    db_chapter = await crud_service.get_item_by_id(session, DBChapter, chapter_id)

    if not db_chapter:
        return None, None

    db_manga = await crud_service.get_item_by_id(session, DBManga, db_chapter.manga_id)
    return db_chapter, db_manga


async def get_episode_precheck(session: AsyncSession, episode_id: int, crud_service: CRUDService) -> Tuple[DBChapter, DBManga]:
    db_ep = await crud_service.get_item_by_id(session, DBEpisode, episode_id)

    if not db_ep:
        return None, None

    db_anime = await crud_service.get_item_by_id(session, DBAnime, db_ep.anime_id)
    return db_ep, db_anime


async def create_stream_response(session: AsyncSession,
                                 pages: List[DBPage] = None,
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

            await save_pages(session, crud_service, result, chapter_id)
        yield 'data: {}\n\n'

    return StreamingResponse(img_gen(), media_type="text/event-stream")




@router.get("/search_anime/{site}/{search_keyword}", response_model=List[Anime])
@inject
async def search_anime(site: MangaSiteEnum,
                       search_keyword: str,
                       scraping_service_factory: providers.FactoryAggregate = Depends(
                           Provider[Container.scraping_service_factory]),
                       crud_service: CRUDService = Depends(
                           Provide[Container.crud_service]),
                       session_iter: AsyncGeneratorType[AsyncSession] = Depends(get_session)):
    scraping_service: AbstractAnimeSiteScrapingService = scraping_service_factory(
        site)
    session = await session_iter.__anext__()
    site_id = await crud_service.get_id_by_attr(
        session, DBMangaSite, "name", site.value)
    animes = await scraping_service.search_anime(search_keyword)

    animes = [
        {
            "name": anime.name, "url": str(anime.url), "manga_site_id": site_id,
            "eps": anime.eps, "sub": anime.sub, "season": anime.season,
            "year": anime.year
        }
        for anime in animes]
    return await crud_service.bulk_create_objs_with_unique_key(session, DBAnime, animes, "url")


@router.get("/search/{site}/{search_keyword}", response_model=List[MangaBase])
@inject
async def search_manga(site: MangaSiteEnum,
                       search_keyword: str,
                       scraping_service_factory: providers.FactoryAggregate = Depends(
                           Provider[Container.scraping_service_factory]),
                       crud_service: CRUDService = Depends(
                           Provide[Container.crud_service]),
                       session_iter: AsyncGeneratorType[AsyncSession] = Depends(get_session)):

    scraping_service: AbstractMangaSiteScrapingService = scraping_service_factory(
        site)
    mangas = await scraping_service.search_manga(search_keyword)

    session = await session_iter.__anext__()
    manga_site_id = await crud_service.get_id_by_attr(
        session,
        DBMangaSite,
        "name",
        site.value
    )

    mangas = [{"name": manga.name, "url": str(manga.url), "manga_site_id": manga_site_id}
              for manga in mangas]
    return await crud_service.bulk_create_objs_with_unique_key(session, DBManga, mangas, "url")


@router.get("/anime_index/{site}/{anime_id}")
@inject
async def get_anime_index(site: MangaSiteEnum,
                          anime_id: int,
                          scraping_service_factory: providers.FactoryAggregate = Depends(
                              Provider[Container.scraping_service_factory]),
                          crud_service: CRUDService = Depends(
                              Provide[Container.crud_service]),
                          session_iter: AsyncGeneratorType[AsyncSession] = Depends(get_session)) -> List[Episode]:
    scraping_service: AbstractAnimeSiteScrapingService = scraping_service_factory(
        site)
    session = await session_iter.__anext__()
    db_anime = await crud_service.get_item_by_id(session, DBAnime, anime_id)

    if db_anime is None:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Anime does not exist"
        )
    return await update_episode(session, db_anime, scraping_service, crud_service)


@router.get('/index/{site}/{manga_id}')
@inject
async def get_index(site: MangaSiteEnum,
                    manga_id: int,
                    scraping_service_factory: providers.FactoryAggregate = Depends(
                        Provider[Container.scraping_service_factory]),
                    crud_service: CRUDService = Depends(
                        Provide[Container.crud_service]),
                    session_iter: AsyncGeneratorType[AsyncSession] = Depends(get_session)) -> Manga:

    scraping_service: AbstractMangaSiteScrapingService = scraping_service_factory(
        site)

    session = await session_iter.__anext__()

    db_manga = await crud_service.get_item_by_id(session, DBManga, manga_id)

    if db_manga is None:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Manga does not exist"
        )

    manga = Manga(name=db_manga.name, url=db_manga.url, id=db_manga.id)

    manga = await scraping_service.get_index_page(manga)

    db_chapter_dict = await save_chapters(crud_service, session, manga_id, manga)
    for index_type in db_chapter_dict:
        manga.chapters[index_type] = db_chapter_dict[index_type]

    meta_data = {
        # "last_update": manga.last_update,
        "finished": manga.finished,
        "thum_img": manga.thum_img
    }

    await crud_service.update_object(session, DBManga, manga_id, **meta_data, auto_commit=False)
    await session.commit()

    return manga


@router.get("/episode/{site}/{episode_id}")
@inject
async def get_episode(site: MangaSiteEnum,
                      episode_id: int,
                      scraping_service_factory: providers.FactoryAggregate = Depends(
                          Provider[Container.scraping_service_factory]),
                      crud_service: CRUDService = Depends(Provide[Container.crud_service]),
                      session_iter: AsyncGeneratorType[AsyncSession] = Depends(get_session)):

    session = await session_iter.__anext__()
    scraping_service: AbstractAnimeSiteScrapingService = scraping_service_factory(
        site)

    db_ep, db_anime = await get_episode_precheck(
        session, episode_id, crud_service)

    if not db_anime or not db_ep:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Anime or Episode does not exist"
        )

    await update_episode(session, db_anime, scraping_service, crud_service)

    async for result in scraping_service.download_episode(Anime.from_orm(db_anime), Episode.from_orm(db_ep)):
        return result


@router.get('/chapter/{site}/{chapter_id}')
@inject
async def get_chapter(site: MangaSiteEnum,
                      chapter_id: int,
                      scraping_service_factory: providers.FactoryAggregate = Depends(
                          Provider[Container.scraping_service_factory]),
                      crud_service: CRUDService = Depends(
                          Provide[Container.crud_service]),
                      session_iter: AsyncGeneratorType[AsyncSession] = Depends(get_session)):
    session = await session_iter.__anext__()
    pages = await crud_service.get_items_by_same_attr(
        session, DBPage, "chapter_id", chapter_id, "idx")

    if pages:
        logger.info("found pages in db")
        return await create_stream_response(None, pages, None, None, None, None, None)

    scraping_service: AbstractMangaSiteScrapingService = scraping_service_factory(
        site)
    logger.info("get_chapter_precheck")

    db_chapter, db_manga = await get_chapter_precheck(
        session, chapter_id, crud_service)

    if not db_chapter or not db_manga:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Manga or Chapter does not exist"
        )

    manga = MangaBase.from_orm(db_manga)
    chapter = Chapter.from_orm(db_chapter)
    logger.info("creating response")

    return await create_stream_response(session, pages, scraping_service, manga, chapter, crud_service, chapter_id)
