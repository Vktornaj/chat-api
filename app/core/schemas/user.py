from pydantic import BaseModel, EmailStr, ValidationError, validator, constr
import uuid


# TODO: check if code is needed 
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str | None
    code: str | None
    # TODO: add this data
    # birth_date: date
    # nationality: str
    # languages: List[str]

    @validator('first_name', 'last_name')
    def must_be_albabetic(cls, v):
        s: str = v.replace(' ', '')
        if not s.isalpha():
            raise ValueError('must be alphanumeric')
        if len(s) < 1:
            raise ValueError('must be at least one character')
        if len(s) > 100:
            raise ValueError('must be minor than 100 characteres')
        return v.title()

    @validator('password')
    def valid_password(cls, v):
        if v is None:
            return None
        if len(v) < 8:
            raise ValueError('must be at least 8 characters')
        if len(v) > 20:
            raise ValueError('must be minor than 20 digits')
        if v.isalpha():
            raise ValueError('must contain at least one number')
        if v.isnumeric():
            raise ValueError('must contain at least one letter')
        if v.islower():
            raise ValueError('must contain at least one uppercase')
        if v.isupper():
            raise ValueError('must contain at least one lowercase')
        return v.title()


class UserInfo(BaseModel):
    email: str
    username: str | None
    first_name: str 
    last_name: str 
    is_active: bool | None = True
    is_verified: bool | None = True
    profile_picture: uuid.UUID | None

    class Config:
        orm_mode = True


class User(BaseModel):
    id: int
    email: str
    username: str
    hashed_password: str | None
    first_name: str
    last_name: str
    profile_picture: uuid.UUID
    is_active: bool
    is_verified: bool

    class Config:
        orm_mode = True
