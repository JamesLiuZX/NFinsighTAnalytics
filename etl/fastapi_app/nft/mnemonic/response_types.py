from enum import Enum
from pydantic import BaseModel
from pydantic.generics import GenericModel
from typing import Generic, List, TypeVar, TypedDict
from datetime import datetime


DataT = TypeVar('DataT')

class MnemonicTopCollections__Collection__CollectionObject(BaseModel):
    contractAddress: str
    name: str


class MnemonicTopCollections__Collection(BaseModel):
    collection: MnemonicTopCollections__Collection__CollectionObject
    metricValue: str


class MnemonicTopCollectionsResponse(TypedDict):
    collections: List[MnemonicTopCollections__Collection]


class MnemonicResponse__CollectionType(Enum):
    UNKNOWN         = "TOKEN_TYPE_UNKNOWN"
    ERC20           = "TOKEN_TYPE_ERC20"
    ERC721          = "TOKEN_TYPE_ERC721"
    ERC1155         = "TOKEN_TYPE_ERC1155"
    ERC721_LEGACY   = "TOKEN_TYPE_ERC721_LEGACY"
    CRYPTOPUNKS     = "TOKEN_TYPE_CRYPTOPUNKS"


class MnemonicResponse__CollectionMeta__Metadata__Type(Enum):
    BANNER_IMAGE    = "TYPE_BANNER_IMAGE_URL"
    DESCRIPTION     = "TYPE_DESCRIPTION"
    IMAGE           = "TYPE_IMAGE_URL"
    DISCORD         = "TYPE_DISCORD_URL"
    EXT_URL         = "TYPE_EXTERNAL_URL"
    MEDIUM_USN      = "TYPE_MEDIUM_USERNAME"
    TELE_USN        = "TYPE_TELEGRAM_URL"
    TWITTER_USN     = "TYPE_TWITTER_USERNAME"
    INSTA_USN       = "TYPE_INSTAGRAM_USERNAME"
    WIKI_USN        = "TYPE_WIKI_URL"


class MnemonicResponse__CollectionMeta__MetadataItem(TypedDict):
    type: MnemonicResponse__CollectionMeta__Metadata__Type
    value: str


class MnemonicCollectionsMetaResponse(TypedDict):
    name: str
    types: List[MnemonicResponse__CollectionType]
    tokensCount: str
    ownersCount: str
    salesVolume: str
    metadata: List[MnemonicResponse__CollectionMeta__MetadataItem]


class TimeSeriesPoint(BaseModel):
    timestamp: datetime


class MnemonicCollection__PriceHistory(TimeSeriesPoint):
    min: str
    max: str
    avg: str


class MnemonicCollection__SalesHistory(TimeSeriesPoint):
    quantity: str
    volume: str


class MnemonicCollection__TokenHistory(TimeSeriesPoint):
    minted: str
    burned: str
    totalMinted: str
    totalBurned: str


class MnemonicCollection__OwnerHistory(TimeSeriesPoint):
    count: str


class MnemonicCollectionHistoryResponse(GenericModel, Generic[DataT]):
    dataPoints: List[DataT]


