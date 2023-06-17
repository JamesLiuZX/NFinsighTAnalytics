from enum import Enum

class GallopRankMetric(Enum):
    VOLUME = "eth_volume"
    SALES_COUNT = "sales_count"

class GallopRankingPeriod(Enum):
    ONE_DAY = "one_day"
    SEVEN_DAYS = "seven_days"
    THIRTY_DAYS = "thirty_days"
    NINETY_DAYS = "ninety_days"
    ALL_TIME = "all_time"


    