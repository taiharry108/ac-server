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


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(database: Database):
    with database.session() as session:
        session.query(User).delete()
        session.commit()
    yield


@pytest.fixture
@inject
def security_service(security_service: providers.Singleton[SecurityService] = Provide[Container.security_service]) -> SecurityService:
    return security_service


@pytest.fixture
def username() -> str: return "test_user1"


@pytest.fixture
def password() -> str: return "123456"


async def test_verify_password(security_service: SecurityService, password: str):
    hashed_password = security_service.hash_password(password)
    hashed_password2 = security_service.hash_password(password)
    logger.info(f"{password=},{hashed_password=},{hashed_password2=}")
    assert security_service.verify_password(password, hashed_password)
    assert security_service.verify_password(password, hashed_password2)


async def test_create_user(security_service: SecurityService, username: str, password: str):
    db_user = security_service.create_user(username, password)
    assert db_user.email == username
    assert security_service.verify_password(password, db_user.hashed_password)

async def test_create_user_twice(security_service: SecurityService, username: str, password: str):
    security_service.create_user(username, password)
    db_user2 = security_service.create_user(username, password)
    assert db_user2 is None
# assert db_user.email == username
    # assert security_service.verify_password(password, db_user.hashed_password)


async def test_get_user(security_service: SecurityService, username: str):
    db_user = security_service.get_user(username)
    if db_user is None:
        assert False

    assert db_user.username == username


async def test_authenticate_user(security_service: SecurityService, username: str, password):
    user = security_service.authenticate_user(username, password)
    assert user
    assert user.username == username


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
