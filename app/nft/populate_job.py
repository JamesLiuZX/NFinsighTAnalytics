from .mnemonic.mnemonic_types import *
from .mnemonic.api import *

# WIP
async def update_rankings():
    for rank in MnemonicQuery__RankType._member_map_:
        for duration in MnemonicQuery__RecordsDuration._member_map_:
            """
            top_collections = await get_top_collections(
                MnemonicQuery__RankType[rank],
                MnemonicQuery__RecordsDuration[duration]
            )
            """
            print(rank, duration)

