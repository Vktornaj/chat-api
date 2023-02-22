FROM python:3.10-alpine

WORKDIR /code

# RUN apt-get -y update && apt-get -y install build-essential
RUN apk add build-base

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "main:app", "--bind", "0.0.0.0:8000"]
