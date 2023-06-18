from aiometer import run_all
from functools import partial
from fastapi import APIRouter
import time

from .mnemonic.api import *
from .mnemonic.mnemonic_types import *
from .mnemonic.response_types import *

from ...celery_app.celery import upsert_collection, create_ranking, delete_rankings, CassandraDb

router = APIRouter()

TIME_PERIOD_IN_SECONDS = 1
CASSANDRA_REQUESTS_PER_TIME_PERIOD = 25
MNEMONIC_REQUESTS_PER_TIME_PERIOD = 30
CASSANDRA_DELAY = TIME_PERIOD_IN_SECONDS / CASSANDRA_REQUESTS_PER_TIME_PERIOD

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

# WIP
@router.get("/nft/populate")
async def update_collections_ranking():
    out = set()
    delete_rankings.delay()

    # As there is a time delay in between each `create_ranking` invocation,
    # there is no need to rate limit the `get_top_collections` call.
    for rank in MnemonicQuery__RankType._member_map_:
        for duration in MnemonicQuery__RecordsDuration._member_map_:
            top_collections: MnemonicTopCollectionsResponse = await get_top_collections(
                MnemonicQuery__RankType[rank],
                MnemonicQuery__RecordsDuration[duration]
            )
            for ranking in top_collections['collections']:
                out.add(ranking['collection']['contractAddress'])
                create_ranking.apply_async(
                    (
                        ranking['collection']['contractAddress'],
                        ranking['metricValue'],
                        MnemonicQuery__RankType[rank]._value_,
                        MnemonicQuery__RecordsDuration[duration]._value_
                    ))
                time.sleep(CASSANDRA_DELAY)
    
    return {
        'count': out.__len__(),
        'collections': list(out),
    }


# WIP
@router.get("/get_collection_data")
async def get_collection_data(contract_address: str, duration: MnemonicQuery__RecordsDuration = MnemonicQuery__RecordsDuration.SEVEN_DAYS): 
    jobs = [
        partial(get_collection_meta, contract_address),                       #[0] - Meta
        partial(get_collection_price_history, contract_address, duration),    #[1] - Price History
        partial(get_collection_sales_volume, contract_address, duration),     #[2] - Sales Volume
        partial(get_collection_token_supply, contract_address, duration),     #[3] - Token Supply
        partial(get_collection_owners_count, contract_address, duration)      #[4] - Owners Count
    ]
    results = await run_all(jobs, max_per_second=MNEMONIC_REQUESTS_PER_TIME_PERIOD)
    
    metadata, prices, sales, tokens, owners = results
    await populate_collection_meta(contract_address, metadata)
    
    return results


async def populate_collection_meta(
        contract_address: str, 
        meta_response: MnemonicCollectionsMetaResponse
):
    banner_image, image, ext_url, description = "", "", "", ""
    for meta in meta_response['metadata']:
        if meta['type'] == \
                MnemonicResponse__CollectionMeta__Metadata__Type.BANNER_IMAGE._value_:
            banner_image = meta['value']
        elif meta['type'] == \
                MnemonicResponse__CollectionMeta__Metadata__Type.DESCRIPTION._value_:
            description = meta['value']
        elif meta['type'] == \
                MnemonicResponse__CollectionMeta__Metadata__Type.IMAGE._value_:
            image = meta['value']
        elif meta['type'] == \
                MnemonicResponse__CollectionMeta__Metadata__Type.EXT_URL._value_:
            ext_url = meta['value']
    
    # insert into database
    upsert_collection.apply_async(
        args = (
            contract_address,
            image,
            banner_image,
            meta_response['ownersCount'],
            meta_response['tokensCount'],
        ),
        kwargs = {
            'name': meta_response['name'],
            'description': description,
            'external_url': ext_url,
            'sales_volume': meta_response['salesVolume'],
            'type': ",".join(list(meta_response['types']))
        }
    )
