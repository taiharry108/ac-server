from dependency_injector.wiring import inject, Provide
from bs4 import BeautifulSoup
import pytest

from webapp.services.download_service import DownloadService
from webapp.containers import Container
from logging import getLogger
from ..application import app


logger = getLogger(__name__)


@pytest.fixture
@inject
def download_service(download_service: DownloadService = Provide[Container.download_service]) -> DownloadService:
    return download_service


async def test_get_json(download_service: DownloadService):
    json_data = await download_service.get_json("http://ip.jsontest.com/")
    assert 'ip' in json_data.keys()


async def test_get_bytes(download_service: DownloadService):
    b = await download_service.get_bytes("http://ip.jsontest.com/")


async def test_get_soup(download_service: DownloadService):
    soup: BeautifulSoup = await download_service.get_soup("https://www.example.com")
    assert soup.find('title').text == "Example Domain"
