import os

from fastapi.routing import APIRouter

from datetime import datetime
from functools import lru_cache
from httpx import AsyncClient

from .mnemonic_types import MnemonicQuery__RankType, MnemonicQuery__RecordsDuration


client = AsyncClient()

router = APIRouter()

@lru_cache(maxsize=1)
def get_header():
    return {
        'X-API-Key': os.environ['MNEMONIC_API_KEY']
    }


async def get_collection_meta(contract_address: str):
    url = f'https://ethereum-rest.api.mnemonichq.com/collections/v1beta2/{contract_address}/metadata?includeStats=true'
    header = get_header()
    response = await client.get(url=url, headers=header)

    assert response.status_code == 200
    return response.json()

@router.get("/top_collections/{rank}/{time_period}")
async def get_top_collections(
        rank:           MnemonicQuery__RankType,
        time_period:    MnemonicQuery__RecordsDuration,
        limit:          str = '100', #To be added in increments of 100
        offset:         str = '0'
):  
    url = f'https://ethereum-rest.api.mnemonichq.com/collections/v1beta2/top/METRIC_{str(rank.value).upper()}/{time_period.value}'
    params = {
        'limit': limit,
        'offset': offset
        }
    header = get_header()
    response = await client.get(url, params=params, headers=header)

    # assert response.status_code == 200
    return response.json()
    

async def get_collection_price_history(
        contract_address:   str,
        time_period:        MnemonicQuery__RecordsDuration,
        group_by:           str,
        time_stamp_lt:      datetime
):
    url = f'https://ethereum-rest.api.mnemonichq.com/collections/v1beta2/{contract_address}/prices/{time_period.value}/{group_by}'
    params = {
        'timestampLt': time_stamp_lt.strftime("%Y-%M-%dT%H:%M:%SZ")
        }
    header = get_header()
    response = await client.get(url, params=params, headers=header)

    assert response.status_code == 200
    return response.json()


async def get_collection_sales_volume(
        contract_address:   str,
        time_period:        MnemonicQuery__RecordsDuration,
        group_by:           str,
        time_stamp_lt:      datetime
):
    url = f'https://ethereum-rest.api.mnemonichq.com/collections/v1beta2/{contract_address}/sales_volume/{time_period.value}/{group_by}'
    params = {
        'timestampLt': time_stamp_lt.strftime("%Y-%M-%dT%H:%M:%SZ")
        }
    header = get_header()
    response = await client.get(url, params=params, headers=header)

    assert response.status_code == 200
    return response.json()


async def get_collection_token_supply(
        contract_address:   str,
        time_period:        MnemonicQuery__RecordsDuration,
        group_by:           str,
        time_stamp_lt:      datetime
):
    url = f'https://ethereum-rest.api.mnemonichq.com/collections/v1beta2/{contract_address}/supply/{time_period.value}/{group_by}'
    params = {
        'timestampLt': time_stamp_lt.strftime("%Y-%M-%dT%H:%M:%SZ")
        }
    header = get_header()
    response = await client.get(url, params=params, headers=header)

    assert response.status_code == 200
    return response.json()


async def get_collection_owners_count(
        contract_address:   str,
        time_period:        MnemonicQuery__RecordsDuration,
        group_by:           str,
        time_stamp_lt:      datetime
):
    url = f'https://ethereum-rest.api.mnemonichq.com/collections/v1beta2/{contract_address}/owners_count/{time_period.value}/{group_by}'
    params = {
        'timestampLt': time_stamp_lt.strftime("%Y-%M-%dT%H:%M:%SZ")
        }
    header = get_header()
    response = await client.get(url, params=params, headers=header)

    assert response.status_code == 200
    return response.json()


