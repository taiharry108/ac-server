from datetime import timedelta
from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from webapp.containers import Container
from webapp.models.user import Token, TokenData, User
from dependency_injector.wiring import Provide, inject
from logging import getLogger

from jose import JWTError

from webapp.services.secruity_service import SecurityService

logger = getLogger(__name__)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/token")


@router.post("/signup", response_model=User)
@inject
async def signup(security_service: SecurityService = Depends(Provide[Container.security_service]),
                 username: str = Form(...), password: str = Form(...)):
    db_user = security_service.create_user(username, password)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )

    return User(username=db_user.email, is_active=db_user.is_active)


@router.post("/token", response_model=Token)
@inject
async def login_for_access_token(security_service: SecurityService = Depends(Provide[Container.security_service]),
                                 form_data: OAuth2PasswordRequestForm = Depends()):
    user = security_service.authenticate_user(
        form_data.username, form_data.password)
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
async def get_current_user(security_service: SecurityService = Depends(Provide[Container.security_service]),
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
    user = security_service.get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


# async def get_current_active_user(current_user: User = Depends(get_current_user)):
#     if current_user.disabled:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
