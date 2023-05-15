import dotenv
import os

from fastapi import FastAPI

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, management
from ssl import PROTOCOL_TLSv1_2, SSLContext, CERT_NONE

from .auth.authenticate import router as auth_router
from .nft.models import Collection, DataPoint, Ranking

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

    app.db_session = cluster.connect()
    app.db_connection = connection.register_connection('cluster1', session=app.db_session)

    management.sync_table(Collection, keyspaces=[os.environ['MAIN_KEYSPACE']], connections=[app.db_connection.name])
    management.sync_table(Ranking, keyspaces=[os.environ['MAIN_KEYSPACE']], connections=[app.db_connection.name])
    management.sync_table(DataPoint, keyspaces=[os.environ['MAIN_KEYSPACE']], connections=[app.db_connection.name])

