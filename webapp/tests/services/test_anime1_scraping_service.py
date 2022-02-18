from datetime import datetime
from logging import getLogger
from dependency_injector.wiring import inject, Provider
from dependency_injector import providers

import pytest
from webapp.containers import Container
from webapp.models.anime import Anime
from webapp.models.episode import Episode

from webapp.services.abstract_anime_site_scraping_service import AbstractAnimeSiteScrapingService
from webapp.services.anime1_scraping_service import Anime1ScrapingService

logger = getLogger(__name__)

@pytest.fixture
@inject
def scraping_service(scraping_service_factory: providers.Factory[AbstractAnimeSiteScrapingService] = Provider[Container.scraping_service_factory]):
    return scraping_service_factory("anime1")


@pytest.mark.parametrize("search_text,name,url_ending", [
    ("東方", "ORIENT 東方少年", "cat=978")
])
async def test_search_anime(scraping_service: Anime1ScrapingService,
                            search_text: str,
                            name: str,
                            url_ending: str):
    anime_list = await scraping_service.search_anime(search_text)
    assert len(anime_list) != 0

    filtered_list = list(filter(lambda anime: anime.name == name, anime_list))

    assert len(filtered_list) != 0

    for anime in anime_list:
        if anime.name == name:
            assert anime.url.endswith(url_ending)


async def test_get_index_page(scraping_service: Anime1ScrapingService):
    anime = Anime(name="", eps="", year="", season="", sub="", url="?cat=975")
    eps = await scraping_service.get_index_page(anime)
    assert len(eps) == 18
    logger.info(eps)


async def test_get_video_url(scraping_service: Anime1ScrapingService):
    data = '%7B%22c%22%3A%22975%22%2C%22e%22%3A%2218%22%2C%22t%22%3A1645137394%2C%22p%22%3A0%2C%22s%22%3A%22e5276a7c44a725a867601e7c5bdeebe8%22%7D'
    episode = Episode(title="", last_update=datetime.now(), data=data)
    video_url = await scraping_service.get_video_url(episode)
    assert video_url.endswith("mp4")
    assert video_url.startswith("https://")


async def test_download_episode(scraping_service: Anime1ScrapingService):
    data = '%7B%22c%22%3A%22975%22%2C%22e%22%3A%2218%22%2C%22t%22%3A1645137394%2C%22p%22%3A0%2C%22s%22%3A%22e5276a7c44a725a867601e7c5bdeebe8%22%7D'
    anime = Anime(name="test", eps="", year="", season="", sub="", url="https://example.com")
    episode = Episode(title="", last_update=datetime.now(), data=data)    
    async for d in scraping_service.download_episode(anime, episode):
        logger.info(d)
