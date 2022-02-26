"""Database module."""

from contextlib import AbstractContextManager, asynccontextmanager
from typing import Callable
import logging

from sqlalchemy import orm
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

Base = declarative_base()



class Database:

    def __init__(self, db_url: str) -> None:
        self.db_url = db_url
        logger.info(db_url)
        self._engine = create_async_engine(db_url, echo=False)
        self._session_factory = orm.sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine,
                expire_on_commit=False,
                class_=AsyncSession
            )

    async def create_database(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> Callable[..., AbstractContextManager[Session]]:
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            logger.exception("Session rollback because of exception")
            await session.rollback()
            raise
        finally:
            await session.close()
