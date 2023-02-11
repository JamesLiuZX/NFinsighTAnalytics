from prisma import Prisma
from prisma.models import *

db = Prisma(auto_register=True)

async def main():
  await db.connect()
  collection = await Collection.prisma().create(
    data={
      'address': '0x432'
    }
  )
  await db.disconnect()