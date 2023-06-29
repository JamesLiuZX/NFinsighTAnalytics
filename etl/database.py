import os
from dotenv import load_dotenv
from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster

from psycopg2 import pool
from psycopg2.extras import execute_batch

# from ssl import CERT_NONE, PROTOCOL_TLSv1_2, SSLContext
# from cassandra.cqlengine import connection
# from cassandra.policies import RoundRobinPolicy


load_dotenv()

CASSANDRA_CLIENT_ID = os.environ["ASTRA_CLIENT_ID"]
CASSANDRA_CLIENT_SECRET = os.environ["ASTRA_CLIENT_SECRET"]
CASSANDRA_DB_NAME = os.environ["ASTRA_DB_NAME"]
CASSANDRA_KEYSPACE = os.environ["ASTRA_KEYSPACE"]

CLOUD_CONFIG = {
    "secure_connect_bundle": f"{os.getcwd()}/etl/secure-connect-{CASSANDRA_DB_NAME}.zip"
}

AUTH_PROVIDER = PlainTextAuthProvider(CASSANDRA_CLIENT_ID, CASSANDRA_CLIENT_SECRET)

COSMOS_KEYSPACE = "nf-main-keyspace"


class CassandraDb:
    db_session = None
    db_connection = None

    @classmethod
    def c_init(cls, **kwargs):
        """
        Maintain a singleton connection. May be converted to a connection pool in the future.
        """

        # DOTENV_PATH = os.getcwd() + "/etl/celery_app/.env"
        # dotenv.load_dotenv(DOTENV_PATH)

        # ssl_context = SSLContext(PROTOCOL_TLSv1_2)
        # ssl_context.verify_mode = CERT_NONE
        # auth_provider = PlainTextAuthProvider(
        #     username=os.environ["DATABASE_USERNAME"],
        #     password=os.environ["DATABASE_PASSWORD"],
        # )

        # cluster = Cluster(
        #     [os.environ["DATABASE_CONTACT_POINT"]],
        #     port=int(os.environ["DATABASE_PORT"]),
        #     auth_provider=auth_provider,
        #     ssl_context=ssl_context,
        #     load_balancing_policy=RoundRobinPolicy(),
        #     protocol_version=4,
        # )
        # db_session = cluster.connect(COSMOS_KEYSPACE)
        # db_connection = connection.register_connection("cluster1", session=db_session)

        cluster = Cluster(
            cloud=CLOUD_CONFIG, auth_provider=AUTH_PROVIDER, protocol_version=4
        )

        db_session = cluster.connect(CASSANDRA_KEYSPACE)
        cls.db_session = db_session
        # cls.db_connection = db_connection

    # @classmethod
    # def get_db_connection(cls, **kwargs):
    #     if cls.db_connection is not None:
    #         return cls.db_connection
    #     CassandraDb.c_init()
    #     return cls.db_connection

    @classmethod
    def get_db_session(cls, **kwargs):
        if cls.db_session is not None:
            return cls.db_session
        CassandraDb.c_init()
        return cls.db_session


PG_PORT = os.environ["PG_PORT"]
PG_URI = os.environ["PG_CONN_STRING"]
PG_PASSWORD = os.environ["PG_PASSWORD"]
PG_CONN_STRING = f"postgres://postgres:{PG_PASSWORD}@{PG_URI}:{PG_PORT}/postgres"


class PostgresSearchDb:
    DB_POOL = None

    @classmethod
    def get_pool(cls):
        if cls.DB_POOL is None:
            cls.DB_POOL = pool.ThreadedConnectionPool(
                0,  # Min Connection
                4,  # Max Connection (4 Threads)
                user="postgres",
                password=PG_PASSWORD,
                host=PG_URI,
                database="postgres",
            )
        return cls.DB_POOL

    @classmethod
    def execute_query_batch(cls, query, params):
        pool = cls.get_pool()
        connection = pool.getconn()
        if connection:
            cursor = connection.cursor()
            execute_batch(cursor, query, params)
            cursor.close()
            connection.commit()
            pool.putconn(connection)
        else:
            print("Unable to get connection")
    
    @classmethod
    def execute_query(cls, query):
        pool = cls.get_pool()
        connection = pool.getconn()
        if connection:
            cursor = connection.cursor()
            cursor.execute(query)
            cursor.close()
            connection.commit()
            pool.putconn(connection)
        else:
            print("Unable to get connection")
    
