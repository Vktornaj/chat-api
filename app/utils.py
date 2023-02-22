import os
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
import random
import logging
from PIL import Image
from datetime import timezone
from uuid import UUID
import io
import json

import crud
from core.schemas.user import User
import cloud_storage


# setup loggers
logging.config.fileConfig('./logging.conf', disable_existing_loggers=False)

# get root logger
logger = logging.getLogger(__name__)  # the __name__ resolve to "main" since we are at the root of the project. 
# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.environ["SECRET_KEY"]
TEMPORARY_SECRET_KEY = os.environ["TEMPORARY_SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"])


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)


# Utils
def get_user(db, username: str):
    if user := crud.read_user_by_username(db, username=username):
        return User.from_orm(user)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db, username: str, password: str):
    if user := get_user(db, username):
        return user if verify_password(password, user.hashed_password) else False
    else:
        return False


def create_access_token(
    data: dict, expires_delta: timedelta | None = None, temporary: bool = False
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode["exp"] = expire
    return jwt.encode(
        to_encode, 
        TEMPORARY_SECRET_KEY if temporary else SECRET_KEY, 
        algorithm=ALGORITHM
    )


def get_random_code(digits):
    range_start = 10**(digits - 1)
    range_end = (10**digits) - 1
    return random.randint(range_start, range_end)


def square_image(image: Image, length: int) -> Image:
    """
    Resize an image to a square. Can make an image bigger to make it fit or smaller if it doesn't fit. It also crops
    part of the image.

    :param self:
    :param image: Image to resize.
    :param length: Width and height of the output image.
    :return: Return the resized image.
    """

    """
    Resizing strategy : 
     1) We resize the smallest side to the desired dimension (e.g. 1080)
     2) We crop the other side so as to make it fit with the same length as the smallest side (e.g. 1080)
    """
    if image.size[0] < image.size[1]:
        # The image is in portrait mode. Height is bigger than width.

        # This makes the width fit the LENGTH in pixels while conserving the ration.
        resized_image = image.resize((length, int(image.size[1] * (length / image.size[0]))))

        # Amount of pixel to lose in total on the height of the image.
        required_loss = (resized_image.size[1] - length)

        # Crop the height of the image so as to keep the center part.
        resized_image = resized_image.crop(
            box=(0, required_loss / 2, length, resized_image.size[1] - required_loss / 2))

        # We now have a length*length pixels image.
        return resized_image
    else:
        # This image is in landscape mode or already squared. The width is bigger than the heihgt.

        # This makes the height fit the LENGTH in pixels while conserving the ration.
        resized_image = image.resize((int(image.size[0] * (length / image.size[1])), length))

        # Amount of pixel to lose in total on the width of the image.
        required_loss = resized_image.size[0] - length

        # Crop the width of the image so as to keep 1080 pixels of the center part.
        resized_image = resized_image.crop(
            box=(required_loss / 2, 0, resized_image.size[0] - required_loss / 2, length))

        # We now have a length*length pixels image.
        return resized_image


def get_cloud_image_path(user_id: str, size: str, uuid: str) -> str:
    match_extension = {
        "original": "jpeg",
        "lar": "webp",
        "med": "webp",
        "min": "webp",
    }
    if size not in match_extension:
        return None
    return f"{user_id}/{size}/{uuid}.{match_extension[size]}"


# Google
def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}


def print_index_table():
  return ('<table>' +
          '<tr><td><a href="/test">Test an API request</a></td>' +
          '<td>Submit an API request and see a formatted JSON response. ' +
          '    Go through the authorization flow if there are no stored ' +
          '    credentials for the user.</td></tr>' +
          '<tr><td><a href="/authorize">Test the auth flow directly</a></td>' +
          '<td>Go directly to the authorization flow. If there are stored ' +
          '    credentials, you still might not be prompted to reauthorize ' +
          '    the application.</td></tr>' +
          '<tr><td><a href="/revoke">Revoke current credentials</a></td>' +
          '<td>Revoke the access token associated with the current user ' +
          '    session. After revoking credentials, if you go to the test ' +
          '    page, you should see an <code>invalid_grant</code> error.' +
          '</td></tr>' +
          '<tr><td><a href="/clear">Clear Flask session credentials</a></td>' +
          '<td>Clear the access token currently stored in the user session. ' +
          '    After clearing the token, if you <a href="/test">test the ' +
          '    API request</a> again, you should go back to the auth flow.' +
          '</td></tr></table>')


# TODO: generalize function
def upload_versed_images_of_user(
    image: Image, 
    storage: cloud_storage.CloudStorage,
    uuid: UUID,
    user_id: int
):
    image_lar = square_image(image=image, length=1080)
    image_med = square_image(image=image, length=720)
    image_min = square_image(image=image, length=150)

    with io.BytesIO() as in_mem_file:
        image.save(in_mem_file, format="JPEG", quality=95)
        in_mem_file.seek(0)
        storage.upload_file(
            cloud_path=f"{user_id}/original/{uuid}.jpeg",
            local_path_or_file=in_mem_file
        )
    with io.BytesIO() as in_mem_file:
        image_lar.save(in_mem_file, format="WEBP", quality=95)
        in_mem_file.seek(0)
        storage.upload_file(
            cloud_path=f"{user_id}/lar/{uuid}.webp",
            local_path_or_file=in_mem_file
        )
    with io.BytesIO() as in_mem_file:
        image_med.save(in_mem_file, format="WEBP", quality=95)
        in_mem_file.seek(0)
        storage.upload_file(
            cloud_path=f"{user_id}/med/{uuid}.webp",
            local_path_or_file=in_mem_file
        )
    with io.BytesIO() as in_mem_file:
        image_min.save(in_mem_file, format="WEBP", quality=95)
        in_mem_file.seek(0)
        storage.upload_file(
            cloud_path=f"{user_id}/min/{uuid}.webp",
            local_path_or_file=in_mem_file
        )


