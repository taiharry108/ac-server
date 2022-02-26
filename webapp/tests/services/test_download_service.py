from dependency_injector.wiring import inject, Provide
from bs4 import BeautifulSoup
import pytest

from webapp.services.download_service import DownloadService
from webapp.containers import Container
from logging import getLogger


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


async def test_download_img(download_service: DownloadService):
    url = "https://placeholder.com/wp-content/uploads/2018/10/placeholder-1.png"
    result = await download_service.download_img(url, download_path="test", filename="test.png")
    assert "pic_path" in result


async def test_download_vid(download_service: DownloadService):
    url = "http://localhost:8001/Anime1/%E7%99%BD%E9%87%91%E7%B5%82%E5%B1%80(Platinum%20End)/dfb9b01655ca8dacc96b81382e47131f.mp4"

    result = await download_service.download_vid(
        url, download_path="test")
    assert "vid_path" in result
