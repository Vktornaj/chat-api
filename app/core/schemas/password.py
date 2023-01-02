from pydantic import BaseModel, ValidationError, validator


# Password
class UpdatePassword(BaseModel):
    password: str
    new_password: str

    @validator('new_password')
    def valid_password(cls, v):
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


class Password(BaseModel):
    password: str
