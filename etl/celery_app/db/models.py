from enum import Enum

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class Collection(Model):
    """
    The ORM creates definitions which are hard to work with.
    Therefore, create this table using the following CQL command:

    ```cql
    CREATE TABLE collection (
        address TEXT,
        name TEXT,
        type TEXT,
        tokens INT,
        owners INT,
        sales_volume DECIMAL,
        floor DECIMAL,
        image TEXT,
        banner_image TEXT,
        description TEXT,
        external_url TEXT,
        PRIMARY KEY (address)
    );
    ```
    """

    __table_name__ = "collection"
    address = columns.Text(primary_key=True, required=True)
    name = columns.Text(required=False)
    type = columns.Text(required=False)

    tokens = columns.Integer(required=True)
    owners = columns.Integer(required=True)
    sales_volume = columns.Decimal(required=True)
    floor = columns.Decimal(required=False)

    image = columns.Text(required=True)
    banner_image = columns.Text(required=True)
    description = columns.Text(required=False)
    external_url = columns.Text(required=False)


class RankingType(Enum):
    AVERAGE_PRICE = "1"
    MAX_PRICE = "2"
    SALES_COUNT = "3"
    SALES_VOLUME = "4"


class DurationType(Enum):
    ONE_DAY = "1"
    SEVEN_DAYS = "2"
    THIRTY_DAYS = "3"
    NINETY_DAYS = "4"
    ONE_YEAR = "5"
    ALL_TIME = "6"


class Ranking(Model):
    """
    The ORM creates definitions which are hard to work with.
    Therefore, create this table using the following CQL command:

    ```cql
    CREATE TABLE ranking (
        collection TEXT,
        duration TEXT,
        rank TEXT,
        value DECIMAL,
        PRIMARY KEY ((rank, duration), collection)
    );
    ```
    """

    __keyspace__ = "nf-main-keyspace"
    __connection__ = "cluster1"
    value = columns.Decimal(required=True)
    ranking = columns.Text(primary_key=True, required=True, partition_key=True)
    duration = columns.Text(primary_key=True, required=True, partition_key=True)
    collection = columns.Text(primary_key=True, required=True)


class DataPoint(Model):
    """
    The ORM creates definitions which are hard to work with.
    Therefore, create this table using the following CQL command:

    ```cql
    CREATE TABLE data_point (
        collection TEXT,
        time_stamp TIMESTAMP,
        average_price DECIMAL,
        max_price DECIMAL,
        min_price DECIMAL,
        sales_count DECIMAL,
        sales_volume DECIMAL,
        tokens_minted BIGINT,
        tokens_burned BIGINT,
        total_minted BIGINT,
        total_burned BIGINT,
        owners_count BIGINT,
        PRIMARY KEY (collection, time_stamp)
    ) WITH CLUSTERING ORDER BY (time_stamp ASC);
    ```
    """

    # One partition per collection
    collection = columns.Text(partition_key=True, primary_key=True, required=True)

    time_stamp = columns.DateTime(
        primary_key=True, required=True, clustering_order="ASC"
    )

    average_price = columns.Decimal()
    max_price = columns.Decimal()
    min_price = columns.Decimal()

    sales_count = columns.BigInt()
    sales_volume = columns.Decimal()

    tokens_minted = columns.BigInt()
    tokens_burned = columns.BigInt()
    total_minted = columns.BigInt()
    total_burned = columns.BigInt()

    owners_count = columns.BigInt()
