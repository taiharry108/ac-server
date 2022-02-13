from dependency_injector.wiring import inject, Provider, Provide
from dependency_injector import providers
from webapp.containers import Container
from webapp.models.chapter import Chapter
from webapp.models.manga import Manga
from webapp.models.manga_index_type_enum import MangaIndexTypeEnum
from webapp.services.abstract_manga_site_scraping_service import AbstractMangaSiteScrapingService
import pytest

from logging import getLogger

logger = getLogger(__name__)


@pytest.fixture
@inject
def scraping_service(scraping_service_factory: providers.Factory[AbstractMangaSiteScrapingService] = Provider[Container.scraping_service_factory]):
    return scraping_service_factory("manhuaren")


@pytest.fixture
def manga(m_data) -> Manga:
    return Manga(name=m_data["name"], url=m_data["url"])


@pytest.fixture
def chapter(c_data) -> Chapter:
    return Chapter(title=c_data["title"], page_url=c_data["page_url"])


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
            assert manga.url.endswith(url_ending)


@pytest.mark.parametrize("m_data", [
    {"name": "火影忍者", "url": "https://www.manhuaren.com/manhua-huoyingrenzhe-naruto/"}
])
async def test_get_index_page(scraping_service: AbstractMangaSiteScrapingService, manga: Manga):
    manga = await scraping_service.get_index_page(manga)
    assert manga.name == "火影忍者"
    assert len(manga.chapters[MangaIndexTypeEnum.CHAPTER]) == 521
    assert len(manga.chapters[MangaIndexTypeEnum.MISC]) == 20

    chap = manga.get_chapter(
        MangaIndexTypeEnum.CHAPTER, 0)
    assert chap.page_url.endswith("m5196/")
    assert chap.title == '第1卷'

    assert manga.thum_img.startswith("thum_img")
    assert manga.thum_img.endswith("jpeg")

    logger.info(manga.chapters[MangaIndexTypeEnum.CHAPTER][0])


@pytest.mark.parametrize("c_data", [
    {"title": "第187话", "page_url": 'https://www.manhuaren.com/m1199828/'}
])
async def test_get_page_urls(scraping_service: AbstractMangaSiteScrapingService, chapter: Chapter):
    img_urls = await scraping_service.get_page_urls(chapter)
    assert len(img_urls) == 18

    for img_url in img_urls:
        assert img_url.startswith("https://manhua")
        assert ".jpg" in img_url


@pytest.mark.parametrize("m_data,c_data", [
    ({"name": "海盗战记", "url": "https://www.manhuaren.com/manhua-haidaozhanji/"},
     {"title": "第186话", "page_url": 'https://www.manhuaren.com/m1199827/'})
])
async def test_download_chapter(scraping_service: AbstractMangaSiteScrapingService, manga: Manga, chapter: Chapter):
    async for item in scraping_service.download_chapter(manga, chapter):
        assert "pic_path" in item
        assert "idx" in item
