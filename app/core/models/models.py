from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as AlchemyUUID
from uuid import UUID

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    profile_picture = Column(AlchemyUUID(as_uuid=True), default=UUID(int=0))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True)

    images = relationship("Image", back_populates="owner")
    google_credentials = relationship("GoogleCredentials", back_populates="owner")
    sent_messages = relationship("Message", back_populates="owner")


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    uuid = Column(AlchemyUUID(as_uuid=True))
    date = Column(DateTime)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="images")


class GoogleCredentials(Base):
    __tablename__ = "google_credentials"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String)
    expiry = Column(DateTime)
    _quota_project_id = Column(String)
    _scopes = Column(String)
    _default_scopes = Column(String)
    _refresh_token = Column(String)
    _id_token = Column(String)
    _granted_scopes = Column(String)
    _token_uri = Column(String)
    _client_id = Column(String)
    _client_secret = Column(String)
    _rapt_token = Column(String)
    _refresh_handler = Column(String)
    _enable_reauth_refresh = Column(Boolean)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="google_credentials")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    body = Column(String)
    date = Column(DateTime)
    state = Column(String)
    receiver_id = Column(Integer)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="sent_messages")
