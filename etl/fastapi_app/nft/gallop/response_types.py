from typing import List, TypedDict, Union

from pydantic import BaseModel

from .gallop_types import GallopRankingPeriod, GallopRankMetric


class Floor__MarketPlaceEntry(BaseModel):
    updated_at: str  # DateTime string
    floor_price: Union[float, None]
    marketplace: str
    collection_id: str
    eth_floor_price: Union[float, None]
    usd_floor_price: Union[float, None]
    sub_collection_tag: str


class Floor__Collections(BaseModel):
    collection_address: str
    marketplaces: List[Floor__MarketPlaceEntry]


class Floor__Response(BaseModel):
    total_items: int
    total_pages: int
    page: int
    collections: List[Floor__Collections]


class GallopFloorResponse(TypedDict):
    status: int
    response: Floor__Response


class LeaderboardEntry(BaseModel):
    rank: int
    collection_address: str
    collection_name: str
    value: float
    type: Union[str, None]
    symbol: Union[str, None]


class TopCollectionResponse(BaseModel):
    total_items: int
    total_pages: int
    page: int
    interval: GallopRankingPeriod
    ranking_metric: GallopRankMetric
    leaderboard: List[LeaderboardEntry]


class GallopTopCollectionResponse(TypedDict):
    status: int
    response: TopCollectionResponse
