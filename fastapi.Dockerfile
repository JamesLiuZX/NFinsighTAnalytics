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

ADD ./etl/fastapi_app ./fastapi_app

WORKDIR /app

COPY ./scripts/api.sh .

EXPOSE 80

CMD ["uvicorn", "etl.fastapi_app.main:app", "--host", "0.0.0.0", "--port", "80"]

