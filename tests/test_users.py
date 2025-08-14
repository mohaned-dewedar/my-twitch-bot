import asyncio
import pytest
import pytest_asyncio
from db.database import Database
from db.users import get_or_create_user

@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture()
async def db(event_loop):
    await Database.init("postgresql://trivia:trivia-password@localhost/trivia_test")

    # Clean DB before each test
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE users, channels, sessions, attempts RESTART IDENTITY CASCADE")

    yield
    await Database.close()

@pytest.mark.asyncio
async def test_get_or_create_user(db):  # depends on db fixture
    username = "TestUser123"
    user_id_1 = await get_or_create_user(username)
    assert user_id_1 is not None

    user_id_2 = await get_or_create_user(username)
    assert user_id_1 == user_id_2
