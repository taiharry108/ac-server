import dataclasses
from datetime import datetime
from typing import List, Optional

from webapp.models.user import UserInDB
from webapp.services.crud_service import CRUDService
from webapp.models.db_models import History as DBHistory, User as DBUser, Manga as DBManga, Chapter as DBChapter
from webapp.services.secruity_service import SecurityService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from sqlalchemy import select
from logging import getLogger


logger = getLogger(__name__)


@dataclasses.dataclass
class UserService:
    crud_service: CRUDService
    security_service: SecurityService

    async def add_fav(self, session: AsyncSession,  manga_id: int, user_id: int) -> DBUser:
        return await self.crud_service.add_item_to_obj(session, DBUser, DBManga, user_id, manga_id, "fav_mangas")

    async def remove_fav(self, session: AsyncSession,  manga_id: int, user_id: int) -> DBUser:
        return await self.crud_service.remove_item_from_obj(session, DBUser, DBManga, user_id, manga_id, "fav_mangas")

    async def get_fav(self, session: AsyncSession,  user_id: int) -> List[DBManga]:
        return await self.crud_service.get_attr_of_item_by_id(session, DBUser, user_id, "fav_mangas", "fav_mangas")

    async def get_history(self, session: AsyncSession,  user_id: int) -> List[DBHistory]:
        return await self.crud_service.get_attr_of_item_by_id(session, DBUser, user_id, "history_mangas", "history_mangas")

    async def get_latest_chap(self, session: AsyncSession,  user_id: int, manga_id: int) -> Optional[DBChapter]:
        db_history = await self.crud_service.get_item_by_attrs(session,
                                                         DBHistory,
                                                         manga_id=manga_id,
                                                         user_id=user_id)
        if db_history is None:
            return None
        return await self.crud_service.get_item_by_id(session, DBChapter, db_history.chaper_id)

    async def remove_history(self, session: AsyncSession,  manga_id: int, user_id: int) -> bool:
        async def work(session, db_user, db_manga):
            q = select(DBHistory).where(DBHistory.manga_id ==
                                        manga_id).where(DBHistory.user_id == user_id)
            db_hist = await session.execute(q)
            try:
                db_hist = db_hist.one()[0]
            except NoResultFound:
                db_hist = None
            if db_hist is not None:
                await session.delete(db_hist)
                await session.commit()
                return True
            else:
                return False

        return await self.crud_service.item_obj_iteraction(session, DBUser, DBManga, user_id, manga_id, work)

    async def update_history(self, session: AsyncSession, chap_id: int, user_id: int):
        manga_id = await self.crud_service.get_attr_of_item_by_id(session, DBChapter, chap_id, "manga_id")
        async def work(session, db_user, db_manga):
            q = select(DBHistory).where(DBHistory.manga_id ==
                                        manga_id).where(DBHistory.user_id == user_id)
            db_hist = await session.execute(q)
            try:
                db_hist = db_hist.one()[0]
            except NoResultFound:
                db_hist = None
            if db_hist is not None:
                db_hist.chaper_id = chap_id
                await session.commit()
                return True
            else:
                return False

        return await self.crud_service.item_obj_iteraction(session, DBUser, DBManga, user_id, manga_id, work)

    async def add_history(self, session: AsyncSession,  manga_id: int, user_id: int) -> DBHistory:
        async def work(session, db_user, db_manga):
            q = select(DBHistory).where(DBHistory.manga_id ==
                                        manga_id).where(DBHistory.user_id == user_id)
            db_hist = await session.execute(q)
            try:
                db_hist = db_hist.one()[0]
            except NoResultFound:
                db_hist = None
            if db_hist is None:
                logger.info(f"history not exists for {user_id=},{manga_id=}")
                db_hist = DBHistory(last_added=datetime.now(),
                                    user=db_user, manga=db_manga)
                session.add(db_hist)
            else:
                db_hist.last_added = datetime.now()
            await session.commit()
            return db_hist

        return await self.crud_service.item_obj_iteraction(session, DBUser, DBManga, user_id, manga_id, work)

    async def get_user(self, session: AsyncSession, username: str) -> Optional[UserInDB]:
        db_user = await self.crud_service.get_item_by_attr(session, DBUser, "email", username)
        if db_user is None:
            return None
        return UserInDB(username=db_user.email,
                        is_active=db_user.is_active,
                        hashed_password=db_user.hashed_password)

    async def get_user_id(self, session: AsyncSession,  username: str) -> int:
        return await self.crud_service.get_id_by_attr(session, DBUser, "email", username)

    async def create_user(self, session: AsyncSession,  username: str, password: str) -> Optional[DBUser]:
        if await self.get_user(session, username):
            return None
        hashed_password = self.security_service.hash_password(password)
        db_user = await self.crud_service.create_obj(session,
                                                     DBUser, email=username, hashed_password=hashed_password)
        return db_user
