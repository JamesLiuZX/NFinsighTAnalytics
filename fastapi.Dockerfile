# Compile Image
FROM python:3.9-slim-bullseye AS compile-image

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential musl-dev libpq-dev gcc

RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

COPY ./requirements.txt .

RUN pip install -r requirements.txt

# Build image
FROM python:3.9-slim-bullseye AS build-image

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev

COPY --from=compile-image /opt/venv /opt/venv

# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH" \
  PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/etl

COPY ./etl/config.py .
COPY ./etl/database.py .
COPY ./etl/.env .
COPY ./etl/secure-connect-*.zip .

ADD ./etl/fastapi_app ./fastapi_app

WORKDIR /app

EXPOSE 80

CMD ["uvicorn", "etl.fastapi_app.main:app", "--host", "0.0.0.0", "--port", "80"]

