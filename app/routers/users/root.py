import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
import os

from app.dependencies import get_db, get_current_active_user
from app import crud
from app.core.schemas.user import UserInfo, User
from app.core.schemas.password import Password, UpdatePassword
from app.core.schemas.name import UpdateName
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
    prefix="/users/me",
    tags=["users-me"],
    dependencies=[_current_user:=Depends(get_current_active_user)],
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


@router.get("/", response_model=UserInfo)
async def read_users_me(current_user: User = _current_user):
    return current_user


@router.delete("/")
async def delete_account(
    password: Password, 
    current_user: User = _current_user,
    db: Session = Depends(get_db)
):
    user = utils.authenticate_user(db, current_user.username, password.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    crud.delete_account(db, user.username)
    return { "delete_account": "done" }


@router.get("/items")
async def read_own_items(current_user: User = _current_user):
    return [{"item_id": "Foo", "owner": current_user.username}]


@router.put("/password/update")
async def update_password(
    params: UpdatePassword, 
    current_user: User = _current_user, 
    db: Session = Depends(get_db)
):
    if params.password == params.new_password:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="the new password cannot be the same as the old one"
        )
    user = utils.authenticate_user(db, current_user.username, params.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    crud.update_password(db, user.username, password=params.new_password)
    return { "change_password": "done" }


@router.put("/name/update")
async def update_password(
    params: UpdateName, 
    current_user: User = _current_user, 
    db: Session = Depends(get_db)
):
    if (params.new_first_name == current_user.first_name 
        and params.new_last_name == current_user.last_name):
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="the new name cannot be the same as the old one"
        )
    user = utils.authenticate_user(db, current_user.username, params.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            )
    crud.update_name(
        db,
        user.username, 
        first_name=params.new_first_name,
        last_name=params.new_last_name
    )
    return { "change_name": "done" }


@router.put("/profile-picture/update/{uuid}")
async def update_profile_picture(
    uuid: UUID, 
    current_user: User = _current_user, 
    db: Session = Depends(get_db)
):
    if (uuid == current_user.profile_picture):
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="the new picture cannot be the same as the old one"
        )
    public_storage.delete_dir(f"{current_user.id}/")
    crud.update_profile_picture(
        db,
        current_user.username, 
        profile_picture=uuid
    )
    for size in ["lar", "med", "min"]:
        private_storage.copy_object_to(
            origin_cloud_path=utils.get_cloud_image_path(current_user.id, size, uuid),
            destination_bucket=public_storage.bucket_name,
            destination_cloud_path=utils.get_cloud_image_path(current_user.id, size, uuid)
        )

    return { "profile_picture": uuid }


@router.put("/profile-picture/remove/")
async def update_profile_picture(
    current_user: User = _current_user, 
    db: Session = Depends(get_db)
):
    public_storage.delete_dir(f"{current_user.id}/")
    crud.update_profile_picture(
        db,
        current_user.username, 
        profile_picture=UUID(int=0)
    )

    return { "msg": "done" }
