from enum import Enum


class MnemonicQuery__DataTimeGroup(Enum):
    # UNSPECIFIED   = "GROUP_BY_PERIOD_UNSPECIFIED"
    FIFTEEN_MIN   = "GROUP_BY_PERIOD_15_MINUTES"
    ONE_HR        = "GROUP_BY_PERIOD_1_HOUR"
    ONE_DAY       = "GROUP_BY_PERIOD_1_DAY"


class MnemonicQuery__RecordsDuration(Enum):
    ONE_DAY         = "DURATION_1_DAY"
    SEVEN_DAYS      = "DURATION_7_DAYS"
    THIRTY_DAYS     = "DURATION_30_DAYS"
    ONE_YEAR        = "DURATION_365_DAYS"


class MnemonicQuery__Marketplaces(Enum):
    OPENSEA         = "MARKETPLACE_ID_OPENSEA"
    LOOKSRARE       = "MARKETPLACE_ID_LOOKSRARE"
    CRYPTORUNKS     = "MARKETPLACE_ID_CRYPTOPUNKS"
    SUPERRARE       = "MARKETPLACE_ID_SUPERRARE"


class MnemonicQuery__RankType(Enum):
    AVG_PRICE = "avg_price"
    MAX_PRICE = "max_price"
    # SALES_VOLUME = "sales_volume"     # Gallop gives more accurate metrics
    # SALES_COUNT = "sales_quantity"    # Gallop gives more accurate metrics


