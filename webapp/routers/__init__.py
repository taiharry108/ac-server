from dependency_injector.wiring import inject, Provide
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from webapp.containers import Container
from webapp.services.crud_service import CRUDService

@inject
async def get_session(crud_service: CRUDService = Depends(
        Provide[Container.crud_service])) -> AsyncSession:
    while True:
        async with crud_service.database.session() as session:
            async with session.begin():
                yield session
