from datetime import datetime
from typing import List, TypedDict

class TimeSeriesPoint(TypedDict):
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


# TypedDict does not support generics in Python 3.9
class MnemonicOwnersSeries(TypedDict):
    dataPoints: List[MnemonicCollection__OwnerHistory]


class MnemonicPriceSeries(TypedDict):
    dataPoints: List[MnemonicCollection__PriceHistory]


class MnemonicSalesVolumeSeries(TypedDict):
    dataPoints: List[MnemonicCollection__SalesHistory]


class MnemonicTokensSeries(TypedDict):
    dataPoints: List[MnemonicCollection__TokenHistory]
