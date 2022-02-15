from datetime import timedelta
from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from webapp.containers import Container
from webapp.models.db_models import MangaSite
from webapp.models.user import Token, TokenData, User
from dependency_injector.wiring import Provide, inject
from logging import getLogger

from jose import JWTError
from webapp.services.database import Database

from webapp.services.secruity_service import SecurityService
from webapp.services.user_service import UserService
from webapp.tests.utils import delete_all

logger = getLogger(__name__)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/token")


@router.post("/signup", response_model=User)
@inject
async def signup(user_service: UserService = Depends(Provide[Container.user_service]),
                 username: str = Form(...), password: str = Form(...)):
    db_user = user_service.create_user(username, password)

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
                                 form_data: OAuth2PasswordRequestForm = Depends()):
    db_user = user_service.get_user(form_data.username)
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
                           token: str = Depends(oauth2_scheme)):
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
    user = user_service.get_user(username=token_data.username)
    user_id = user_service.get_user_id(token_data.username)
    if user is None:
        raise credentials_exception
    return user, user_id


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/fav")
@inject
async def get_fav(current_user: User = Depends(get_current_user),
                  user_service: UserService = Depends(
        Provide[Container.user_service])):
    _, user_id = current_user
    mangas = user_service.get_fav(user_id)
    return mangas


@router.get("/history")
@inject
async def get_history(current_user: User = Depends(get_current_user),
                      user_service: UserService = Depends(
        Provide[Container.user_service])):
    _, user_id = current_user
    mangas = user_service.get_history(user_id)
    return mangas


@router.post("/add_fav")
@inject
async def add_fav(manga_id: int,
                  current_user: User = Depends(get_current_user),
                  user_service: UserService = Depends(
                      Provide[Container.user_service]),
                  ):
    _, user_id = current_user
    return {"success": user_service.add_fav(manga_id, user_id)}


@router.post("/add_history")
@inject
async def add_history(manga_id: int,
                      current_user: User = Depends(get_current_user),
                      user_service: UserService = Depends(
                          Provide[Container.user_service]),
                      ):
    _, user_id = current_user
    return {"success": user_service.add_history(manga_id, user_id)}


@router.delete("/remove_fav")
@inject
async def remove_fav(manga_id: int,
                  current_user: User = Depends(get_current_user),
                  user_service: UserService = Depends(
                      Provide[Container.user_service]),
                  ):
    _, user_id = current_user
    return {"success": user_service.remove_fav(manga_id, user_id)}


@router.delete("/remove_history")
@inject
async def remove_history(manga_id: int,
                     current_user: User = Depends(get_current_user),
                     user_service: UserService = Depends(
                         Provide[Container.user_service]),
                     ):
    _, user_id = current_user
    return {"success": user_service.remove_history(manga_id, user_id)}


@router.delete("/all")
@inject
async def delete_all_data(database: Database = Depends(Provide[Container.db])):
    with database.session() as session:
        delete_all(session)
    return {"success": 200}


@router.post("/init")
@inject
async def init_data(database: Database = Depends(Provide[Container.db])):
    with database.session() as session:
        site = MangaSite(name="manhuaren", url="https://www.manhuaren.com")
        session.add(site)
        session.commit()

    return {"success": 200}
