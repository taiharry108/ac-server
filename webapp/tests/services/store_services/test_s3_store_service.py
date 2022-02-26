from logging import getLogger
from dependency_injector.wiring import inject, Provider
from dependency_injector import providers
import pytest
from webapp.services.store_services.abstract_store_service import AbstractStoreService

from webapp.containers import Container
import pytest

from webapp.services.store_services.s3_store_service import S3StoreService

logger = getLogger(__name__)


async def tmp_data():
    for i in range(10):
        yield bytes(f"{i}", 'utf8')

@pytest.fixture()
def data():
    path = "test1/test.txt"
    return {"path": path}


@pytest.fixture
@inject
async def s3_store_service(store_service_factory: providers.Factory[AbstractStoreService] = Provider[Container.store_service_factory]):
    return store_service_factory("s3")


@pytest.fixture(autouse=True)
async def run_before_and_after_tests(s3_store_service: S3StoreService, data):
    yield


async def test_get_boto_key(s3_store_service: S3StoreService):
    result = await s3_store_service.get_boto_key("test.png")
    assert "ETag" in result
    assert "LastModified" in result
    logger.info(type(result))
    logger.info(result)


async def test_get_boto_key_not_exist(s3_store_service: S3StoreService):
    result = await s3_store_service.get_boto_key("test.pn")
    assert len(result) == 0


async def test_file_exists(s3_store_service: S3StoreService, data):
    assert await s3_store_service.file_exists("test.png")
    assert not await s3_store_service.file_exists("test.pn")
    assert await s3_store_service.file_exists(data['path'])


async def test_persist_file(s3_store_service: S3StoreService, data):
    path = data["path"]
    result = await s3_store_service.persist_file(path, tmp_data())
    assert result == path


async def test_stat_file(s3_store_service: S3StoreService, data):
    path = data["path"]
    result = await s3_store_service.stat_file(path)
    logger.info(result)