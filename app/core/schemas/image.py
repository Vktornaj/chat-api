from datetime import datetime
from pydantic import BaseModel
from uuid import UUID

import cloud_storage
import utils


# Img
class Image(BaseModel):
    title: str
    description: str | None = None
    date: datetime


class ImgCreate(Image):
    owner_id: int
    uuid: UUID

    class Config:
        orm_mode = True


class ImgDB(ImgCreate):
    id: int


class ImgInfoURL(Image):
    url: str

    @classmethod
    def from_ImgDB(cls, img_db: ImgDB, c_storage: cloud_storage.CloudStorage, size: str) -> "ImgInfoURL":
        return cls(
            title=img_db.title,
            description=img_db.description,
            date=img_db.date,
            url=c_storage.create_presigned_url(utils.get_cloud_image_path(img_db.owner_id, size, img_db.uuid))
        )


class ImgInfoUUID(Image):
    uuid: UUID

    @classmethod
    def from_ImgDB(cls, img_db: ImgDB) -> "ImgInfoUUID":
        return cls(
            title=img_db.title,
            description=img_db.description,
            date=img_db.date,
            uuid=img_db.uuid
        )
