import pytest
from dependency_injector.wiring import inject, Provide
from dependency_injector import providers
from webapp.containers import Container
from webapp.models.user import User
from webapp.models.manga import Manga

from webapp.models.db_models import User as DBUser, Manga as DBManga, History as DBHistory, Chapter as DBChapter
from webapp.services.crud_service import CRUDService
from webapp.services.database import Database
from webapp.services.secruity_service import SecurityService
from sqlalchemy.ext.asyncio import AsyncSession

from logging import getLogger
from logging import config

from webapp.services.user_service import UserService
from webapp.tests.utils import delete_all, delete_dependent_tables
config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = getLogger(__name__)


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
def chapter_url() -> str:
    return "https://example.com/chap"


@pytest.fixture(scope="module")
def username() -> str: return "test_user1"


@pytest.fixture(scope="module")
def password() -> str: return "123456"


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(database: Database, username: str, password: str, crud_service: CRUDService, manga: Manga, chapter_url: str):
    async with database.session() as session:
        async with session.begin():
            await delete_all(session)
            await session.commit()

    async with database.session() as session:
        async with session.begin():
            await delete_dependent_tables(session)
            session.add(DBUser(email=username, hashed_password=password))
            db_manga = DBManga(name=manga.name, url=manga.url)
            session.add(db_manga)
            await session.commit()
    
    async with database.session() as session:
        async with session.begin():
            session.add(DBChapter(title="Test title",
                        page_url=chapter_url,
                        manga_id=db_manga.id))
            await session.commit()

    yield


@pytest.fixture
async def session(crud_service: CRUDService) -> AsyncSession:
    async with crud_service.database.session() as session:
        async with session.begin():
            yield session


@pytest.fixture
async def manga_id(crud_service: CRUDService, manga: Manga, session: AsyncSession) -> int:
    return await crud_service.get_id_by_attr(session, DBManga, "name", manga.name)


@pytest.fixture
async def chapter_id(crud_service: CRUDService, chapter_url: str, session: AsyncSession) -> int:
    return await crud_service.get_id_by_attr(session, DBChapter, "page_url", chapter_url)


@pytest.fixture
async def db_user(crud_service: CRUDService, session: AsyncSession, username: str) -> DBUser:
    return await crud_service.get_item_by_attr(session, DBUser, "email", username)


async def test_get_user(user_service: UserService, username: str, session: AsyncSession):
    db_user = await user_service.get_user(session, username)
    if db_user is None:
        assert False

    assert db_user.username == username


async def test_create_user(user_service: UserService, security_service: SecurityService, password: str, session: AsyncSession):
    username = "test_user2"
    db_user = await user_service.create_user(session, username, password)
    assert db_user.email == username
    assert security_service.verify_password(password, db_user.hashed_password)


async def test_create_user_twice(user_service: UserService, username: str, password: str, session: AsyncSession):
    db_user = await user_service.create_user(session, username, password)
    assert db_user is None


async def test_add_fav(user_service: UserService,
                       manga_id: int,
                       session: AsyncSession,
                       db_user: DBUser):
    user_id = db_user.id
    result = await user_service.add_fav(session, manga_id, user_id)

    filtered_mangas = [
        manga for manga in result.fav_mangas if manga.id == manga_id]

    assert len(list(filtered_mangas)) == 1


async def test_add_fav_twice(user_service: UserService,
                             manga_id: int,
                             session: AsyncSession,
                             db_user: DBUser):
    user_id = db_user.id
    assert not await user_service.add_fav(session, manga_id, user_id)


async def test_add_history(user_service: UserService,
                           manga_id: int,
                           session: AsyncSession,
                           db_user: DBUser):
    user_id = db_user.id
    db_history = await user_service.add_history(session, manga_id, user_id)

    assert db_history.manga_id == manga_id
    assert db_history.user_id == user_id
    assert db_history.last_added


async def test_add_history_twice(user_service: UserService,
                                 manga_id: int,
                                 session: AsyncSession,
                                 db_user: DBUser):
    user_id = db_user.id
    assert await user_service.add_history(session, manga_id, user_id)


async def test_update_history(user_service: UserService,
                              session: AsyncSession,
                              db_user: DBUser,
                              chapter_id: int):
    user_id = db_user.id

    assert await user_service.update_history(session, chapter_id, user_id)


async def test_get_history(user_service: UserService,
                           manga_id: int,
                           session: AsyncSession,
                           db_user: DBUser):
    user_id = db_user.id
    history_mangas = await user_service.get_history(session, user_id)

    assert len(history_mangas) == 1
    assert history_mangas[0].manga_id == manga_id


async def test_remove_fav(user_service: UserService,
                          manga_id: int,
                          session: AsyncSession,
                          db_user: DBUser):
    user_id = db_user.id
    db_user = await user_service.remove_fav(session, manga_id, user_id)

    fav_mangas = db_user.fav_mangas

    filtered_mangas = [manga for manga in fav_mangas if manga.id == manga_id]
    assert len(filtered_mangas) == 0


async def test_get_latest_chap(user_service: UserService, manga_id: int, session: AsyncSession, db_user: DBUser, chapter_id: int):
    user_id = db_user.id
    latest_chapter = await user_service.get_latest_chap(session, user_id, manga_id)
    assert chapter_id == latest_chapter.id
    logger.info(chapter_id)


async def test_remove_history(user_service: UserService,
                              manga_id: int,
                              session: AsyncSession,
                              db_user: DBUser):
    user_id = db_user.id
    assert await user_service.remove_history(session, manga_id, user_id)

