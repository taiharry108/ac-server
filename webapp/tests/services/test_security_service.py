import pytest
from dependency_injector.wiring import inject, Provide
from dependency_injector import providers
from webapp.containers import Container
from webapp.models.db_models import User
from webapp.services.crud_service import CRUDService
from webapp.services.database import Database

from webapp.services.secruity_service import SecurityService
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from logging import getLogger
from logging import config
from webapp.services.user_service import UserService

from webapp.tests.utils import delete_all, delete_dependent_tables
config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = getLogger(__name__)


@pytest.fixture(scope="module")
@inject
def user_service(user_service: providers.Singleton[UserService] = Provide[Container.user_service]) -> UserService:
    return user_service


@pytest.fixture(scope="module")
def username() -> str: return "test_user1"


@pytest.fixture(scope="module")
def password() -> str: return "123456"


@pytest.fixture(scope="module")
@inject
def security_service(security_service: providers.Singleton[SecurityService] = Provide[Container.security_service]) -> SecurityService:
    return security_service


@pytest.fixture(scope="module")
@inject
def crud_service(database: Database, crud_service: CRUDService = Provide[Container.crud_service]) -> CRUDService:
    crud_service.database = database
    return crud_service


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(database: Database, username: str, password: str):
    async with database.session() as session:
        async with session.begin():
            await delete_all(session)
            await session.commit()

    async with database.session() as session:
        async with session.begin():
            await delete_dependent_tables(session)
            session.add(User(email=username, hashed_password=password))
            await session.commit()

    yield


@pytest.fixture
async def session(crud_service: CRUDService) -> AsyncSession:
    async with crud_service.database.session() as session:
        async with session.begin():
            yield session


async def test_verify_password(security_service: SecurityService, password: str):
    hashed_password = security_service.hash_password(password)
    hashed_password2 = security_service.hash_password(password)
    logger.info(f"{password=},{hashed_password=},{hashed_password2=}")
    assert security_service.verify_password(password, hashed_password)
    assert security_service.verify_password(password, hashed_password2)


async def test_verify_password_failed(security_service: SecurityService, password: str):
    assert not security_service.verify_password(password, "12345")


async def test_authenticate_user_not_exists(user_service: UserService, security_service: SecurityService, session: AsyncSession):
    db_user = await user_service.get_user(session, "abc")
    user = security_service.authenticate_user(db_user, "123456")
    assert user == False


async def test_authenticate_user_wrong_pw(user_service: UserService, security_service: SecurityService, username: str, session: AsyncSession):
    db_user = await user_service.get_user(session, username)
    user = security_service.authenticate_user(db_user, "123a45")
    assert user == False


async def test_authenticate_user(user_service: UserService, security_service: SecurityService, username: str, password: str, session: AsyncSession):
    db_user = await user_service.get_user(session, username)
    db_user.hashed_password = security_service.hash_password(db_user.hashed_password)
    user = security_service.authenticate_user(db_user, password)
    assert user == db_user


async def test_create_access_token(security_service: SecurityService, username: str):
    data = {"sub": username}
    token = security_service.create_access_token(data)
    decoded_data = jwt.decode(token, security_service.secret_key, algorithms=[
                              security_service.algorithm])
    assert decoded_data["sub"] == data["sub"]


# async def test_decode_access_token(security_service: SecurityService, username: str):
#     data = {"sub": username}
#     token = security_service.create_access_token(data)
#     decoded_data = security_service.decode_access_token(token)
#     assert decoded_data["sub"] == data["sub"]
