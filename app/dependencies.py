from fastapi import (
    Depends, HTTPException, status, Cookie, Query
)
from .database import SessionLocal, engine
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import os

from app.core.models import models
from app.core.schemas.token import TokenData
from app.core.schemas.user import User
from app import utils

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.environ["SECRET_KEY"]
TEMPORARY_SECRET_KEY = os.environ["TEMPORARY_SECRET_KEY"]
ALGORITHM = "HS256"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/authenticate")

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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
    except JWTError as e:
        raise credentials_exception from e
    user = utils.get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_client_id(token: str | None = Query(default=None)):
    try:
        payload = jwt.decode(token, TEMPORARY_SECRET_KEY, algorithms=[ALGORITHM])
        client_id: str = payload.get("client_id")
        if client_id is None:
            return None
    except JWTError:
        return None
    return client_id
