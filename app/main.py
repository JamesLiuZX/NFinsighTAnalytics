import dotenv
import os

from fastapi import FastAPI
from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions

from .auth.authenticate import router as auth_router

app = FastAPI()

app.include_router(auth_router)

# Initialise env values
async def read_env_values():
    DOTENV_PATH = os.getcwd() + "/app/.env"
    dotenv.load_dotenv(DOTENV_PATH)


# Connect to database, init env values
@app.on_event("startup")
async def connect_db():
    await read_env_values()
    app.cosmos_client = CosmosClient(
        os.getenv("DATABASE_URI"),
        os.getenv("DATABASE_KEY")
    )
    try:
        app.database = app.cosmos_client.get_database_client(os.getenv("DATABASE_NAME"))
    except exceptions.CosmosResourceNotFoundError:
        # Close app if cannot connect to db
        print("Cannot find database")
        exit(1)


