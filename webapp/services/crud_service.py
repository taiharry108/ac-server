import dataclasses
from logging import getLogger
from typing import Any, Dict, List
from webapp.services.database import Database

from typing import List, TypeVar, Type

T = TypeVar("T")

logger = getLogger(__name__)


def rearrange_items(og_items, shuffled_items, unique_key, og_is_value=False):
    if og_is_value:
        idx_dict = {item: idx for idx,
                    item in enumerate(og_items)}
    else:
        idx_dict = {getattr(item, unique_key): idx for idx,
                    item in enumerate(og_items)}

    new_list = [None for _ in enumerate(og_items)]

    for item in shuffled_items:
        new_list[idx_dict[getattr(item, unique_key)]] = item
    
    new_list = [item for item in new_list if item is not None]

    return new_list


@dataclasses.dataclass
class CRUDService:
    database: Database

    def get_item_by_id(self, orm_obj_type: Type[T], id: int) -> T:
        """Get item by id, return None if not exists"""
        query_result = self.get_items_by_ids(orm_obj_type, [id])
        if query_result:
            return query_result[0]
        return None

    def get_items_by_ids(self, orm_obj_type: Type[T], ids: List[int]) -> List[T]:
        """Get item by id, return empty list if not exists"""
        with self.database.session() as session:
            result = session.query(orm_obj_type).filter(
                orm_obj_type.id.in_(ids)).all()
            if not result:
                return []
            return rearrange_items(ids, result, "id", True)
            # return [next(s for s in result if s.id == id) for id in ids]

    def get_item_by_attr(self, orm_obj_type: Type[T], attr_name: str, attr_value: Any) -> T:
        with self.database.session() as session:
            return session.query(orm_obj_type).filter(getattr(orm_obj_type, attr_name) == attr_value).first()

    def get_id_by_attr(self, orm_obj_type: Type[T], attr_name: str, attr_value: Any) -> int:
        return self.get_item_by_attr(orm_obj_type, attr_name, attr_value).id

    def get_items_by_attrs(self, orm_obj_type: Type[T], attr_name: str, attr_values: List[Any]) -> List[T]:
        with self.database.session() as session:            
            db_items = session.query(orm_obj_type).filter(
                getattr(orm_obj_type, attr_name).in_(attr_values)).all()

            db_items = rearrange_items(attr_values, db_items, attr_name, True)
            logger.info(len(db_items))
            return db_items

    def get_items_by_same_attr(self, orm_obj_type: Type[T], attr_name: str, attr_value: Any, sort_key: str = None) -> List[T]:
        with self.database.session() as session:
            db_filter = session.query(orm_obj_type).filter(
                getattr(orm_obj_type, attr_name) == attr_value)

            if sort_key is not None:
                db_items = db_filter.order_by(
                    getattr(orm_obj_type, sort_key)).all()
            else:
                db_items = db_filter.all()

            return db_items

    def create_obj(self, orm_obj_type: Type[T], **kwargs) -> T:
        with self.database.session() as session:
            db_manga = orm_obj_type(**kwargs)
            session.add(db_manga)
            session.commit()
            session.refresh(db_manga)
            return db_manga

    def bulk_create_objs(self, orm_obj_type: Type[T], items: List[Dict]) -> bool:
        logger.info(f"Going to bulk create {len(items)} items")
        result = [orm_obj_type(**item) for item in items]
        with self.database.session() as session:
            session.bulk_save_objects(result)
            session.commit()
        return True

    def bulk_create_objs_with_unique_key(self, orm_obj_type: Type[T], items: List[Dict], unique_key: str) -> bool:
        db_items = self.get_items_by_attrs(
            orm_obj_type, unique_key, [item[unique_key] for item in items])

        existing_unique_keys = set(getattr(item, unique_key)
                                   for item in db_items)

        # filter out items that already exist
        items = [item for item in items if not item[unique_key]
                 in existing_unique_keys]
        return self.bulk_create_objs(orm_obj_type, items)
