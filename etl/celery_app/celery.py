from decimal import Decimal
import time
import dotenv
import os
from ssl import CERT_NONE, PROTOCOL_TLSv1_2, SSLContext

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster
from cassandra.cqlengine import connection
from cassandra.policies import RoundRobinPolicy

from celery.app import Celery
from .celery_utils import format_timestring, or_else

from etl.fastapi_app.nft.mnemonic.response_types import (
    MnemonicOwnersSeries,
    MnemonicPriceSeries,
    MnemonicSalesVolumeSeries,
    MnemonicTokensSeries,
)

CASSANDRA_BATCH_DELAY = 2.5
BATCH_STEP = 30


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
        # db_connection = connection.register_connection("cluster1", session=db_session)

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
        if cls.db_connection is not None:
            return cls.db_session
        CassandraDb.c_init()
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
def create_rankings(
    rankings,
    rank_metric,
    duration,
):
    session = CassandraDb.get_db_session()
    statements = []
    for rank in rankings:
        statements.append(
            f"""
            INSERT INTO ranking (rank, duration, collection, value)
            VALUES ('{rank_metric}', '{duration}', '{rank['contract_address']}', {rank['value']})
            """
        )

    errors = []
    for i in range(0, len(statements), BATCH_STEP):
        try:
            session.execute(
                "BEGIN BATCH\n"
                + "\n".join(statements[i : i + BATCH_STEP])
                + "\nAPPLY BATCH"
            )
            time.sleep(CASSANDRA_BATCH_DELAY)
        except Exception as e:
            errors.append(e.__str__())
    return {
        "operation": f"{rank_metric}/{duration}",
        "status": "success" if not errors else errors,
    }


@app.task
def delete_rankings():
    session = CassandraDb.get_db_session()
    res = session.execute("TRUNCATE ranking")
    return {"operation": "ranking/delete/all"}


@app.task
def update_prices(contract_address: str, prices: MnemonicPriceSeries):
    """
    While this may be vulnerable to CQL injection,
    it is a temporary workaround to avoid the rate limits imposed by Cosmos.
    """
    session = CassandraDb.get_db_session()

    statement = []
    for point in prices["dataPoints"]:
        statement.append(
            f"""
            UPDATE data_point
               SET min_price = {or_else(point['min'])},
                   max_price = {or_else(point['max'])},
                   average_price = {or_else(point['avg'])}
            WHERE collection = '{contract_address}'
            AND time_stamp = '{format_timestring(point['timestamp'])}';
            """
        )

    errors = []
    for i in range(0, len(statement), BATCH_STEP):
        try:
            session.execute(
                "BEGIN BATCH"
                + "\n".join(statement[i : i + BATCH_STEP])
                + "\nAPPLY BATCH"
            )
            time.sleep(CASSANDRA_BATCH_DELAY)
        except Exception as e:
            errors.append(e.__str__())

    return {
        "operation": f"prices/{contract_address}",
        "status": "success" if not errors else errors,
    }


@app.task
def update_sales(contract_address: str, sales: MnemonicSalesVolumeSeries):
    session = CassandraDb.get_db_session()

    statement = []
    for point in sales["dataPoints"]:
        statement.append(
            f"""
            UPDATE data_point
               SET sales_count = {or_else(point['quantity'])},
                   sales_volume = {or_else(point['volume'])}
            WHERE collection = '{contract_address}'
            AND time_stamp = '{format_timestring(point['timestamp'])}';
            """
        )

    errors = []
    for i in range(0, len(statement), BATCH_STEP):
        try:
            session.execute(
                "BEGIN BATCH"
                + "\n".join(statement[i : i + BATCH_STEP])
                + "\nAPPLY BATCH"
            )
            time.sleep(CASSANDRA_BATCH_DELAY)
        except Exception as e:
            errors.append(e.__str__())

    return {
        "operation": f"sales/{contract_address}",
        "status": "success" if not errors else errors,
    }


@app.task
def update_tokens(contract_address: str, tokens: MnemonicTokensSeries):
    session = CassandraDb.get_db_session()

    statement = []
    for point in tokens["dataPoints"]:
        statement.append(
            f"""
            UPDATE data_point
               SET tokens_minted = {or_else(point['minted'])},
                   tokens_burned = {or_else(point['burned'])},
                   total_minted = {or_else(point['totalMinted'])},
                   total_burned = {or_else(point['totalBurned'])}
            WHERE collection = '{contract_address}'
            AND time_stamp = '{format_timestring(point['timestamp'])}';
            """
        )

    errors = []
    for i in range(0, len(statement), BATCH_STEP):
        try:
            session.execute(
                "BEGIN BATCH"
                + "\n".join(statement[i : i + BATCH_STEP])
                + "\nAPPLY BATCH"
            )
            time.sleep(CASSANDRA_BATCH_DELAY)
        except Exception as e:
            errors.append(e.__str__())

    return {
        "operation": f"tokens/{contract_address}",
        "status": "success" if not errors else errors,
    }


@app.task
def update_owners(contract_address: str, owners: MnemonicOwnersSeries):
    session = CassandraDb.get_db_session()

    statement = []
    for point in owners["dataPoints"]:
        statement.append(
            f"""
            UPDATE data_point
               SET owners_count = {or_else(point['count'])}
            WHERE collection = '{contract_address}'
            AND time_stamp = '{format_timestring(point['timestamp'])}';
            """
        )

    errors = []
    for i in range(0, len(statement), BATCH_STEP):
        try:
            session.execute(
                "BEGIN BATCH"
                + "\n".join(statement[i : i + BATCH_STEP])
                + "\nAPPLY BATCH"
            )
            time.sleep(CASSANDRA_BATCH_DELAY)
        except Exception as e:
            errors.append(e.__str__())

    return {
        "operation": f"owners/{contract_address}",
        "status": "success" if not errors else errors,
    }
