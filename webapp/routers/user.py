from datetime import timedelta
from types import AsyncGeneratorType
from typing import List, Optional, Set
from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from webapp.containers import Container
from webapp.models.chapter import Chapter
from webapp.models.db_models import Manga as DBManga, MangaSite, Chapter as DBChapter
from webapp.models.manga import MangaSimple, MangaWithMeta
from webapp.models.user import Token, TokenData, User
from dependency_injector.wiring import Provide, inject
from logging import getLogger

from jose import JWTError
from webapp.services.crud_service import CRUDService
from webapp.services.database import Database

from webapp.services.secruity_service import SecurityService
from webapp.services.user_service import UserService
from webapp.tests.utils import delete_all, delete_dependent_tables
from webapp.routers import get_session
from sqlalchemy.ext.asyncio import AsyncSession


logger = getLogger(__name__)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/token")


@router.post("/signup", response_model=User)
@inject
async def signup(user_service: UserService = Depends(Provide[Container.user_service]),
                 username: str = Form(...), password: str = Form(...),
                 session_iter: AsyncGeneratorType[AsyncSession] = Depends(get_session)):
    session = await session_iter.__anext__()
    db_user = await user_service.create_user(session, username, password)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )

    return User(username=db_user.email, is_active=db_user.is_active)


@router.post("/token", response_model=Token)
@inject
async def login_for_access_token(user_service: UserService = Depends(Provide[Container.user_service]),
                                 security_service: SecurityService = Depends(
                                     Provide[Container.security_service]),
                                 form_data: OAuth2PasswordRequestForm = Depends(),
                                 session_iter: AsyncGeneratorType[AsyncSession] = Depends(get_session)):
    session = await session_iter.__anext__()
    db_user = await user_service.get_user(session, form_data.username)
    user = security_service.authenticate_user(
        db_user, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=security_service.access_token_expire_minutes)
    access_token = security_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@inject
async def get_current_user(user_service: UserService = Depends(Provide[Container.user_service]),
                           security_service: SecurityService = Depends(
                               Provide[Container.security_service]),
                           token: str = Depends(oauth2_scheme),
                           session_iter: AsyncGeneratorType[AsyncSession] = Depends(get_session)):
    session = await session_iter.__anext__()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security_service.decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await user_service.get_user(session, username=token_data.username)
    user_id = await user_service.get_user_id(session, token_data.username)
    if user is None:
        raise credentials_exception
    return user, user_id


def create_manga_simple(manga: DBManga, chapter: Optional[DBChapter], fav_manga_ids: Set[int]) -> MangaSimple:
    latest_chapter = Chapter() if chapter is None else Chapter.from_orm(chapter)
    manga_with_meta = MangaWithMeta.from_orm(manga)
    return MangaSimple(is_fav=manga.id in fav_manga_ids,
                       latest_chapter=latest_chapter,
                       **manga_with_meta.dict())


@inject
async def get_fav_manga_ids(current_user: User = Depends(get_current_user),
                            user_service: UserService = Depends(
                                Provide[Container.user_service]),
                            session_iter: AsyncGeneratorType[AsyncSession] = Depends(get_session)) -> Set[int]:
    session = await session_iter.__anext__()
    _, user_id = current_user
    fav_mangas = await user_service.get_fav(session, user_id)
    return set(manga.id for manga in fav_mangas)


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    logger.info(current_user)
    return current_user[0]


@router.get("/fav")
@inject
async def get_fav(current_user: User = Depends(get_current_user),
                  crud_service: CRUDService = Depends(
                      Provide[Container.crud_service]),
                  user_service: UserService = Depends(
                      Provide[Container.user_service]),
                  fav_manga_ids: Set[int] = Depends(get_fav_manga_ids),
                  session_iter: AsyncGeneratorType[AsyncSession] = Depends(get_session)):
    session = await session_iter.__anext__()
    _, user_id = current_user
    history = await user_service.get_history(session, user_id)
    db_mangas = await crud_service.get_items_by_ids(
        session, DBManga, [h.manga_id for h in history if h.manga_id in fav_manga_ids])
    db_chapters = await crud_service.get_items_by_ids(
        session, DBChapter, [h.chaper_id for h in history if h.manga_id in fav_manga_ids], keep_none=True
    )
    return [create_manga_simple(manga, chapter, fav_manga_ids)
            for manga, chapter in zip(db_mangas, db_chapters)]


@router.get("/history", response_model=List[MangaSimple])
@inject
async def get_history(current_user: User = Depends(get_current_user),
                      user_service: UserService = Depends(
                          Provide[Container.user_service]),
                      crud_service: CRUDService = Depends(
                          Provide[Container.crud_service]),
                      fav_manga_ids: Set[int] = Depends(get_fav_manga_ids),
                      session_iter: AsyncGeneratorType[AsyncSession] = Depends(get_session)):

    session = await session_iter.__anext__()
    _, user_id = current_user
    history = await user_service.get_history(session, user_id)
    db_mangas = await crud_service.get_items_by_ids(
        session, DBManga, [h.manga_id for h in history])
    db_chapters = await crud_service.get_items_by_ids(
        session, DBChapter, [h.chaper_id for h in history], keep_none=True
    )
    return [create_manga_simple(manga, chapter, fav_manga_ids)
            for manga, chapter in zip(db_mangas, db_chapters)]


@router.get("/latest_chap", response_model=Chapter)
@inject
async def get_latest_chap(manga_id: int,
                          current_user: User = Depends(get_current_user),
                          user_service: UserService = Depends(
                              Provide[Container.user_service]),
                          session_iter: AsyncGeneratorType[AsyncSession] = Depends(
                              get_session),
                          ):
    session = await session_iter.__anext__()
    _, user_id = current_user
    db_chap = await user_service.get_latest_chap(session, user_id, manga_id)
    if not db_chap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    return db_chap


@router.post("/add_fav")
@inject
async def add_fav(manga_id: int,
                  current_user: User = Depends(get_current_user),
                  user_service: UserService = Depends(
                      Provide[Container.user_service]),
                  session_iter: AsyncGeneratorType[AsyncSession] = Depends(
                      get_session)
                  ):
    session = await session_iter.__anext__()
    _, user_id = current_user
    db_user = await user_service.add_fav(session, manga_id, user_id)
    result = True if db_user else False
    return {"success": result}


@router.post("/add_history")
@inject
async def add_history(manga_id: int,
                      current_user: User = Depends(get_current_user),
                      user_service: UserService = Depends(
                          Provide[Container.user_service]),
                      session_iter: AsyncGeneratorType[AsyncSession] = Depends(
                          get_session)
                      ):
    session = await session_iter.__anext__()
    _, user_id = current_user
    db_history = await user_service.add_history(session, manga_id, user_id)
    result = True if db_history else False
    return {"success": result}


@router.delete("/remove_fav")
@inject
async def remove_fav(manga_id: int,
                     current_user: User = Depends(get_current_user),
                     user_service: UserService = Depends(
                         Provide[Container.user_service]),
                     session_iter: AsyncGeneratorType[AsyncSession] = Depends(
                         get_session)
                     ):
    session = await session_iter.__anext__()
    _, user_id = current_user
    db_user = await user_service.remove_fav(session, manga_id, user_id)
    result = True if db_user else False
    return {"success": result}


@router.delete("/remove_history")
@inject
async def remove_history(manga_id: int,
                         current_user: User = Depends(get_current_user),
                         user_service: UserService = Depends(
                             Provide[Container.user_service]),
                         session_iter: AsyncGeneratorType[AsyncSession] = Depends(
                             get_session)
                         ):
    session = await session_iter.__anext__()
    _, user_id = current_user
    db_history = await user_service.remove_history(session, manga_id, user_id)
    result = True if db_history else False
    return {"success": result}


@router.put("/update_history")
@inject
async def update_history(chap_id: int,
                         current_user: User = Depends(get_current_user),
                         user_service: UserService = Depends(
                             Provide[Container.user_service]),
                         session_iter: AsyncGeneratorType[AsyncSession] = Depends(
                             get_session)):
    session = await session_iter.__anext__()
    _, user_id = current_user
    result = await user_service.update_history(session, chap_id, user_id)
    return {"success": result}


@router.delete("/all")
@inject
async def delete_all_data(database: Database = Depends(Provide[Container.db])):
    async with database.session() as session:
        async with session.begin():
            await delete_all(session)
            await session.commit()

    async with database.session() as session:
        async with session.begin():
            await delete_dependent_tables(session)
            await session.commit()
    return {"success": 200}


@router.post("/init")
@inject
async def init_data(database: Database = Depends(Provide[Container.db])):
    async with database.session() as session:
        async with session.begin():
            session.add(MangaSite(name="manhuaren",
                        url="https://www.manhuaren.com"))
            session.add(MangaSite(name="anime1", url="https://anime1.me/"))
            await session.commit()

    return {"success": 200}
