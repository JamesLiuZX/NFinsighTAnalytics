from aiometer import run_all
from functools import partial
from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

from .mnemonic.mnemonic_types import *
from .mnemonic.api import *


router = APIRouter()

REQUESTS_PER_TIME_PERIOD = 30
TIME_PERIOD_IN_SECONDS = 1

# WIP
@router.get("/nft/populate", response_class=ORJSONResponse)
async def update_rankings():
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


# WIP
@router.get("/populate_collection")
async def populate_collection(collection_address: str): 
    duration = MnemonicQuery__RecordsDuration.SEVEN_DAYS

    jobs = [
        partial(get_collection_meta, collection_address),
        partial(get_collection_price_history, collection_address, duration),
        partial(get_collection_sales_volume, collection_address, duration),
        partial(get_collection_sales_volume, collection_address, duration),
        partial(get_collection_owners_count, collection_address, duration)
    ]

    results = await run_all(jobs, max_per_second=30)
    return ORJSONResponse(results)


