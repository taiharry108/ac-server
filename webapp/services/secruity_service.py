import dataclasses
from datetime import datetime, timedelta
from typing import Optional, Union

from passlib.context import CryptContext

from jose import jwt

from webapp.models.user import UserInDB
from webapp.models.db_models import User as DBUser
from webapp.services.crud_service import CRUDService

from logging import getLogger

logger = getLogger(__name__)


@dataclasses.dataclass
class SecurityService:
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    crud_service: CRUDService
    pwd_context: CryptContext

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> bool:
        return self.pwd_context.hash(password)

    def get_user(self, username: str) -> Optional[UserInDB]:
        db_user = self.crud_service.get_item_by_attr(DBUser, "email", username)
        if db_user is None:
            return None
        return UserInDB(username=db_user.email,
                        is_active=db_user.is_active,
                        hashed_password=db_user.hashed_password)

    def authenticate_user(self, username: str, password: str) -> Union[bool, UserInDB]:
        user = self.get_user(username)
        if not user:
            return False
        if not self.verify_password(password, user.hashed_password):
            return False
        return user

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_access_token(self, token: str):
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

    def create_user(self, username: str, password: str) -> Optional[DBUser]:
        if self.get_user(username):            
            return None
        hashed_password = self.hash_password(password)
        db_user = self.crud_service.create_obj(
            DBUser, email=username, hashed_password=hashed_password)
        return db_user
