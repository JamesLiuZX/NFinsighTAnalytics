from enum import Enum


class MnemonicResponse__CollectionType(Enum):
    UNKNOWN         = "TOKEN_TYPE_UNKNOWN"
    ERC20           = "TOKEN_TYPE_ERC20"
    ERC721          = "TOKEN_TYPE_ERC721"
    ERC1155         = "TOKEN_TYPE_ERC1155"
    ERC721_LEGACY   = "TOKEN_TYPE_ERC721_LEGACY"
    CRYPTOPUNKS     = "TOKEN_TYPE_CRYPTOPUNKS"


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


class MnemonicQuery__Marketplaces(Enum):
    OPENSEA         = "MARKETPLACE_ID_OPENSEA"
    LOOKSRARE       = "MARKETPLACE_ID_LOOKSRARE"
    CRYPTORUNKS     = "MARKETPLACE_ID_CRYPTOPUNKS"
    SUPERRARE       = "MARKETPLACE_ID_SUPERRARE"


class MnemonicQuery__RankType(Enum):
    AVG_PRICE = "avg_price"
    MAX_PRICE = "max_price"


