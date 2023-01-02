import os
from datetime import timedelta
from email.headerregistry import Address
import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import redis
import json

from app.dependencies import get_db
from app import crud
from app.core.schemas.token import Token
from app.core.schemas.user import UserCreate
from app.core.schemas.confirmation import ConfirmationEmail
from app import utils
from app.send_emails import emails as _emails


# setup loggers
logging.config.fileConfig('app/logging.conf', disable_existing_loggers=False)

# get root logger
logger = logging.getLogger(__name__)  # the __name__ resolve to "main" since we are at the root of the project. 
                                      # This will get the root logger since no logger in the configuration has this name.

ACCESS_TOKEN_EXP_M = int(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"])
CONF_CODE_EXP_S = 300

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[_db:=Depends(get_db)],
    responses={404: {"description": "Not found"}},
)

cache = redis.Redis(host="cache")


@router.post("/authenticate", response_model=Token)
async def login_for_access_token(db: Session = _db, form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.password == "":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    user = utils.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXP_M)
    access_token = utils.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_202_ACCEPTED)
def register(user: UserCreate, background_tasks: BackgroundTasks, db: Session = _db):

    user.email = user.email.lower()

    if cache.exists(user.email):
        raise HTTPException(status_code=409, detail="email not available")

    if crud.read_user_by_email(db, email=user.email):
        raise HTTPException(status_code=409, detail="email not available")

    email_array = user.email.split('@')

    code = utils.get_random_code(digits=6)

    background_tasks.add_task(
        _emails.send_confirmation_email,
        to=Address(display_name=user.first_name, username=email_array[0], domain=email_array[-1]),
        code=str(code)
    )

    user.code = str(code)

    cache.set(user.email, user.json(), ex=CONF_CODE_EXP_S)

    return {
        "email": user.email,
        "msg": f"the email must be confirmed within {CONF_CODE_EXP_S / 60} minutes"
    }


@router.post("/confirmation")
def confirmation_email(data: ConfirmationEmail, db: Session = _db):
    if cache.exists(data.email):
        register_request: dict = json.loads(cache.get(data.email))
    else:
        HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="request not found"
        )

    if data.code == register_request["code"]:
        cache.delete(data.email)
        crud.create_user(
            db=db, 
            user=UserCreate.parse_obj(register_request)
        )        
        return {"msg": "successfully verified"}

    raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail="invalid code"
    )
