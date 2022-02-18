import dataclasses
from logging import getLogger
from typing import Any, Callable, Dict, List
from webapp.models.db_models import User
from webapp.services.database import Database

from typing import List, TypeVar, Type
from functools import wraps
from sqlalchemy.orm import Session

T = TypeVar("T")

logger = getLogger(__name__)


def add_session(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        with self.database.session() as session:
            return func(self, session, *args, **kwargs)
    return wrapped


def rearrange_items(og_items, shuffled_items, unique_key, og_is_value=False, keep_none=False):
    if og_is_value:
        idx_dict = {item: idx for idx,
                    item in enumerate(og_items)}
    else:
        idx_dict = {getattr(item, unique_key): idx for idx,
                    item in enumerate(og_items)}

    new_list = [None for _ in enumerate(og_items)]

    for item in shuffled_items:
        new_list[idx_dict[getattr(item, unique_key)]] = item

    if not keep_none:
        new_list = [item for item in new_list if item is not None]

    return new_list


@dataclasses.dataclass
class CRUDService:
    database: Database

    @add_session
    def get_item_by_id(self, session: Session, orm_obj_type: Type[T], id: int) -> T:
        """Get item by id, return None if not exists"""
        query_result = session.query(orm_obj_type).get(id)
        if not query_result:
            return None
        return query_result

    @add_session
    def get_attr_of_item_by_id(self, session: Session, orm_obj_type: Type[T], id: int, attr_name: str):
        return getattr(session.query(orm_obj_type).get(id), attr_name)

    @add_session
    def get_items_by_ids(self, session: Session, orm_obj_type: Type[T], ids: List[int], keep_none=False) -> List[T]:
        """Get item by id, return empty list if not exists"""
        result = session.query(orm_obj_type).filter(
            orm_obj_type.id.in_(ids)).all()
        return rearrange_items(ids, result, "id", True, keep_none=keep_none)

    def get_item_by_attr(self, orm_obj_type: Type[T], attr_name: str, attr_value: Any) -> T:
        return self.get_item_by_attrs(orm_obj_type, **{attr_name: attr_value})

    @add_session
    def get_item_by_attrs(self, session: Session, orm_obj_type: Type[T], **kwargs) -> T:
        q = session.query(orm_obj_type)

        filter_query = [getattr(orm_obj_type, attr_name) == attr_value
                        for attr_name, attr_value in kwargs.items()]
        return q.filter(*filter_query).first()

    def get_id_by_attr(self, orm_obj_type: Type[T], attr_name: str, attr_value: Any) -> int:
        return self.get_item_by_attr(orm_obj_type, attr_name, attr_value).id

    @add_session
    def get_items_by_attr(self, session: Session, orm_obj_type: Type[T], attr_name: str, attr_values: List[Any]) -> List[T]:
        db_items = session.query(orm_obj_type).filter(
            getattr(orm_obj_type, attr_name).in_(attr_values)).all()

        db_items = rearrange_items(attr_values, db_items, attr_name, True)
        return db_items

    @add_session
    def get_items_by_same_attr(self, session: Session, orm_obj_type: Type[T], attr_name: str, attr_value: Any, sort_key: str = None) -> List[T]:
        db_filter = session.query(orm_obj_type).filter(
            getattr(orm_obj_type, attr_name) == attr_value)

        if sort_key is not None:
            db_items = db_filter.order_by(
                getattr(orm_obj_type, sort_key)).all()
        else:
            db_items = db_filter.all()

        return db_items

    @add_session
    def get_items_of_obj(self, session: Session, orm_obj_type: Type[T], obj_id: int, attr_name: str) -> List[T]:
        db_obj = session.query(orm_obj_type).filter(
            orm_obj_type.id == obj_id).first()
        return getattr(db_obj, attr_name)

    def item_obj_iteraction(self, session: Session, orm_obj_type: Type[T],
                            orm_item_type: Type[T],
                            obj_id: int, item_id: int, func: Callable, **kwargs):
        def work(session):
            db_obj = session.query(orm_obj_type).get(obj_id)
            db_item = session.query(orm_item_type).get(item_id)

            if not db_obj or not db_item:
                return False

            return func(session, db_obj, db_item, **kwargs)
        if session is None:
            with self.database.session() as session:
                return work(session)
        return work(session)

    @add_session
    def add_item_to_obj(self, session: Session, orm_obj_type: Type[T], orm_item_type: Type[T],
                        obj_id: int, item_id: int, attr_name: str) -> bool:
        def append_item(session, db_obj, db_item):
            if not db_item in getattr(db_obj, attr_name):
                getattr(db_obj, attr_name).append(db_item)
                session.commit()
                return True
            return False
        return self.item_obj_iteraction(session, orm_obj_type, orm_item_type, obj_id, item_id, append_item)

    @add_session
    def remove_item_from_obj(self, session: Session, orm_obj_type: Type[T], orm_item_type: Type[T],
                             obj_id: int, item_id: int, attr_name: str) -> bool:
        def remove_item(session, db_obj, db_item):
            if db_item in getattr(db_obj, attr_name):
                getattr(db_obj, attr_name).remove(db_item)
                session.commit()
                return True
            return False
        return self.item_obj_iteraction(session, orm_obj_type, orm_item_type, obj_id, item_id, remove_item)

    @add_session
    def create_obj(self, session: Session, orm_obj_type: Type[T], **kwargs) -> T:
        db_item = orm_obj_type(**kwargs)
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        return db_item

    @add_session
    def bulk_create_objs(self, session: Session, orm_obj_type: Type[T], items: List[Dict]) -> bool:
        logger.info(f"Going to bulk create {len(items)} items")
        result = [orm_obj_type(**item) for item in items]
        session.bulk_save_objects(result)
        session.commit()
        return True

    def bulk_create_objs_with_unique_key(self, orm_obj_type: Type[T], items: List[Dict], unique_key: str) -> bool:
        """Bulk create jobs, but check if a value exsists for a unique key"""
        db_items = self.get_items_by_attr(
            orm_obj_type, unique_key, [item[unique_key] for item in items])

        existing_unique_keys = set(getattr(item, unique_key)
                                   for item in db_items)

        # filter out items that already exist
        items = [item for item in items if not item[unique_key]
                 in existing_unique_keys]
        return self.bulk_create_objs(orm_obj_type, items)

    @add_session
    def update_object(self, session: Session, orm_obj_type: Type[T], id: int, **kwargs) -> bool:
        db_item = session.query(orm_obj_type).get(id)
        if not db_item:
            return False
        for key, value in kwargs.items():
            if not hasattr(db_item, key):
                return False
            setattr(db_item, key, value)
        session.commit()
        return True
