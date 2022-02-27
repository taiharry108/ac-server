from webapp.models.db_models import Chapter, MangaSite, Manga, User, History
from webapp.models.manga_site_enum import MangaSiteEnum
from webapp.services.crud_service import CRUDService
from webapp.services.database import Database
from webapp.containers import Container
import pytest
from dependency_injector.wiring import Provide, inject
from logging import getLogger
from logging import config

from webapp.tests.utils import delete_all, delete_dependent_tables

from sqlalchemy.ext.asyncio import AsyncSession
config.fileConfig('logging.conf', disable_existing_loggers=False)


logger = getLogger(__name__)


@pytest.fixture(scope="module")
@inject
def crud_service(database: Database, crud_service: CRUDService = Provide[Container.crud_service]):
    crud_service.database = database
    return crud_service


@pytest.fixture
async def session(crud_service: CRUDService) -> AsyncSession:
    async with crud_service.database.session() as session:
        async with session.begin():
            yield session



@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(database: Database):
    async with database.session() as session:
        async with session.begin():
            await delete_all(session)
            await session.commit()
    
    async with database.session() as session:
        async with session.begin():
            await delete_dependent_tables(session)

            db_manga_site = MangaSite(
                name='manhuaren',
                url='https://www.manhuaren.com/')
            
            session.add(db_manga_site)
            user = User(email="taiharry108@gmail.com", hashed_password="12345")
            manga = Manga(name="Test Manga", url="https://example.com/manga")
            session.add(user)
            session.add(manga)
            
            await session.commit()
    async with database.session() as session:
        async with session.begin():
            title = "Test Title"
            page_urls = [f"https://example.com/{i}" for i in range(10)]
            logger.info(f'{manga.id=}')
            chapters = [Chapter(**{'title': title, 'page_url': page_url, 'manga_id':manga.id}) for page_url in page_urls]

            session.add_all(chapters)
            await session.commit()
    yield

@pytest.fixture
def manga_name() -> str:
    return "Test Manga"

@pytest.fixture
def manga_url() -> str:
    return "https://example.com"


@pytest.fixture
async def manga_site_id(crud_service: CRUDService, session: AsyncSession):
    site = MangaSiteEnum.ManHuaRen
    return await crud_service.get_id_by_attr(session, MangaSite, "name", site.value)    


async def test_get_item_by_attrs(crud_service: CRUDService, session: AsyncSession):
    site = MangaSiteEnum.ManHuaRen
    db_mangasite = await crud_service.get_item_by_attrs(session, MangaSite, name=site.value)
    assert db_mangasite.name == "manhuaren"


async def test_get_item_by_id(crud_service: CRUDService, session: AsyncSession):
    site = MangaSiteEnum.ManHuaRen
    db_mangasite = await crud_service.get_item_by_attrs(session, MangaSite, name=site.value)
    db_mangasite2 = await crud_service.get_item_by_id(session, MangaSite, db_mangasite.id)
    assert db_mangasite.id == db_mangasite2.id


async def test_get_item_by_id_not_exists(crud_service: CRUDService, session: AsyncSession):
    db_mangasite = await crud_service.get_item_by_id(session, MangaSite, 99999)
    assert db_mangasite is None

async def test_get_id_by_attr(crud_service: CRUDService, session: AsyncSession):
    site = MangaSiteEnum.ManHuaRen
    manga_site_id = await crud_service.get_id_by_attr(session, MangaSite, "name", site.value)
    assert manga_site_id > 0


async def test_get_items_by_attr(crud_service: CRUDService, session: AsyncSession):
    urls = ["https://www.manhuaren.com/"]
    db_mangas = await crud_service.get_items_by_attr(session, MangaSite, "url", urls)
    assert len(db_mangas) == 1
    assert db_mangas[0].url == urls[0]
    

async def test_create_manga(crud_service: CRUDService, manga_site_id: int, manga_name: str, manga_url: str, session: AsyncSession):
    db_manga = await crud_service.create_obj(session, Manga, name=manga_name,
                                       url=manga_url, manga_site_id=manga_site_id)    
    assert isinstance(db_manga, Manga)
    assert db_manga.name == manga_name
    assert db_manga.url == manga_url
    assert db_manga.manga_site_id == manga_site_id
    assert db_manga.id is not None


async def test_bulk_create_mangas(crud_service: CRUDService, manga_site_id: int, session: AsyncSession):
    mangas = [{
        "name": f"Test Manga {i}",
        "url": f"https://example.com/{i}",
        "manga_site_id": manga_site_id,
    } for i in range(15)]

    db_mangas = await crud_service.bulk_create_objs(session, Manga, mangas)

    assert len(db_mangas) == 15
    assert isinstance(db_mangas[0], Manga)
    for db_manga in db_mangas:
        assert db_manga.name.startswith("Test Manga")
        assert db_manga.url.startswith("https://example.com")
        assert db_manga.manga_site_id == manga_site_id


async def test_update_values(crud_service: CRUDService, manga_url: str, session: AsyncSession):
    db_manga = await crud_service.get_item_by_attr(session, Manga, "url", manga_url)
    manga_id = db_manga.id
    assert db_manga.thum_img is None
    thum_img = "test.png"
    result = await crud_service.update_object(session, Manga, manga_id, thum_img=thum_img)
    assert isinstance(result, Manga)
    assert result.thum_img == thum_img


async def test_update_values_failed_wrong_attr(crud_service: CRUDService, manga_url: str, session: AsyncSession):
    db_manga = await crud_service.get_item_by_attr(session, Manga, "url", manga_url)
    manga_id = db_manga.id
    thum_img = "test.png"
    result = await crud_service.update_object(session, Manga, manga_id, foo=thum_img)
    assert result is None


async def test_bulk_create_objs_with_unique_key(crud_service: CRUDService, manga_name: str, manga_url: str, session: AsyncSession):
    items = [{"name": manga_name, "url": manga_url}, {"name":manga_name, "url": manga_url + "another"}]

    db_items = await crud_service.bulk_create_objs_with_unique_key(session, Manga, items, "url")
    assert len(db_items) == 1
    assert db_items[0].url == manga_url + "another"


async def test_add_item_to_obj(crud_service: CRUDService, session: AsyncSession, manga_url: str):
    db_user = await crud_service.get_item_by_attr(session, User, "email", "taiharry108@gmail.com")
    db_manga = await crud_service.get_item_by_attr(session, Manga, "url", manga_url)

    db_updated_user = await crud_service.add_item_to_obj(session, User, Manga, db_user.id, db_manga.id, "fav_mangas")
    fav_manga = db_updated_user.fav_mangas[0]
    assert fav_manga.id == db_manga.id


async def test_add_item_to_obj_2nd(crud_service: CRUDService, session: AsyncSession, manga_url: str):
    db_user = await crud_service.get_item_by_attr(session, User, "email", "taiharry108@gmail.com")
    db_manga = await crud_service.get_item_by_attr(session, Manga, "url", manga_url)

    db_updated_user = await crud_service.add_item_to_obj(session, User, Manga, db_user.id, db_manga.id, "fav_mangas")
    assert db_updated_user is None


async def test_get_items_of_obj(crud_service: CRUDService, session: AsyncSession):
    db_user = await crud_service.get_item_by_attr(session, User, "email", "taiharry108@gmail.com")
    db_mangas = await crud_service.get_items_of_obj(session, User, db_user.id, "fav_mangas")
    assert len(db_mangas) != 0


async def test_remove_item_from_obj(crud_service: CRUDService, session: AsyncSession, manga_url: str):
    db_user = await crud_service.get_item_by_attr(session, User, "email", "taiharry108@gmail.com")
    db_manga = await crud_service.get_item_by_attr(session, Manga, "url", manga_url)

    db_updated_user = await crud_service.remove_item_from_obj(session, User, Manga, db_user.id, db_manga.id, "fav_mangas")
    assert not db_manga in db_updated_user.fav_mangas


async def test_get_items_by_same_attr(crud_service: CRUDService, session: AsyncSession):
    manga_id = await crud_service.get_id_by_attr(session, Manga, "url", "https://example.com/manga")
    db_chapters = await crud_service.get_items_by_same_attr(session, Chapter, 'manga_id', manga_id)
    assert len(db_chapters) == 10


async def test_get_items_by_ids(crud_service: CRUDService, session: AsyncSession):
    manga_id = await crud_service.get_id_by_attr(session, Manga, "url", "https://example.com/manga")
    db_chapters = await crud_service.get_items_by_same_attr(session, Chapter, 'manga_id', manga_id)
    chap_ids = [chap.id for chap in db_chapters]
    db_chapters2 = await crud_service.get_items_by_ids(session, Chapter, chap_ids, False)
    assert len(db_chapters) == len(db_chapters2)

