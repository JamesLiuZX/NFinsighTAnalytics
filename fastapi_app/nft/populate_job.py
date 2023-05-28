from aiometer import run_all
from cassandra.cqlengine.query import DoesNotExist
from functools import partial
from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

from .db.models import *
from .mnemonic.mnemonic_types import *
from .mnemonic.api import *


router = APIRouter()

REQUESTS_PER_TIME_PERIOD = 30
TIME_PERIOD_IN_SECONDS = 1

# WIP
@router.get("/nft/populate", response_class=ORJSONResponse)
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
    out = []
    for rank in MnemonicQuery__RankType._member_map_:
        for duration in MnemonicQuery__RecordsDuration._member_map_:
            # """
            top_collections = await get_top_collections(
                MnemonicQuery__RankType[rank],
                MnemonicQuery__RecordsDuration[duration]
            )
            out.append(top_collections)
            print(f'{rank}|{duration}\n{len(top_collections["collections"])} collections')
            # """
            # print(rank, duration)
    return ORJSONResponse(out)


async def get_collection_data(collection_address: str):
    """
    This operation is to be done daily for all collections in the rankings, and in the database.
    """
    
    try:
        collection = Collection.get(collection_address = collection_address)
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


