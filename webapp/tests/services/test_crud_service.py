from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
import pytest

from webapp.containers import Container
from webapp.services.database import Database


@containers.override(Container)
class OverridingContainer(containers.DeclarativeContainer):
    config = providers.Configuration(yaml_files=["config.yml"])
    db = providers.Singleton(Database, db_url=config.db.test_url)


@pytest.fixture
@inject
def db(database: Database = Provide[Container.db]):
    print(database.db_url)
    return database


async def test_a(db):
    pass