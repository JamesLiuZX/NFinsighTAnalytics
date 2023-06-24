FROM python:3.9-slim-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y gcc

RUN pip3 install -r requirements.txt

WORKDIR /app/etl

COPY ./etl/config.py .
COPY ./etl/database.py .
COPY ./etl/.env .
COPY ./etl/secure-connect-*.zip .

ADD ./etl/celery_app ./celery_app
COPY ./scripts/celery.sh .

WORKDIR /app

RUN ls

ENTRYPOINT celery -A etl.celery_app.celery worker -P gevent -c 3 --loglevel=info
