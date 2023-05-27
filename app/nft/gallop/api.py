import os
import json

from fastapi import APIRouter
from functools import lru_cache
from httpx import AsyncClient
from typing import List

from .gallop_types import GallopRankMetric, GallopRankingPeriod
from .response_types import GallopFloorResponse, GallopTopCollectionResponse


client = AsyncClient()
router = APIRouter()


@lru_cache(maxsize=1)
def get_header():
    return {
        'accept': 'application/json',
        'content-type': 'application/json',
        'x-api-key': os.environ['GALLOP_API_KEY']
    }


@router.get("/top_collections")
async def get_top_collections(
        rank: GallopRankMetric,
        rank_duration: GallopRankingPeriod,
        num_records: int = 100
) -> GallopTopCollectionResponse:
    payload = {
        "interval": rank_duration.value,
        "ranking_metric": rank.value,
        "page_size": num_records
    }
    url = f'https://api.prod.gallop.run/v1/analytics/eth/getLeaderBoard'
    header = get_header()
    response = await client.post(
        url,
        json=payload,
        headers=header
    )

    assert response.status_code == 200
    return response.json()


@router.post("/floor_price", response_model=GallopFloorResponse)
async def floor_price(collection_addresses: List[str]) -> GallopFloorResponse:
    assert len(collection_addresses) > 0
    url = "https://api.prod.gallop.run/v1/data/eth/getMarketplaceFloorPrice"
    payload = {
        "collection_address": collection_addresses
    }
    header = get_header()

    response = await client.post(url, headers=header, json=payload)

    assert response.status_code == 200
    return response.json()


