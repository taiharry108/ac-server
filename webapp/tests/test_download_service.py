import pytest
from fastapi.testclient import TestClient

from webapp.services.download_service import DownloadService

from ..application import app

@pytest.mark.asyncio
async def test_get_soup():
    download_service: DownloadService = app.container.download_service()
    print(await download_service.get_json("http://ip.jsontest.com/"))

