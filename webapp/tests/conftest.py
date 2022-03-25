import pytest
import asyncio
from webapp.containers import Container
from dependency_injector import providers
from webapp.services.database import Database


@pytest.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    c = Container()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="module")
async def database():
    container = Container()
    container.db.override(providers.Singleton(
        Database, db_url="postgresql+asyncpg://taiharry:123456@postgres/testAcDB"))
    db = container.db()
    await db.create_database()
    return db
