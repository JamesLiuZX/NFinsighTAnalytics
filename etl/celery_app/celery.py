from decimal import Decimal
import dotenv
import os
from ssl import CERT_NONE, PROTOCOL_TLSv1_2, SSLContext

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.cqlengine import connection
from cassandra.policies import RoundRobinPolicy

from celery.app import Celery


class CassandraDb:
    db_session = None
    db_connection = None
    db_prepared = {}

    @classmethod
    def c_init(cls):
        """
        Maintain a singleton connection. May be converted to a connection pool in the future.
        """

        DOTENV_PATH = os.getcwd() + "/etl/celery_app/.env"
        dotenv.load_dotenv(DOTENV_PATH)

        ssl_context = SSLContext(PROTOCOL_TLSv1_2)
        ssl_context.verify_mode = CERT_NONE
        auth_provider = PlainTextAuthProvider(
            username=os.environ["DATABASE_USERNAME"],
            password=os.environ["DATABASE_PASSWORD"],
        )

        cluster = Cluster(
            [os.environ["DATABASE_CONTACT_POINT"]],
            port=int(os.environ["DATABASE_PORT"]),
            auth_provider=auth_provider,
            ssl_context=ssl_context,
            load_balancing_policy=RoundRobinPolicy(),
            protocol_version=4,
        )

        # Authenticate and save session for reuse
        db_session = cluster.connect("nf-main-keyspace")
        db_connection = connection.register_connection("cluster1", session=db_session)

        cls.db_session = db_session
        cls.db_connection = db_connection

    @classmethod
    def get_db_connection(cls, **kwargs):
        if cls.db_connection is not None:
            return cls.db_connection
        CassandraDb.c_init()
        return cls.db_connection

    @classmethod
    def get_db_session(cls, **kwargs):
        connection = CassandraDb.get_db_connection()
        return cls.db_session


BROKER_URL = "amqp://localhost"
REDIS_URL = "redis://localhost"


app = Celery(__name__, broker=BROKER_URL, backend=REDIS_URL)


@app.task
def upsert_collection(
    contract_address: str,
    image: str,
    banner_image: str,
    owners: int,
    tokens: int,
    name: str = None,
    description: str = None,
    external_url: str = None,
    sales_volume: str = None,
    type: str = None,
):
    session = CassandraDb.get_db_session()
    q = session.prepare(
        f"""
        UPDATE collection
        SET image = ?,
            banner_image = ?,
            owners = ?,
            tokens = ?,
            name = ?,
            description = ?,
            external_url = ?,
            sales_volume = ?,
            type = ?
        WHERE address = ?
        """
    )

    try:
        session.execute(
            q,
            [
                image,
                banner_image,
                int(owners),
                int(tokens),
                name,
                description,
                external_url,
                Decimal(sales_volume),
                type,
                contract_address,
            ],
        )
        return {
            "operation": f"collection/upsert/{contract_address}",
            "status": "success",
        }
    except Exception as e:
        return {
            "operation": f"collection/upsert/{contract_address}",
            "status": "failed",
            "message": e.__str__(),
        }


@app.task
def get_rankings():
    session = CassandraDb.get_db_session()

    res = session.execute(
        """
        SELECT *
        FROM ranking
        WHERE rank = 'avg_price'
          AND duration = 'DURATION_1_DAY';
        """
    )

    for row in res:
        # row: {
        #   'collection' : '',
        #   'duration': '',
        #   'rank': '',
        #   'value': Decimal()
        # }
        pass


@app.task
def upsert_collections(collections):
    pass


@app.task
def create_ranking(
    contract_address: str, metric_value: str, rank_type: str, rank_duration: str
):
    session = CassandraDb.get_db_session()

    statement = session.prepare(
        """
        INSERT INTO ranking (rank, duration, collection, value)
            VALUES (?, ?, ?, ?)
        """
    )
    try:
        session.execute(
            statement,
            [rank_type, rank_duration, contract_address, Decimal(value=metric_value)],
        )
        return {
            "operation": f"rank/{rank_type}/{rank_duration}/{contract_address}",
            "status": "success",
        }
    except Exception as e:
        return {
            "operation": f"rank/{rank_type}/{rank_duration}/{contract_address}",
            "status": "failed",
        }


@app.task
def delete_rankings():
    session = CassandraDb.get_db_session()
    res = session.execute("TRUNCATE ranking")
    return res


@app.task
def upsert_datapoint(datapoint):
    pass


@app.task
def upsert_datapoints(datapoints):
    pass
