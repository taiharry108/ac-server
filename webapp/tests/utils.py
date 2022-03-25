from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from webapp.models.db_models import User, History, Manga, MangaSite, Chapter, Page
from sqlalchemy.orm import selectinload


async def delete_all(session: AsyncSession) -> bool:
    await session.execute(delete(History))
    await session.execute(delete(Page))
    await session.execute(delete(Chapter))
    for user in (await session.execute(select(User).options(selectinload(User.fav_mangas)))).all():
        user = user[0]
        user.fav_mangas = []
        user.history = []
    return True

async def delete_dependent_tables(session: AsyncSession) -> bool:
    await session.execute(delete(Manga))
    await session.execute(delete(User))
    await session.execute(delete(MangaSite))
    return True
