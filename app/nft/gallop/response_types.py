from pydantic import BaseModel
from typing import List, TypedDict, Union


class Floor__MarketPlaceEntry(BaseModel):
    updated_at: str #DateTime string
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
    

