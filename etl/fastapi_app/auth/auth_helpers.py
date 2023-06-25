import os

from datetime import datetime, timedelta
from typing import Annotated, Union

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status

from etl.database import CassandraDb

from .models import TokenData, User, UserInDB
from ..dependencies import oauth2_scheme, pwd_context


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    session = CassandraDb.get_db_session()
    statement = session.prepare(
        """
        SELECT username, hashed_password, disabled
        FROM admin_user
        WHERE username = ?
        """
    )
    res = session.execute(statement, [username]).one()
    if res is None:
        return None
    return UserInDB(
        username=res.username,
        disabled=res.disabled,
        hashed_password=res.hashed_password
    )


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    SECRET_KEY = os.getenv("SECRET_KEY")

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    SECRET_KEY = os.getenv("SECRET_KEY")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
