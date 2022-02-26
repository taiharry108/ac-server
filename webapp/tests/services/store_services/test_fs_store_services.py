import io
from logging import getLogger
from dependency_injector.wiring import inject, Provider, Provide
from dependency_injector import providers
import pytest
from webapp.services.download_service import DownloadService
from webapp.services.store_services.abstract_store_service import AbstractStoreService

from webapp.containers import Container
from webapp.services.store_services.fs_store_service import FSStoreService
import pytest

logger = getLogger(__name__)

async def tmp_data():
    for i in range(10):
        yield bytes(f"{i}", 'utf8')


@pytest.fixture
def data():
    path = "test.txt"
    return {"path": path}


@pytest.fixture
@inject
async def fs_store_service(store_service_factory: providers.Factory[AbstractStoreService] = Provider[Container.store_service_factory]):
    return store_service_factory("fs")


@pytest.fixture(autouse=True)
async def run_before_and_after_tests(fs_store_service: FSStoreService, data):
    yield
    absolute_path = fs_store_service.get_filesystem_path(data["path"])
    import os
    if os.path.exists(absolute_path):
        os.remove(absolute_path)


async def test_persist_file(fs_store_service: FSStoreService, data):
    path = data["path"]
    result = await fs_store_service.persist_file(path, tmp_data())
    assert result

    absolute_path = fs_store_service.get_filesystem_path(path)
    assert absolute_path.exists()


async def test_stat_file(fs_store_service: FSStoreService, data):
    path = data["path"]
    persist_result = await fs_store_service.persist_file(path, tmp_data())
    stat_dict = await fs_store_service.stat_file(path)
    assert persist_result
    assert len(stat_dict) == 2
