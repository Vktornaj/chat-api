import os
from fastapi import (
    FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import redis
from datetime import datetime, timezone
import logging
import pickle

from app import crud
from app.routers.logins import standar
from app.routers.users import images
from app.routers.users import root as _root
from app.routers.users import messages
from app.routers.logins import google
from app.core.schemas.message import MessageSend, MessageCreate
from app.core.schemas.user import User
# from app.core.schemas.user import User
from app.dependencies import get_db, get_client_id


ALLOWED_ORIGINS = os.environ["ALLOWED_ORIGINS"].split(",")
TEMPORARY_ACCESS_TOKEN_EXP_M = int(os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"])

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(images.router)
app.include_router(_root.router)
app.include_router(standar.router)
app.include_router(google.router)
app.include_router(messages.router)

origins = ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cache = redis.Redis(host="cache")
# celery_app = Celery('task', broker=os.environ.get("BROKER_URL"))

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Chat api API! Visit chat.geduardo.com"
    }


@app.get("/privacy-policy/")
async def privacy_policy():
    return {
        "message": "Welcome to the Chat api API! privacy policy"
    }

    
@app.get("/terms-of-service/")
async def terms_of_service():
    return {
        "message": "Welcome to the Chat api API terms of service"
    }


# ---websockets---

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if not client_id in self.active_connections:
            self.active_connections[client_id] = websocket
            return True
        return False

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id)

    async def send_personal_message(
        self, 
        message: MessageSend,
        client_id: str
    ):
        if websocket := self.active_connections.get(client_id):
            await websocket.send_json({
                "body": message.body,
                "sender": message.sender
            })
            return True
        return False

    async def broadcast(self, message: MessageSend):
        for connection in self.active_connections.values():
            await connection.send_json({
                "receiver": message.receiver,
                "body": message.body,
                "sender": message.sender
            })


manager = ConnectionManager()


async def send_messag(
    db: Session, sender_username: str, data_dict: dict[str, str]
):  
    receiver: User = crud.read_user_by_username(db, data_dict["receiver"])
    logger.info(f"active sockets: { str(manager.active_connections.keys()) }")
    logger.info(
        f"active sessions of {receiver.id}: { str(pickle.loads(cache.get(receiver.id))) }"
    )
    if receiver_sessions := pickle.loads(cache.get(receiver.id)):
        for client_id in receiver_sessions:
            await manager.send_personal_message(
                MessageSend(
                    sender=sender_username, 
                    receiver=data_dict["receiver"], 
                    body=data_dict["body"]
                ), 
                client_id
            )


def get_user_id(client_id: str):
    if not client_id:
        logger.info("no client_id")
        return None
    
    user_id = cache.get(client_id)
    if not user_id:
        logger.info("no user_id")
        return None
    return user_id
            

@app.websocket("/messages/wss")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db)
):
    user_id = get_user_id(client_id)
    if user_id is None:
        return

    user: User = crud.read_user(db, int(user_id.decode()))

    if sessions := cache.get(user_id):
        if sessions := pickle.loads(sessions):
            sessions.append(client_id)
        else:
            sessions = [client_id]

    cache.set(name=user.id, value=pickle.dumps(sessions))

    if not await manager.connect(websocket, client_id):
        return
    try:
        while True:
            data_dict = await websocket.receive_json()
            await send_messag(db, user.username, data_dict)

    except WebSocketDisconnect:
        if sessions := pickle.loads(cache.get(user.id)):
            sessions.remove(client_id)
            cache.set(user.id, pickle.dumps(sessions))
        manager.disconnect(client_id)
