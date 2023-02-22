import os
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
# from datetime import datetime, timezone
import redis
from datetime import timedelta
import uuid
import json
import pickle

from dependencies import get_db, get_current_active_user
# import crud
from core.schemas.user import User
import utils
# from core.schemas.message import MessageSend, MessageCreate


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

TEMPORARY_ACCESS_TOKEN_EXP_M = int(os.environ["TEMPORARY_ACCESS_TOKEN_EXPIRE_MINUTES"])

router = APIRouter(
    prefix="/users/me/messages",
    tags=["messages token"],
    responses={404: {"description": "Not found"}},
)

cache = redis.Redis(host="cache")

# @router.post("/send/")
# def send_message(
#     message: MessageSend,
#     current_user: User = _current_user,
#     db: Session = _db
# ):
#     message = crud.create_message(
#         db=db,
#         message=MessageCreate(
#             owner_id=current_user.id,
#             receiver_id=crud.read_user_by_username(db, message.receiver).id,
#             body=message.body,
#             date=datetime.now(timezone.utc),
#             state="sent"
#         )
#     )

#     return { "message_uuid": f"{message.id}" }


# @router.put("/confirm_of_received/{_uuid}")
# def confirm_of_received(
#     _uuid: uuid.UUID, current_user: User = _current_user, db: Session = _db
# ):
#     if not current_user:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

#     crud.delete_message(db=db, uuid=_uuid)

#     return { "msg": "done" }


# TODO: make endpoint to generate authentication token
@router.get("/token/")
def get_token_message(
    current_user: User = Depends(get_current_active_user), 
):
    _uuid = json.dumps(uuid.uuid4(), cls=utils.UUIDEncoder)

    temporary_token = utils.create_access_token(
        data={ "client_id":  _uuid}, 
        expires_delta=timedelta(minutes=TEMPORARY_ACCESS_TOKEN_EXP_M),
        temporary=True
    )

    cache.set(name=_uuid, value=current_user.id, ex=TEMPORARY_ACCESS_TOKEN_EXP_M)

    return {"access_token": temporary_token, "token_type": "bearer"}
