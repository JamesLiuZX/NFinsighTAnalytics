from prisma import Prisma
from prisma.models import *
from prisma.types import CollectionCreateInput
from decimal import Decimal

db = Prisma(auto_register=True, use_dotenv=True)

async def p_main():
  await db.connect()

  data_point: CollectionCreateInput = {
      'address': '0x432',
      'tokens': 0,
      'owners': 0,
      'salesVolume': Decimal('0'),
      'image': "",
      'bannerImg': ""
    }

  collection = await Collection.prisma().upsert(
    where={
      'address': '0x432'
    },
    data={
      'create': data_point,
      'update': data_point
    }
  )
  await db.disconnect()
