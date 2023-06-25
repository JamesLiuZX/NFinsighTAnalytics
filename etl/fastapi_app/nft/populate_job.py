from typing import Annotated
from aiometer import run_all
from functools import partial
from celery import Celery
from fastapi import APIRouter, Depends
import time

from etl.config import BROKER_URL, CELERY_APP_NAME, REDIS_URL
from etl.database import CassandraDb
from ..auth.auth_helpers import get_current_active_user
from ..auth.models import User

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


TIME_PERIOD_IN_SECONDS = 1
MNEMONIC_REQUESTS_PER_TIME_PERIOD = 30
MNEMONIC_DELAY = TIME_PERIOD_IN_SECONDS / MNEMONIC_REQUESTS_PER_TIME_PERIOD

router = APIRouter()

task_broker = Celery(CELERY_APP_NAME, broker=BROKER_URL, backend=REDIS_URL)


@router.get("/nft/refresh")
async def refresh_collections(
    current_user: Annotated[User, Depends(get_current_active_user)],
    num_days: str = "ONE_DAY",
):
    """
    The daily job that runs a refresh on the collections' data.

    Rankings across all metrics are updated, while metadata and time series are populated as well.
    """

    # 1. Update rankings, and get a set of all collections referenced
    # Get all existing collections
    existing_collections = set(get_collections())

    res = await update_collections_ranking()
    if res["collections"] is None:
        return "Rankings Update failed"

    existing_refresh_amount_map = {
        "ONE_DAY": MnemonicQuery__RecordsDuration.ONE_DAY,
        "SEVEN_DAYS": MnemonicQuery__RecordsDuration.SEVEN_DAYS,
    }

    # 2.1: Populate past ONE DAY of new data for existing collections
    new_collections = set(res["collections"]).difference(existing_collections)
    refresh_jobs = [
        partial(
            upsert_collection_data,
            current_user,
            collection,
            populate_data=True,
            duration=existing_refresh_amount_map[num_days],
        )
        for collection in existing_collections
    ]

    # 2.2: Populate 365 days of fresh data for new collections
    for contract_address in new_collections:
        refresh_jobs.append(
            partial(
                upsert_collection_data,
                current_user,
                contract_address,
                duration=MnemonicQuery__RecordsDuration.ONE_YEAR,  # needed for new collections datapoints
                populate_data=True,
            )
        )

    # 2.3: Refresh metadata - Each fires off requests to Mnemonic API, so only 1 can be fired at once
    await run_all(refresh_jobs, max_at_once=1)

    # 3: Refresh floor price
    await get_set_floor(current_user)


@router.get("/nft/populate_data")
async def populate_data(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Performs a bulk populate data points job of 365 daily points per collection for new database setup.
    """
    existing_collections = get_collections()
    jobs = [
        partial(
            upsert_collection_data,
            collection,
            duration=MnemonicQuery__RecordsDuration.ONE_YEAR,
            populate_data=True,
        )
        for collection in existing_collections
    ]
    await run_all(jobs, max_at_once=1)


@router.get("/collections/get")
def get_collections(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Returns all collection addresses currently in the database.
    """
    session = CassandraDb.get_db_session()
    res = session.execute(
        """
        SELECT address FROM collection
        """
    )
    return [c.address for c in res]


async def update_collections_ranking():
    """
    Updates the ranking tables within the database for both Gallop and Mnemonic APIs.
    """

    # 1: DELETE existing rankings
    out = set()
    task_broker.send_task("delete_rankings")

    # 2.1: Populate Mnemonic Rankings
    # As there is a time delay in between each `create_ranking` invocation,
    # there is no need to rate limit the `get_top_collections` call.
    for rank in MnemonicQuery__RankType._member_map_:
        for duration in MnemonicQuery__RecordsDuration._member_map_:
            top_collections: MnemonicTopCollectionsResponse = await get_top_collections(
                MnemonicQuery__RankType[rank], MnemonicQuery__RecordsDuration[duration]
            )
            for ranking in top_collections["collections"]:
                out.add(ranking["collection"]["contractAddress"])

            task_broker.send_task(
                "create_rankings",
                args=(
                    [
                        {
                            "contract_address": rank["collection"]["contractAddress"],
                            "value": rank["metricValue"],
                        }
                        for rank in top_collections["collections"]
                    ],
                    MnemonicQuery__RankType[rank]._value_,
                    MnemonicQuery__RecordsDuration[duration]._value_,
                ),
            )
            time.sleep(MNEMONIC_DELAY)

    # 2.2: Gallop Rankings
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

            task_broker.send_task(
                "create_rankings",
                args=(
                    [
                        {
                            "contract_address": rank["collection_address"],
                            "value": rank["value"],
                        }
                        for rank in top_collections["response"]["leaderboard"]
                    ],
                    GallopRankMetric[rank]._value_,
                    GallopRankingPeriod[duration]._value_,
                ),
            )
            time.sleep(MNEMONIC_DELAY)

    return {
        "count": out.__len__(),
        "collections": list(out),
    }


@router.get("/upsert_collection_data")
async def upsert_collection_data(
    current_user: Annotated[User, Depends(get_current_active_user)],
    contract_address: str,
    populate_data=False,
    duration: MnemonicQuery__RecordsDuration = MnemonicQuery__RecordsDuration.ONE_DAY,
):
    """
    Retrieves 5 sets of data:
    1. Metadata
    2. Price history
    3. Sales Volume
    4. Token Supply
    5. Owner Movements

    Runs all these requests at the Mnemonic API rate limit of 30 calls per second.
    """
    jobs = [
        partial(get_collection_meta, contract_address),  # [0] - Meta
    ]

    if populate_data:
        jobs += [
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

    # Update metadata in database.
    metadata = results[0]
    await populate_collection_meta(contract_address, metadata)

    # Update data points in database.
    if populate_data:
        _, prices, sales, tokens, owners = results
        task_broker.send_task("update_prices", args=(contract_address, prices))
        task_broker.send_task("update_sales", args=(contract_address, sales))
        task_broker.send_task("update_tokens", args=(contract_address, tokens))
        task_broker.send_task("update_owners", args=(contract_address, owners))

    return results


async def populate_collection_meta(
    contract_address: str, meta_response: MnemonicCollectionsMetaResponse
):
    """
    Populates the collection's metadata from the Mnemonic API response.
    """
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
    task_broker.send_task(
        "upsert_collection",
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
async def get_set_floor(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Sends collection addresses to the GALLOP API in batches of 10 as per their restriction.
    Retrieves a set of market place data floor prices, which is passed to a Celery worker to process.
    """
    GALLOP_STEP_SIZE = 10
    collections = get_collections()

    for i in range(0, len(collections), GALLOP_STEP_SIZE):
        gallop_response = await floor_price(collections[i : i + GALLOP_STEP_SIZE])

        if gallop_response["response"] is None:
            # WIP: Change to log
            print(gallop_response["title"], gallop_response["detail"])
            continue

        floor_prices = gallop_response["response"]["collections"]
        task_broker.send_task("update_floor", kwargs=({"floor_prices": floor_prices}))
