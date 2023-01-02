from pydantic import BaseModel, ValidationError, validator


# User
class UpdateName(BaseModel):
    password: str
    new_first_name: str
    new_last_name: str

    @validator('new_first_name', 'new_last_name')
    def must_be_albabetic(cls, v):
        s: str = v.replace(' ', '')
        if not s.isalpha():
            raise ValueError('must be alphanumeric')
        if len(s) < 1:
            raise ValueError('must be at least one character')
        if len(s) > 100:
            raise ValueError('must be minor than 100 characteres')
        return v.title()
