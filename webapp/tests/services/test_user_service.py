import pytest
from dependency_injector.wiring import inject, Provide
from dependency_injector import providers
from webapp.containers import Container
from webapp.models.manga_index_type_enum import MangaIndexTypeEnum
from webapp.models.user import User
from webapp.models.manga import Manga

from webapp.models.db_models import User as DBUser, Manga as DBManga, History as DBHistory, Chapter as DBChapter
from webapp.services.crud_service import CRUDService

from webapp.services.database import Database

from webapp.services.secruity_service import SecurityService

from logging import getLogger
from logging import config

from webapp.services.user_service import UserService
from webapp.tests.utils import delete_all
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
def crud_service(database: Database, crud_service: CRUDService = Provide[Container.crud_service]) -> CRUDService:
    crud_service.database = database
    return crud_service


@pytest.fixture
@inject
def user_service(user_service: providers.Singleton[UserService] = Provide[Container.user_service]) -> UserService:
    return user_service


@pytest.fixture
@inject
def security_service(security_service: providers.Singleton[SecurityService] = Provide[Container.security_service]) -> SecurityService:
    return security_service


@pytest.fixture(scope="module")
def manga() -> Manga:
    return Manga(name="Test manga 1", url="https://example.com")


@pytest.fixture(scope="module")
def username() -> str: return "test_user1"


@pytest.fixture(scope="module")
def password() -> str: return "123456"


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(database: Database, username: str, password: str, crud_service: CRUDService, manga: Manga):
    with database.session() as session:
        delete_all(session)
    crud_service.create_obj(DBUser, email=username,
                            hashed_password=password)
    crud_service.create_obj(DBManga, name=manga.name, url=manga.url)
    yield


@pytest.fixture
async def manga_id(crud_service: CRUDService, manga: Manga) -> int:
    return crud_service.get_item_by_attr(DBManga, "name", manga.name).id


async def test_get_user(user_service: UserService, username: str):
    db_user = user_service.get_user(username)
    if db_user is None:
        assert False

    assert db_user.username == username


async def test_create_user(user_service: UserService, security_service: SecurityService, password: str):
    username = "test_user2"
    db_user = user_service.create_user(username, password)
    assert db_user.email == username
    assert security_service.verify_password(password, db_user.hashed_password)


async def test_create_user(user_service: UserService, username: str, password: str):
    db_user = user_service.create_user(username, password)
    assert db_user is None


async def test_add_fav(user_service: UserService, crud_service: CRUDService, username: str, manga_id: int):
    db_user = crud_service.get_item_by_attr(DBUser, "email", username)
    user_id = db_user.id
    result = user_service.add_fav(manga_id, user_id)

    assert result

    fav_mangas = crud_service.get_items_of_obj(DBUser, user_id, "fav_mangas")
    assert len(list(filter(lambda m: m.id, fav_mangas))) != 0


async def test_add_fav_twice(user_service: UserService, crud_service: CRUDService, username: str, manga_id: int):
    db_user = crud_service.get_item_by_attr(DBUser, "email", username)
    user_id = db_user.id
    assert not user_service.add_fav(manga_id, user_id)


async def test_add_history(user_service: UserService, crud_service: CRUDService, username: str, manga_id: int):
    db_user = crud_service.get_item_by_attr(DBUser, "email", username)
    user_id = db_user.id
    assert user_service.add_history(manga_id, user_id)

    db_history = crud_service.get_item_by_attrs(
        DBHistory, manga_id=manga_id, user_id=user_id)
    assert db_history.manga_id == manga_id
    assert db_history.user_id == user_id
    assert db_history.last_added


async def test_add_history_twice(user_service: UserService, crud_service: CRUDService, username: str, manga_id: int):
    db_user = crud_service.get_item_by_attr(DBUser, "email", username)
    user_id = db_user.id
    assert user_service.add_history(manga_id, user_id)
    assert user_service.add_history(manga_id, user_id)


async def test_get_fav(crud_service: CRUDService, user_service: UserService, username: str, manga_id: int):
    db_user = crud_service.get_item_by_attr(DBUser, "email", username)
    user_id = db_user.id
    user_service.add_fav(manga_id, user_id)

    fav_mangas = user_service.get_fav(user_id)

    assert len(fav_mangas) == 1
    assert fav_mangas[0].id == manga_id


async def test_get_history(crud_service: CRUDService, user_service: UserService, username: str, manga_id: int):
    db_user = crud_service.get_item_by_attr(DBUser, "email", username)
    user_id = db_user.id
    user_service.add_history(manga_id, user_id)

    history_mangas = user_service.get_history(user_id)

    assert len(history_mangas) == 1
    assert history_mangas[0].manga_id == manga_id


async def test_remove_fav(crud_service: CRUDService, user_service: UserService, username: str, manga_id: int):
    db_user = crud_service.get_item_by_attr(DBUser, "email", username)
    user_id = db_user.id
    user_service.remove_fav(manga_id, user_id)

    fav_mangas = user_service.get_fav(user_id)

    filtered_mangas = [manga for manga in fav_mangas if manga.id == manga_id]
    assert len(filtered_mangas) == 0


async def test_remove_history(crud_service: CRUDService, user_service: UserService, username: str, manga_id: int):
    db_user = crud_service.get_item_by_attr(DBUser, "email", username)
    user_id = db_user.id
    user_service.remove_history(manga_id, user_id)

    history_mangas = user_service.get_history(user_id)
    filtered_mangas = [
        manga for manga in history_mangas if manga.id == manga_id]
    assert len(filtered_mangas) == 0


async def test_update_history(crud_service: CRUDService, user_service: UserService, username: str, manga_id: int):
    db_chapter = crud_service.create_obj(DBChapter, title="Test title", page_url="https://example.com",
                            manga_id=manga_id, type=MangaIndexTypeEnum.CHAPTER.value)
    db_user = crud_service.get_item_by_attr(DBUser, "email", username)    
    user_id = db_user.id

    assert user_service.add_history(manga_id, user_id)
    assert user_service.update_history(db_chapter.id, user_id)
    db_history = crud_service.get_item_by_attrs(DBHistory, manga_id=manga_id, chaper_id=db_chapter.id, user_id=user_id)
    assert db_history.chaper_id == db_chapter.id



