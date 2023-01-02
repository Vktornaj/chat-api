from PIL import Image
import requests
from io import BytesIO

from app import cloud_storage


C_S_ACCESS_KEY = ""
C_S_SECRET_KEY = ""

C_S_PRIVATE_BUCKET = "chat-users"
C_S_PUBLIC_BUCKET = "chat-public"


def test_create_presigned_url_private():
    private_storage = cloud_storage.CloudStorage(
        public_key=C_S_ACCESS_KEY, 
        secret_key=C_S_SECRET_KEY, 
        bucket_name=C_S_PRIVATE_BUCKET
    )
    url = private_storage.create_presigned_url(cloud_path="1/7fddbf07-3e00-4666-9e0d-d17f648ccc89")
    print(url)
    image = Image.open(BytesIO(requests.get(url).content))
    assert bool(image.format)


# def test_create_presigned_url_public():
#     public_storage = cloud_storage.CloudStorage(
#         public_key=C_S_ACCESS_KEY, 
#         secret_key=C_S_SECRET_KEY, 
#         bucket_name=C_S_PUBLIC_BUCKET
#     )
#     public_storage.create_presigned_url(cloud_path="")

