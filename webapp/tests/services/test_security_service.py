import pytest
from dependency_injector.wiring import inject, Provide
from dependency_injector import providers
from webapp.containers import Container
from webapp.models.db_models import User
from webapp.services.database import Database

from webapp.services.secruity_service import SecurityService
from jose import JWTError, jwt

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


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(database: Database,
                                     user_service: UserService,
                                     username: str, password: str):
    with database.session() as session:
        delete_all(session)
        user_service.create_user(username, password)
    yield


async def test_verify_password(security_service: SecurityService, password: str):
    hashed_password = security_service.hash_password(password)
    hashed_password2 = security_service.hash_password(password)
    logger.info(f"{password=},{hashed_password=},{hashed_password2=}")
    assert security_service.verify_password(password, hashed_password)
    assert security_service.verify_password(password, hashed_password2)


async def test_verify_password_failed(security_service: SecurityService, password: str):
    assert not security_service.verify_password(password, "12345")


async def test_authenticate_user_not_exists(user_service: UserService, security_service: SecurityService):
    db_user = user_service.get_user("abc")
    user = security_service.authenticate_user(db_user, "123456")
    assert user == False


async def test_authenticate_user_wrong_pw(user_service: UserService, security_service: SecurityService, username: str):
    db_user = user_service.get_user(username)
    user = security_service.authenticate_user(db_user, "123a45")
    assert user == False


async def test_authenticate_user(user_service: UserService, security_service: SecurityService, username: str, password: str):
    db_user = user_service.get_user(username)
    user = security_service.authenticate_user(db_user, password)
    assert user == db_user


async def test_create_access_token(security_service: SecurityService, username: str):
    data = {"sub": username}
    token = security_service.create_access_token(data)
    decoded_data = jwt.decode(token, security_service.secret_key, algorithms=[
                              security_service.algorithm])
    assert decoded_data["sub"] == data["sub"]


async def test_decode_access_token(security_service: SecurityService, username: str):
    data = {"sub": username}
    token = security_service.create_access_token(data)
    decoded_data = security_service.decode_access_token(token)
    assert decoded_data["sub"] == data["sub"]
