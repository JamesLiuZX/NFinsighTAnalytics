import os
from ssl import CERT_NONE, PROTOCOL_TLSv1_2, SSLContext

import dotenv
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, management
from cassandra.policies import RoundRobinPolicy

from celery import Task
from celery.app import Celery
from celery.signals import worker_process_init, beat_init

from .db.models import Collection, DataPoint, Ranking


class DbTask(Task):
    db_session = None
    db_connection = None

    @classmethod
    def cassandra_init(cls):
        """
        Maintain a singleton connection. May be converted to a connection pool in the future.
        """

        DOTENV_PATH = os.getcwd() + "/celery_app/.env"
        dotenv.load_dotenv(DOTENV_PATH)

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
            ssl_context=ssl_context,
            load_balancing_policy=RoundRobinPolicy(),
            protocol_version=4
        )

        # Authenticate and save session for reuse
        db_session = cluster.connect()
        db_connection = connection.register_connection(
            'cluster1',
            session=db_session
            )

        # Sync Schema
        management.sync_table(
            Collection,
            keyspaces=[os.environ['MAIN_KEYSPACE']],
            connections=[db_connection.name]
            )
        management.sync_table(
            Ranking,
            keyspaces=[os.environ['MAIN_KEYSPACE']],
            connections=[db_connection.name]
            )
        management.sync_table(
            DataPoint,
            keyspaces=[os.environ['MAIN_KEYSPACE']],
            connections=[db_connection.name]
            )
        
        cls.db_session = db_session
        cls.db_connection = db_connection

    @classmethod
    def get_db(cls, **kwargs):
        if cls.db_connection is not None:
            return cls.db_connection
        DbTask.cassandra_init()
        return cls.db_connection

    def get_db_connection(self):
        return DbTask.get_db()

BROKER_URL = "amqp://localhost"
REDIS_URL = "redis://localhost"

worker_process_init.connect(DbTask.get_db)
beat_init.connect(DbTask.get_db)

app = Celery(__name__, broker=BROKER_URL, backend=REDIS_URL)


@app.task(base=DbTask, bind=True)
def create_collection(self: DbTask, collection):
    connection = self.get_db_connection() # Test Cassandra connectivity
    Collection.objects.all()


@app.task(base=DbTask, bind=True)
def upsert_collections(self, collections):
    pass


@app.task(base=DbTask, bind=True)
def create_ranking(self, ranking):
    pass


@app.task(base=DbTask, bind=True)
def upsert_datapoint(self, datapoint):
    pass


@app.task(base=DbTask, bind=True)
def upsert_datapoints(self, datapoints):
    pass


@app.task(base=DbTask, bind=True)
def delete_rankings(self, ):
    pass
