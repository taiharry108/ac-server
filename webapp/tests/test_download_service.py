import pytest
from fastapi.logger import logger

from webapp.services.download_service import DownloadService

from ..application import app

@pytest.mark.asyncio
async def test_get_soup():
    download_service: DownloadService = app.container.download_service()
    logger.info(await download_service.get_json("http://ip.jsontest.com/"))

