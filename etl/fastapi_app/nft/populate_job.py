from aiometer import run_all
from functools import partial
from fastapi import APIRouter
import time

from .gallop.api import floor_price, get_top_collections_gallop

from .gallop.gallop_types import (
    GallopRankMetric,
    GallopRankingPeriod,
)

from .gallop.response_types import GallopTopCollectionResponse

from .mnemonic.api import (
    get_collection_meta,
    get_collection_owners_count,
    get_collection_price_history,
    get_collection_sales_volume,
    get_collection_token_supply,
    get_top_collections,
)

from .mnemonic.mnemonic_types import (
    MnemonicQuery__RankType,
    MnemonicQuery__RecordsDuration,
)

from .mnemonic.response_types import (
    MnemonicTopCollectionsResponse,
    MnemonicCollectionsMetaResponse,
    MnemonicResponse__CollectionMeta__Metadata__Type,
)

from etl.celery_app.celery import (
    update_floor,
    update_owners,
    update_prices,
    update_sales,
    update_tokens,
    upsert_collection,
    # create_ranking,
    create_rankings,
    delete_rankings,
    CassandraDb,
)

router = APIRouter()

TIME_PERIOD_IN_SECONDS = 1
CASSANDRA_REQUESTS_PER_TIME_PERIOD = 20
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
3) Insert or update data points
    3.1) Insert 365 for new collections
    3.2) Refresh last two days for existing ones

Progress: Currently at 3, working on reducing throughput needed for this operation or handing off to another worker during
server downtime
"""


# WIP
@router.get("/nft/populate")
async def refresh_collections():
    # Get all existing collections
    session = CassandraDb.get_db_session()
    existing = session.execute(
        """
        SELECT address FROM collection
        """
    )
    existing_collections = set([collection.address for collection in existing])

    res = await update_collections_ranking()
    if res["collections"] is None:
        return "Rankings Update failed"

    new_collections = set(res["collections"]).difference(existing_collections)
    refresh_jobs = [
        partial(upsert_collection_data, collection)
        for collection in existing_collections
    ]

    for contract_address in new_collections:
        refresh_jobs.append(
            partial(
                upsert_collection_data,
                contract_address,
                # duration=MnemonicQuery__RecordsDuration.ONE_YEAR, # needed for new collections datapoints
            )
        )

    await run_all(refresh_jobs, max_at_once=1)
    await get_set_floor()


@router.get("/collections/get")
def get_collections():
    session = CassandraDb.get_db_session()
    res = session.execute(
        """
        SELECT address FROM collection
        """
    )
    return [c.address for c in res]


async def update_collections_ranking():
    out = set()
    delete_rankings.delay()

    # As there is a time delay in between each `create_ranking` invocation,
    # there is no need to rate limit the `get_top_collections` call.
    for rank in MnemonicQuery__RankType._member_map_:
        for duration in MnemonicQuery__RecordsDuration._member_map_:
            top_collections: MnemonicTopCollectionsResponse = await get_top_collections(
                MnemonicQuery__RankType[rank], MnemonicQuery__RecordsDuration[duration]
            )
            for ranking in top_collections["collections"]:
                out.add(ranking["collection"]["contractAddress"])

            create_rankings.apply_async(
                (
                    [
                        {
                            "contract_address": rank["collection"]["contractAddress"],
                            "value": rank["metricValue"],
                        }
                        for rank in top_collections["collections"]
                    ],
                    MnemonicQuery__RankType[rank]._value_,
                    MnemonicQuery__RecordsDuration[duration]._value_,
                )
            )
            time.sleep(CASSANDRA_DELAY)

    for rank in GallopRankMetric._member_map_:
        for duration in GallopRankingPeriod._member_map_:
            top_collections: GallopTopCollectionResponse = (
                await get_top_collections_gallop(
                    GallopRankMetric[rank],
                    GallopRankingPeriod[duration],
                )
            )
            for ranking in top_collections["response"]["leaderboard"]:
                out.add(ranking["collection_address"])

            create_rankings.apply_async(
                (
                    [
                        {
                            "contract_address": rank["collection_address"],
                            "value": rank["value"],
                        }
                        for rank in top_collections["response"]["leaderboard"]
                    ],
                    GallopRankMetric[rank]._value_,
                    GallopRankingPeriod[duration]._value_,
                )
            )
            time.sleep(CASSANDRA_DELAY)

    return {
        "count": out.__len__(),
        "collections": list(out),
    }


# WIP
@router.get("/upsert_collection_data")
async def upsert_collection_data(
    contract_address: str,
    duration: MnemonicQuery__RecordsDuration = MnemonicQuery__RecordsDuration.SEVEN_DAYS,
):
    jobs = [
        partial(get_collection_meta, contract_address),  # [0] - Meta
        partial(
            get_collection_price_history, contract_address, duration
        ),  # [1] - Price History
        partial(
            get_collection_sales_volume, contract_address, duration
        ),  # [2] - Sales Volume
        partial(
            get_collection_token_supply, contract_address, duration
        ),  # [3] - Token Supply
        partial(
            get_collection_owners_count, contract_address, duration
        ),  # [4] - Owners Count
    ]
    results = await run_all(jobs, max_per_second=MNEMONIC_REQUESTS_PER_TIME_PERIOD)

    metadata, prices, sales, tokens, owners = results
    await populate_collection_meta(contract_address, metadata)

    # update_prices.apply_async(args=(contract_address, prices))
    # update_sales.apply_async(args=(contract_address, sales))
    # update_tokens.apply_async(args=(contract_address, tokens))
    # update_owners.apply_async(args=(contract_address, owners))

    return results


async def populate_collection_meta(
    contract_address: str, meta_response: MnemonicCollectionsMetaResponse
):
    banner_image, image, ext_url, description = "", "", "", ""
    for meta in meta_response["metadata"]:
        if (
            meta["type"]
            == MnemonicResponse__CollectionMeta__Metadata__Type.BANNER_IMAGE._value_
        ):
            banner_image = meta["value"]
        elif (
            meta["type"]
            == MnemonicResponse__CollectionMeta__Metadata__Type.DESCRIPTION._value_
        ):
            description = meta["value"]
        elif (
            meta["type"]
            == MnemonicResponse__CollectionMeta__Metadata__Type.IMAGE._value_
        ):
            image = meta["value"]
        elif (
            meta["type"]
            == MnemonicResponse__CollectionMeta__Metadata__Type.EXT_URL._value_
        ):
            ext_url = meta["value"]

    # insert into database
    upsert_collection.apply_async(
        args=(
            contract_address,
            image,
            banner_image,
            meta_response["ownersCount"],
            meta_response["tokensCount"],
        ),
        kwargs={
            "name": meta_response["name"],
            "description": description,
            "external_url": ext_url,
            "sales_volume": meta_response["salesVolume"],
            "type": ",".join(list(meta_response["types"])),
        },
    )

@router.get("/floor_price/set")
async def get_set_floor():
    GALLOP_STEP_SIZE = 10
    session = CassandraDb.get_db_session()
    db_collections = session.execute("SELECT address FROM collection")
    collections = [c.address for c in db_collections]
    for i in range(0, len(collections), GALLOP_STEP_SIZE):
        gallop_response = await floor_price(collections[i : i + GALLOP_STEP_SIZE])
        if gallop_response["response"] is None:
            print(gallop_response["title"], gallop_response["detail"])
            continue

        floor_prices = gallop_response["response"]["collections"]
        update_floor.apply_async(kwargs=({
            "floor_prices": floor_prices
        }))
