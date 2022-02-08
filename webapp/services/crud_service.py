import dataclasses
from logging import getLogger
from typing import List
from webapp.services.async_service import AsyncService
from webapp.services.database import Database

from sqlalchemy.orm.decl_api import DeclarativeMeta

from typing import List, TypeVar, Type

T = TypeVar("T")

logger = getLogger(__name__)


@dataclasses.dataclass
class CRUDService:
    database: Database

    def get_item_by_id(self, orm_obj_type: Type[T], id: int) -> T:
        logger.info("here3")
        query_result = self.get_items_by_ids(orm_obj_type, [id])
        if query_result:
            return query_result[0]
        return None

    def get_items_by_ids(self, orm_obj_type: Type[T], ids: List[int]) -> List[T]:
        with self.database.session() as session:
            result = session.query(orm_obj_type).filter(
                orm_obj_type.id.in_(ids)).all()
            if not result:
                return []
            return [next(s for s in result if s.id == id) for id in ids]
