import uuid

from enum import Enum

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model

class Collection(Model):
    __table_name__ = 'collection'
    id             = columns.UUID(primary_key=True, default=uuid.uuid4)
    address        = columns.Text(required=True,)
    name           = columns.Text(required=False)
    type           = columns.Text(required=False)

    tokens         = columns.Integer(required=True)
    owners         = columns.Integer(required=True)
    sales_volume   = columns.Decimal(required=True)
    floor          = columns.Decimal(required=False)

    image          = columns.Text(required=True)
    banner_image   = columns.Text(required=True)
    description    = columns.Text(required=False)
    external_url   = columns.Text(required=False)


class RankingType(Enum):
    AVERAGE_PRICE   = "1"
    MAX_PRICE       = "2"
    SALES_COUNT     = "3"
    SALES_VOLUME    = "4"


class DurationType(Enum):
    ONE_DAY         = "1"
    SEVEN_DAYS      = "2"
    THIRTY_DAYS     = "3"
    NINETY_DAYS     = "4"
    ONE_YEAR        = "5"
    ALL_TIME        = "6"


class Ranking(Model):
    id          = columns.UUID(primary_key=True, default=uuid.uuid4)
    ranking     = columns.Text(required=True, partition_key=True) 
    duration    = columns.Text(required=True, partition_key=True)

    collection  = columns.Text(required=True)
    value       = columns.Decimal(required=True)


class DataPoint(Model):
    id              = columns.UUID(primary_key=True, default=uuid.uuid4)
    
    #One partition per collection
    collection      = columns.Text(partition_key=True, primary_key=True, required=True) 
    
    time_stamp       = columns.DateTime(primary_key=True, required=True)

    average_price   = columns.Decimal()
    max_price       = columns.Decimal()
    min_price       = columns.Decimal()
    
    sales_count     = columns.BigInt()
    sales_volume    = columns.Decimal()

    tokens_minted   = columns.BigInt()
    tokens_burned   = columns.BigInt()
    total_minted    = columns.BigInt()
    total_burned    = columns.BigInt()

    owners_count    = columns.BigInt()


