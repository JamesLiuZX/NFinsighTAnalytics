# Compile Image
FROM python:3.9-slim-bullseye AS compile-image

WORKDIR /app

RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc

RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

COPY ./etl/celery_app/requirements.txt .

RUN pip install -r requirements.txt

# Build Image
FROM python:3.9-slim-bullseye AS build-image
COPY --from=compile-image /opt/venv /opt/venv

# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app/etl

COPY ./etl/config.py .
COPY ./etl/database.py .
COPY ./etl/.env .
COPY ./etl/secure-connect-*.zip .

ADD ./etl/celery_app ./celery_app
COPY ./scripts/celery.sh .

WORKDIR /app

ENTRYPOINT celery -A etl.celery_app.celery worker -P gevent -c 3 --loglevel=info
