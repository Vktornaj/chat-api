from celery import Celery
import os
import logging


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

app = Celery('tasks', broker=os.environ.get("BROKER_URL"))


@app.task(name='sendMessage')
def send_message(data_dict: dict):
    logger.info("Hello from celery")
    logger.info(type(data_dict))
