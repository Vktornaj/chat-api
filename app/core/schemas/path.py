from pydantic import BaseModel


# Item
class Path(BaseModel):
    title: str
    description: str | None = None

    class Config:
        orm_mode = True
