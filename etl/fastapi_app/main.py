import os
from ssl import CERT_NONE, PROTOCOL_TLSv1_2, SSLContext

import dotenv
from fastapi import FastAPI

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, management
from cassandra.policies import RoundRobinPolicy

from .auth.authenticate import router as auth_router
from .nft.gallop.api import router as gallop_router
from .nft.mnemonic.api import router as mnemonic_router
from .nft.populate_job import router as populate_router

from ..celery_app.db.models import Collection, Ranking, DataPoint

app = FastAPI()

app.include_router(auth_router)
app.include_router(gallop_router, prefix="/gallop")
app.include_router(mnemonic_router, prefix="/mnemonic")
app.include_router(populate_router)


# Initialise env values
async def read_env_values():
    DOTENV_PATH = os.getcwd() + "/etl/fastapi_app/.env"
    dotenv.load_dotenv(DOTENV_PATH)


# Connect to database, init env values
@app.on_event("startup")
async def connect_db():
    await read_env_values()
