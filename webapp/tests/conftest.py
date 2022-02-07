import pytest
import asyncio

from webapp.containers import Container


@pytest.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    c = Container()
    yield loop
    loop.close()
