from bs4 import BeautifulSoup
import pytest

from webapp.services.download_service import DownloadService
from logging import getLogger
from ..application import app


logger = getLogger(__name__)

@pytest.fixture(scope="module")
def download_service() -> DownloadService:
    return app.container.download_service()

async def test_get_json(download_service):
    json_data = await download_service.get_json("http://ip.jsontest.com/")
    assert 'ip' in json_data.keys()


async def test_get_bytes(download_service):
    b = await download_service.get_bytes("http://ip.jsontest.com/")


async def test_get_soup(download_service):
    soup: BeautifulSoup = await download_service.get_soup("https://www.example.com")
    assert soup.find('title').text == "Example Domain"
