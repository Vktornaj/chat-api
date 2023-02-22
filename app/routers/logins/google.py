from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
import os
from google_auth_oauthlib.flow import Flow
from sqlalchemy.orm import Session
import requests
from datetime import timedelta
from PIL import Image
import uuid
from datetime import datetime, timezone
from io import BytesIO
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError

import utils
import crud
from dependencies import get_db
from core.schemas.google import Credentials as Credentials
from core.schemas.user import User, UserCreate
from core.schemas.image import ImgCreate
import cloud_storage


ACCESS_TOKEN_EXP_M = int(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"])
CONF_CODE_EXP_S = 300
REDIRECT_URI = os.environ["GOOGLE_REDIRECT_URI"]
CLIENT_SECRETS_FILE = 'app/client_secret.json'
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile"
]
API_VERSION = 'v2'
API_SERVICE_NAME = 'drive'
DATA_URL_1 = "https://www.googleapis.com/oauth2/v1/userinfo"
DATA_URL_2 = "https://openidconnect.googleapis.com/v1/userinfo"

C_S_ACCESS_KEY = os.environ["CLOUD_STORAGE_ACCESS_KEY"]
C_S_SECRET_KEY = os.environ["CLOUD_STORAGE_SECRET_KEY"]

PRIVATE_BUCKET = os.environ["CLOUD_PRIVATE_BUCKET"]
PUBLIC_BUCKET = os.environ["CLOUD_PUBLIC_BUCKET"]
PRIVATE_REGION = os.environ["PRIVATE_REGION"]
PUBLIC_REGION = os.environ["PUBLIC_REGION"]

router = APIRouter(
    prefix="/google-login",
    tags=["google login"],
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


@router.get("/authorize", response_class=RedirectResponse)
def authorize():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES)

    flow.redirect_uri = REDIRECT_URI
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    return authorization_url


# @router.get("/oauth2callback", response_class=RedirectResponse)
@router.get("/oauth2callback")
def oauth2callback(request: Request, db: Session = Depends(get_db)):
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.

    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI

    try:
        # Use the authorization server's response to fetch the OAuth 2.0 tokens.
        flow.fetch_token(
            authorization_response=str(request.url).replace("http://", "https://")
        )
    except InvalidGrantError:
        raise HTTPException(status_code=400, detail="Bad Request")

    credentials = Credentials.from_google_credentials(flow.credentials)

    res = requests.get(
        url=DATA_URL_2, headers={"Authorization": f"Bearer {credentials.token}"}
    )

    if res.status_code == 200:
        user_info = res.json()
    else:
        raise HTTPException(status_code=409, detail="not authorized")

    if not user_info["email_verified"]:
        raise HTTPException(status_code=409, detail="verify your google email address")

    if not crud.read_user_by_email(db, email=user_info["email"]):
        new_user = User.from_orm(
            crud.create_user(
                db=db,
                user=UserCreate(
                    first_name=user_info["name"],
                    last_name=user_info["family_name"],
                    email=user_info["email"],
                    password=None
                )
            )
        )
        # Store credentials in the sb.
        # Create a new user
        # TODO: set expiration date
        crud.create_user_google_credentials(
            db=db,
            credentials=credentials,
            owner_id=new_user.id
        ).id
        response = requests.get(user_info["picture"])
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            _uuid = uuid.uuid4()

            utils.upload_versed_images_of_user(
                image=image,
                storage=private_storage,
                uuid=_uuid,
                user_id=new_user.id
            )

            crud.create_user_img(
                db=db,
                image=ImgCreate(
                    owner_id=new_user.id,
                    title="None",
                    description="lorem",
                    uuid=_uuid,
                    date=datetime.now(timezone.utc)
                )
            )
            crud.update_profile_picture(db, user_info["email"], profile_picture=_uuid)
            for size in ["lar", "med", "min"]:
                private_storage.copy_object_to(
                    origin_cloud_path=utils.get_cloud_image_path(
                        new_user.id, size, _uuid
                    ),
                    destination_bucket=public_storage.bucket_name,
                    destination_cloud_path=utils.get_cloud_image_path(
                        new_user.id, size, _uuid
                    )
                )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXP_M)
    access_token = utils.create_access_token(
        data={"sub": user_info["email"]}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# @router.get('/revoke')
# def revoke():
#   if 'credentials' not in flask.session:
#     return ('You need to <a href="/authorize">authorize</a> before ' +
#             'testing the code to revoke credentials.')

#   credentials = google.oauth2.credentials.Credentials(
#     **flask.session['credentials'])

#   revoke = requests.post('https://oauth2.googleapis.com/revoke',
#       params={'token': credentials.token},
#       headers = {'content-type': 'application/x-www-form-urlencoded'})

#   status_code = getattr(revoke, 'status_code')
#   if status_code == 200:
#     return('Credentials successfully revoked.' + utils.print_index_table())
#   else:
#     return('An error occurred.' + utils.print_index_table())
