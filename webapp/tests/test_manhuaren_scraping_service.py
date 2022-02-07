from dependency_injector.wiring import inject, Provider, Provide
from dependency_injector import providers
from webapp.containers import Container
from webapp.models.chapter import Chapter
from webapp.models.manga import Manga
from webapp.models.manga_index_type_enum import MangaIndexTypeEnum
from webapp.services.abstract_manga_site_scraping_service import AbstractMangaSiteScrapingService
import pytest

from logging import getLogger

from webapp.services.async_service import AsyncService

logger = getLogger(__name__)


@pytest.fixture
@inject
def scraping_service(scraping_service_factory: providers.Factory[AbstractMangaSiteScrapingService] = Provider[Container.scraping_service_factory]):
    return scraping_service_factory("manhuaren")


@pytest.fixture
@inject
def async_service(async_service: AsyncService = Provide[Container.async_service]):
    return async_service


@pytest.fixture
def manga() -> Manga:
    return Manga(name="火影忍者", url="https://www.manhuaren.com/manhua-huoyingrenzhe-naruto/")


@pytest.fixture
def chapter() -> Chapter:
    return Chapter(title="第187话", page_url='https://www.manhuaren.com/m1199828/')


@pytest.mark.parametrize("search_txt,name,url_ending", [
    ("火影", "火影忍者", "manhua-huoyingrenzhe-naruto/"),
    ("stone", "Dr.STONE", "manhua-dr-stone/")
])
async def test_search_manga(scraping_service: AbstractMangaSiteScrapingService, search_txt: str, name: str, url_ending: str):
    manga_list = await scraping_service.search_manga(search_txt)
    assert len(manga_list) != 0

    filtered_list = list(
        filter(lambda manga: manga.name == name, manga_list))
    assert len(filtered_list) != 0

    for manga in manga_list:
        if manga.name == name:
            print(manga)
            assert manga.url.endswith(url_ending)


async def test_get_index_page(scraping_service: AbstractMangaSiteScrapingService, manga: Manga):
    manga = await scraping_service.get_index_page(manga)
    assert manga.name == "火影忍者"
    assert len(manga.chapters[MangaIndexTypeEnum.CHAPTER]) == 521
    assert len(manga.chapters[MangaIndexTypeEnum.MISC]) == 20

    chap = manga.get_chapter(
        MangaIndexTypeEnum.CHAPTER, 0)
    assert chap.page_url.endswith("m5196/")
    assert chap.title == '第1卷'

    assert manga.thum_img.startswith("images")
    assert manga.thum_img.endswith("jpeg")

    logger.info(manga.chapters[MangaIndexTypeEnum.CHAPTER][0])


async def test_get_page_urls(scraping_service: AbstractMangaSiteScrapingService, chapter: Chapter):
    img_urls = await scraping_service.get_page_urls(chapter)
    assert len(img_urls) == 18

    for img_url in img_urls:
        assert img_url.startswith("https://manhua")
        assert ".jpg" in img_url


async def test_async_service(scraping_service: AbstractMangaSiteScrapingService, manga: Manga, chapter: Chapter):    
    async for item in scraping_service.download_chapter(manga, chapter):
        print(item)

    
