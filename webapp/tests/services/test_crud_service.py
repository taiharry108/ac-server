from webapp.models.db_models import MangaSite, Manga
from webapp.models.manga_site_enum import MangaSiteEnum
from webapp.services.crud_service import CRUDService
from webapp.services.database import Database
from webapp.containers import Container
import pytest
from pydantic import HttpUrl
from dependency_injector.wiring import Provide, inject
from dependency_injector import containers, providers
from logging import getLogger
from logging import config
config.fileConfig('logging.conf', disable_existing_loggers=False)


logger = getLogger(__name__)


@pytest.fixture(autouse=True, scope="module")
def database():
    container = Container()
    container.db.override(providers.Singleton(
        Database, db_url="postgresql://taiharry:123456@localhost:5432/testAcDB"))
    db = container.db()
    db.create_database()
    return db


@pytest.fixture(scope="module")
@inject
def crud_service(database: Database, crud_service: CRUDService = Provide[Container.crud_service]):
    crud_service.database = database
    return crud_service


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(database: Database):
    with database.session() as session:
        session.query(Manga).delete()
        session.query(MangaSite).delete()
        db_manga_site = MangaSite(
            name='manhuaren',
            url='https://www.manhuaren.com/')
        session.add(db_manga_site)
        session.commit()
        session.refresh(db_manga_site)
    yield


@pytest.fixture
def manga_site_id(crud_service: CRUDService):
    site = MangaSiteEnum.ManHuaRen
    return crud_service.get_id_by_attr(MangaSite, "name", site.value)


async def test_create_manga(crud_service: CRUDService, manga_site_id: int):
    manga_name = "Test Manga"
    manga_url = "https://example.com"

    db_manga = crud_service.create_obj(Manga, name=manga_name,
                                       url=manga_url, manga_site_id=manga_site_id)

    assert isinstance(db_manga, Manga)
    assert db_manga.name == manga_name
    assert db_manga.url == manga_url
    assert db_manga.manga_site_id == manga_site_id


async def test_bulk_create_mangas(crud_service: CRUDService, manga_site_id: int):
    logger.info(crud_service.database.db_url)
    mangas = [{
        "name": f"Test Manga {i}",
        "url": f"https://example.com/{i}",
        "manga_site_id": manga_site_id,
    } for i in range(15)]

    urls = [manga['url'] for manga in mangas]

    crud_service.bulk_create_objs(Manga, mangas)

    db_mangas = crud_service.get_items_by_attrs(Manga, "url", urls)

    assert len(db_mangas) == 15
    assert isinstance(db_mangas[0], Manga)
    for db_manga in db_mangas:
        assert db_manga.name.startswith("Test Manga")
        assert db_manga.url.startswith("https://example.com")
        assert db_manga.manga_site_id == manga_site_id


async def test_get_items_by_attrs(crud_service: CRUDService):
    urls = [f"https://example.com/{i}" for i in range(4)]
    db_mangas = crud_service.get_items_by_attrs(Manga, "url", urls)
    assert len(db_mangas) == 4
