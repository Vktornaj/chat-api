FROM python:3.10-alpine

RUN pip install flower

CMD [ "celery", "--broker=amqp://chat:2159228AaA@broker:5672/quetzal", "flower"]