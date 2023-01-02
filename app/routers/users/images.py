import os
import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone
from typing import List
from PIL import Image

from app.dependencies import get_db, get_current_active_user
from app import crud
from app.core.schemas.user import User
from app.core.schemas.image import ImgDB, ImgInfoURL, ImgInfoUUID, ImgCreate
from app import utils
from app import cloud_storage


# setup loggers
logging.config.fileConfig('app/logging.conf', disable_existing_loggers=False)

# get root logger
logger = logging.getLogger(__name__)  # the __name__ resolve to "main" since we are at the root of the project. 
                                      # This will get the root logger since no logger in the configuration has this name.

C_S_ACCESS_KEY = os.environ["CLOUD_STORAGE_ACCESS_KEY"]
C_S_SECRET_KEY = os.environ["CLOUD_STORAGE_SECRET_KEY"]

PRIVATE_BUCKET = os.environ["CLOUD_PRIVATE_BUCKET"]
PUBLIC_BUCKET = os.environ["CLOUD_PUBLIC_BUCKET"]
PRIVATE_REGION = os.environ["PRIVATE_REGION"]
PUBLIC_REGION = os.environ["PUBLIC_REGION"]

router = APIRouter(
    prefix="/users/me/images",
    tags=["images"],
    dependencies=[
        _current_user:=Depends(get_current_active_user),
        _db:=Depends(get_db)
    ],
    responses={404: {"description": "Not found"}},
)

private_storage = cloud_storage.CloudStorage(
    public_key=C_S_ACCESS_KEY, 
    secret_key=C_S_SECRET_KEY, 
    bucket_name=PRIVATE_BUCKET,
    region_name=PRIVATE_REGION
)
public_storage = cloud_storage.CloudStorage(
    public_key=C_S_ACCESS_KEY, 
    secret_key=C_S_SECRET_KEY, 
    bucket_name=PUBLIC_BUCKET,
    region_name=PUBLIC_REGION
)


@router.post("/upload/")
def upload_img(
    current_user: User = _current_user,
    file: UploadFile = File(...), 
    db: Session = _db
):
    image = Image.open(file.file)
    _uuid = uuid.uuid4()

    utils.upload_versed_images_of_user(
        image=image,
        storage=private_storage,
        uuid=_uuid,
        user_id=current_user.id
    )

    crud.create_user_img(
        db=db,
        image=ImgCreate(
            owner_id=current_user.id,
            title="None",
            description="lorem",
            uuid=_uuid,
            date=datetime.now(timezone.utc)
        )
    )

    return { "image_uuid": f"{_uuid}" }


@router.get("/get/private/{size}/{uuid}/")
def get_img(uuid: uuid.UUID, size: str, current_user: User = _current_user):
    
    cloud_path = utils.get_cloud_image_path(user_id=current_user.id, uuid=uuid, size=size)
    if cloud_path is None:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="invalid size"
        )
    return private_storage.create_presigned_url(cloud_path)


@router.get("/get/public/{size}/{uuid}/")
def get_img(uuid: uuid.UUID, size: str, current_user: User = _current_user):
    
    cloud_path = utils.get_cloud_image_path(user_id=current_user.id, uuid=uuid, size=size)
    if cloud_path is None:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="invalid size"
        )
    return public_storage.get_url(cloud_path)


@router.get("/get/all/url/{size}/", response_model=List[ImgInfoURL])
def get_all_imgs(
    size: str,
    current_user: User = _current_user,
    db: Session = _db
):
    return [
        ImgInfoURL.from_ImgDB(
            img_db=ImgDB.from_orm(item),
            c_storage=private_storage,
            size=size
        )
        for item in 
        crud.read_images(db=db, user_id=current_user.id)
    ]


@router.get("/get/all/uuid/", response_model=List[ImgInfoUUID])
def get_all_imgs(
    current_user: User = _current_user,
    db: Session = _db
):
    return [
        ImgInfoUUID.from_ImgDB(ImgDB.from_orm(item))
        for item in 
        crud.read_images(db=db, user_id=current_user.id)
    ]


@router.delete("/{uuid}/")
def delete_image(
    uuid: uuid.UUID,
    current_user: User = _current_user,
    db: Session = _db
):

    sizes = ["original", "lar", "med", "min"]
    for size in sizes:
        private_storage.delete_file(
            utils.get_cloud_image_path(current_user.id, size, uuid),
        )

    crud.delete_user_img(db, uuid)

    return {"msg": "done"}
