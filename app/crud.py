from sqlalchemy.orm import Session
from passlib.context import CryptContext
from uuid import UUID

from core.schemas.user import UserCreate
from core.schemas.image import ImgCreate
from core.schemas.google import Credentials
from core.models import models
from core.schemas.message import MessageCreate


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def read_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def read_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def read_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def read_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate):
    if user.password:
        hashed_password = get_password_hash(user.password)
    else:
        hashed_password = None

    db_user = models.User(
        email=user.email, 
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.email
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def read_images(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.Image).filter(models.Image.owner_id == user_id) \
        .offset(skip).limit(limit).all()


def create_user_img(db: Session, image: ImgCreate):
    db_img = models.Image(**image.dict())
    db.add(db_img)
    db.commit()
    db.refresh(db_img)
    return db_img


def delete_user_img(db: Session, uuid: UUID):
    image = db.query(models.Image).filter(models.Image.uuid == uuid)
    image.delete()
    db.commit()


def update_password(db: Session, username: str, password: str):
    hashed_password = get_password_hash(password)
    user = db.query(models.User).filter(models.User.username == username)
    user.update({'hashed_password': hashed_password})
    db.commit()
    return user.first()


def update_name(db: Session, username: str, first_name: str, last_name: str):
    user = db.query(models.User).filter(models.User.username == username)
    user.update({'first_name': first_name})
    user.update({'last_name': last_name})
    db.commit()
    return user.first()


def update_profile_picture(db: Session, username: str, profile_picture: UUID):
    user = db.query(models.User).filter(models.User.username == username)
    user.update({'profile_picture': profile_picture})
    db.commit()
    return user.first()


def delete_account(db: Session, username: str):
    user = db.query(models.User).filter(models.User.username == username)
    user.delete()
    db.commit()
    db.refresh()


def create_user_google_credentials(db: Session, credentials: Credentials, owner_id: int):
    db_credentials = models.GoogleCredentials(**credentials.dict(), owner_id=owner_id)
    db.add(db_credentials)
    db.commit()
    db.refresh(db_credentials)
    return db_credentials


def read_user_google_credentials(db: Session, user_id: int):
    return db.query(models.GoogleCredentials) \
        .filter(models.GoogleCredentials.owner_id == user_id).first()


def create_message(db: Session, message: MessageCreate):
    db_message = models.Message(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def delete_message(db: Session, id: int):
    user = db.query(models.Message).filter(models.Message.id == id)
    user.delete()
    db.commit()
    db.refresh()


# TODO: finish function
def read_messages(db: Session, skip: int = 0, limit: int = 10):
    pass
