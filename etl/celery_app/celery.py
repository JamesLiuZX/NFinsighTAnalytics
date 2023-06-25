from decimal import Decimal

from celery.app import Celery
from celery.signals import worker_process_init

from .celery_utils import format_gallop_timestamp, format_timestring, or_else
from .mnemonic.response_types import (
    MnemonicOwnersSeries,
    MnemonicPriceSeries,
    MnemonicSalesVolumeSeries,
    MnemonicTokensSeries,
)

from etl.config import BROKER_URL, CELERY_APP_NAME, REDIS_URL
from etl.database import CassandraDb

BATCH_STEP = 30

worker_process_init.connect(CassandraDb.c_init)
app = Celery(CELERY_APP_NAME, broker=BROKER_URL, backend=REDIS_URL)

###############################################################################
"""
COLLECTIONS
"""


@app.task(name="upsert_collection")
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


###############################################################################
"""
RANKINGS
"""


@app.task(name="get_rankings")
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
        #   'collection' : '', # row.collection
        #   'duration': '',
        #   'rank': '',
        #   'value': Decimal()
        # }
        pass


@app.task(name="create_ranking")
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
            "message": e.__str__(),
        }


@app.task(name="create_rankings")
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
            # time.sleep(CASSANDRA_BATCH_DELAY)
        except Exception as e:
            errors.append(e.__str__())
    return {
        "operation": f"{rank_metric}/{duration}",
        "status": "success" if not errors else errors,
    }


@app.task(name="delete_rankings")
def delete_rankings():
    session = CassandraDb.get_db_session()
    error = ""
    try:
        res = session.execute("TRUNCATE ranking")
    except Exception as e:
        error = e.__str__()

    return {
        "operation": "ranking/delete/all",
        "status": "success" if not error else ",\n".join(errors),
    }


###############################################################################
"""
DATAPOINTS
"""


@app.task(name="update_prices")
def update_prices(contract_address: str, prices: MnemonicPriceSeries):
    """
    While this may be vulnerable to CQL injection,
    it is a temporary workaround to avoid the rate limits on the database.
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
            # time.sleep(CASSANDRA_BATCH_DELAY) # Time delay for Cosmo
        except Exception as e:
            errors.append(e.__str__())

    return {
        "operation": f"prices/{contract_address}",
        "status": "success" if not errors else ",\n".join(errors),
    }


@app.task(name="update_sales")
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
            # time.sleep(CASSANDRA_BATCH_DELAY) # Time delay for Cosmo
        except Exception as e:
            errors.append(e.__str__())

    return {
        "operation": f"sales/{contract_address}",
        "status": "success" if not errors else ",\n".join(errors),
    }


@app.task(name="update_tokens")
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
            # time.sleep(CASSANDRA_BATCH_DELAY) # Time delay for Cosmo
        except Exception as e:
            errors.append(e.__str__())

    return {
        "operation": f"tokens/{contract_address}",
        "status": "success" if not errors else ",\n".join(errors),
    }


@app.task(name="update_owners")
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
            # time.sleep(CASSANDRA_BATCH_DELAY) # Time delay for Cosmo
        except Exception as e:
            errors.append(e.__str__())

    return {
        "operation": f"owners/{contract_address}",
        "status": "success" if not errors else ",\n".join(errors),
    }


###############################################################################
"""
COLLECTIONS.FLOOR
"""


@app.task(name="update_floor")
def update_floor(floor_prices=[]):
    session = CassandraDb.get_db_session()
    statement = []
    for floor_price_listing in floor_prices:
        contract_address = floor_price_listing["collection_address"]

        latest_updated_at = format_gallop_timestamp(
            floor_price_listing["marketplaces"][0]["updated_at"],
        )
        min_floor = or_else(
            floor_price_listing["marketplaces"][0]["floor_price"], default_value=0
        )
        for i in range(1, len(floor_price_listing["marketplaces"])):
            new_listing = floor_price_listing["marketplaces"][i]
            new_timestamp = format_gallop_timestamp(
                new_listing["updated_at"],
            )
            new_floor = or_else(new_listing["floor_price"], default_value=0)
            if not new_floor:
                pass
            elif (new_timestamp > latest_updated_at) or (new_floor and not min_floor):
                min_floor = new_floor

        statement.append(
            f"""
            UPDATE collection
               SET floor = {min_floor}
            WHERE address = '{contract_address}';
            """
        )

    try:
        session.execute(
            "BEGIN UNLOGGED BATCH\n" + "\n".join(statement) + "\nAPPLY BATCH"
        )
        return {
            "operation": f"floor/{len(floor_prices)}\n[\n    "
            + ",\n    ".join([fpl["collection_address"] for fpl in floor_prices])
            + "\n]",
            "status": "success",
        }
    except Exception as e:
        return {
            "operation": f"floor/{len(floor_prices)}\n[\n    "
            + ",\n    ".join([fpl["collection_address"] for fpl in floor_prices])
            + "\n]",
            "status": "failed",
            "message": e.__str__(),
        }
