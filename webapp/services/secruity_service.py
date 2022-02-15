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
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except ValueError:
            return False

    def hash_password(self, password: str) -> bool:
        return self.pwd_context.hash(password)

    def authenticate_user(self, db_user: DBUser, password: str) -> Union[bool, UserInDB]:        
        if not db_user:
            logger.info("user not exists")
            return False
        
        if not self.verify_password(
                password, db_user.hashed_password):
            logger.info("wrong password")
            return False
        return db_user

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
