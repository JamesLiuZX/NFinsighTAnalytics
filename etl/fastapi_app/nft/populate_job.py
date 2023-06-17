from aiometer import run_all
from cassandra.cqlengine.query import DoesNotExist
from functools import partial
from fastapi import APIRouter
from fastapi.responses import ORJSONResponse
import time

from .mnemonic.mnemonic_types import *
from .mnemonic.api import *

from ...celery_app.celery import create_collection, create_ranking, delete_rankings

router = APIRouter()

REQUESTS_PER_TIME_PERIOD = 30
TIME_PERIOD_IN_SECONDS = 1

# WIP
@router.get("/nft/populate")
async def update_collections():
    """
    Plan:
    Pre: Get set of all collections in DB
    1) Get Rankings
      1.1) Fire batch job to update rankings
      1.2) For every ranking, fire off an upsert collection
    2) Get all collections
      2.1) Fire off batched queries to Gallop to query floor price
      2.2) Batch update all floor prices 

    Progress: Currently at 1.2, each upsert collection coroutine can be handed off to a background worker
    - get_data operation done
    - Now, need to optimise an upsert_data operation to act on the returned data.
    """
    out = set()
    delete_rankings.delay()
    for rank in MnemonicQuery__RankType._member_map_:
        for duration in MnemonicQuery__RecordsDuration._member_map_:
            # """
            top_collections: MnemonicTopCollectionsResponse = await get_top_collections(
                # MnemonicQuery__RankType.AVG_PRICE,
                # MnemonicQuery__RecordsDuration.ONE_DAY
                MnemonicQuery__RankType[rank],
                MnemonicQuery__RecordsDuration[duration]
            )
            for ranking in top_collections['collections']:
                out.add(ranking['collection']['contractAddress'])
                create_ranking.apply_async(
                    (
                        ranking['collection']['contractAddress'],
                        ranking['metricValue'],
                        # MnemonicQuery__RankType.AVG_PRICE._value_,
                        # MnemonicQuery__RecordsDuration.ONE_DAY._value_
                        MnemonicQuery__RankType[rank]._value_,
                        MnemonicQuery__RecordsDuration[duration]._value_
                    ))
                time.sleep(0.05)
                
    return {
        'count': out.__len__(),
        'collections': list(out)
    }

@router.get("/nft/rankings/delete")
async def delete_rankings_route():
    res = delete_rankings.delay()


async def get_collection_data(collection_address: str):
    """
    This operation is to be done daily for all collections in the rankings, and in the database.
    """
    
    try:
        return populate_collection_data(collection_address)  # If it exists, only update past 7 days of data
    except DoesNotExist:
        return populate_collection_data(collection_address, MnemonicQuery__RecordsDuration.ONE_YEAR)


# WIP
@router.get("/populate_collection_data")
async def populate_collection_data(collection_address: str, duration: MnemonicQuery__RecordsDuration = MnemonicQuery__RecordsDuration.SEVEN_DAYS): 
    jobs = [
        partial(get_collection_meta, collection_address),                       #[0] - Meta
        partial(get_collection_price_history, collection_address, duration),    #[1] - Price History
        partial(get_collection_sales_volume, collection_address, duration),     #[2] - Sales Volume
        partial(get_collection_token_supply, collection_address, duration),     #[3] - Token Supply
        partial(get_collection_owners_count, collection_address, duration)      #[4] - Owners Count
    ]

    results = await run_all(jobs, max_per_second=REQUESTS_PER_TIME_PERIOD)
    return ORJSONResponse(results)


