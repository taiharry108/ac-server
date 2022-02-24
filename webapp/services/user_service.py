import dataclasses
from datetime import datetime
from typing import List, Optional
from webapp.models.user import UserInDB
from webapp.services.crud_service import CRUDService
from webapp.models.db_models import History as DBHistory, User as DBUser, Manga as DBManga, Chapter as DBChapter
from webapp.services.secruity_service import SecurityService
from logging import getLogger


logger = getLogger(__name__)


@dataclasses.dataclass
class UserService:
    crud_service: CRUDService
    security_service: SecurityService

    def add_fav(self, manga_id: int, user_id: int) -> bool:
        return self.crud_service.add_item_to_obj(DBUser, DBManga, user_id, manga_id, "fav_mangas")

    def remove_fav(self, manga_id: int, user_id: int) -> bool:
        return self.crud_service.remove_item_from_obj(DBUser, DBManga, user_id, manga_id, "fav_mangas")

    def get_fav(self, user_id: int) -> List[DBManga]:
        return self.crud_service.get_attr_of_item_by_id(DBUser, user_id, "fav_mangas")

    def get_history(self, user_id: int) -> List[DBHistory]:
        return self.crud_service.get_attr_of_item_by_id(DBUser, user_id, "history_mangas")
    
    def get_latest_chap(self, user_id: int, manga_id: int) -> Optional[DBChapter]:
        db_history = self.crud_service.get_item_by_attrs(
            DBHistory, manga_id=manga_id, user_id=user_id)
        if db_history is None:
            return None
        return self.crud_service.get_item_by_id(DBChapter, db_history.chaper_id)

    def remove_history(self, manga_id: int, user_id: int) -> bool:
        def work(session, db_user, db_manga):
            db_hist = session.query(DBHistory).filter(
                DBHistory.manga_id == manga_id, DBHistory.user_id == user_id).first()
            if db_hist is not None:
                session.delete(db_hist)
                session.commit()
            return True

        return self.crud_service.item_obj_iteraction(None, DBUser, DBManga, user_id, manga_id, work)
    
    def update_history(self, chap_id: int, user_id: int):
        manga_id = self.crud_service.get_item_by_id(DBChapter, chap_id).manga_id
        def work(session, db_user, db_manga):
            db_hist: DBHistory = session.query(DBHistory).filter(
                DBHistory.manga_id == manga_id, DBHistory.user_id == user_id).first()
            if db_hist is not None:
                db_hist.chaper_id = chap_id
                session.commit()
                return True
            else:
                return False
        
        return self.crud_service.item_obj_iteraction(None, DBUser, DBManga, user_id, manga_id, work)

    def add_history(self, manga_id: int, user_id: int) -> bool:
        def work(session, db_user, db_manga):
            db_hist = session.query(DBHistory).filter(
                DBHistory.manga_id == manga_id, DBHistory.user_id == user_id).first()
            if db_hist is None:
                logger.info(f"history not exists for {user_id=},{manga_id=}")
                DBHistory(last_added=datetime.now(),
                          user=db_user, manga=db_manga)
            else:
                db_hist.last_added = datetime.now()
            session.commit()
            return True

        return self.crud_service.item_obj_iteraction(None, DBUser, DBManga, user_id, manga_id, work)

    def get_user(self, username: str) -> Optional[UserInDB]:
        db_user = self.crud_service.get_item_by_attr(DBUser, "email", username)
        if db_user is None:
            return None
        return UserInDB(username=db_user.email,
                        is_active=db_user.is_active,
                        hashed_password=db_user.hashed_password)

    def get_user_id(self, username: str) -> int:
        return self.crud_service.get_id_by_attr(DBUser, "email", username)

    def create_user(self, username: str, password: str) -> Optional[DBUser]:
        if self.get_user(username):
            return None
        hashed_password = self.security_service.hash_password(password)
        db_user = self.crud_service.create_obj(
            DBUser, email=username, hashed_password=hashed_password)
        return db_user
