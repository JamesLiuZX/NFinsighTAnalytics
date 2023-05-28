import os
from ssl import CERT_NONE, PROTOCOL_TLSv1_2, SSLContext

import dotenv
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, management
from fastapi import FastAPI

from .auth.authenticate import router as auth_router
from .nft.db.models import Collection, DataPoint, Ranking
from .nft.gallop.api import router as gallop_router
from .nft.mnemonic.api import router as mnemonic_router
from .nft.populate_job import router as populate_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(gallop_router, prefix="/gallop")
app.include_router(mnemonic_router, prefix="/mnemonic")
app.include_router(populate_router)


# Initialise env values
async def read_env_values():
    DOTENV_PATH = os.getcwd() + "/fastapi_app/.env"
    dotenv.load_dotenv(DOTENV_PATH)


# Connect to database, init env values
@app.on_event("startup")
async def connect_db():
    await read_env_values()
    
    # Create Auth context for DB
    ssl_context = SSLContext(PROTOCOL_TLSv1_2)
    ssl_context.verify_mode = CERT_NONE
    auth_provider = PlainTextAuthProvider(
        username=os.environ['DATABASE_USERNAME'],
        password=os.environ['DATABASE_PASSWORD']
    )

    cluster = Cluster(
        [os.environ['DATABASE_CONTACT_POINT']],
        port=int(os.environ['DATABASE_PORT']),
        auth_provider=auth_provider,
        ssl_context=ssl_context
    )

    # Authenticate and save session for reuse
    app.db_session = cluster.connect()
    app.db_connection = connection.register_connection(
        'cluster1',
        session=app.db_session
        )

    # Sync Schema
    management.sync_table(
        Collection,
        keyspaces=[os.environ['MAIN_KEYSPACE']],
        connections=[app.db_connection.name]
        )
    management.sync_table(
        Ranking,
        keyspaces=[os.environ['MAIN_KEYSPACE']],
        connections=[app.db_connection.name]
        )
    management.sync_table(
        DataPoint,
        keyspaces=[os.environ['MAIN_KEYSPACE']],
        connections=[app.db_connection.name]
        )
