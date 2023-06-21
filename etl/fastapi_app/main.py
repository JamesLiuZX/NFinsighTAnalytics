import os
from ssl import CERT_NONE, PROTOCOL_TLSv1_2, SSLContext

import dotenv
from fastapi import FastAPI

from .auth.authenticate import router as auth_router
from .nft.gallop.api import router as gallop_router
from .nft.mnemonic.api import router as mnemonic_router
from .nft.populate_job import router as populate_router


app = FastAPI()

app.include_router(auth_router)
app.include_router(gallop_router, prefix="/gallop")
app.include_router(mnemonic_router, prefix="/mnemonic")
app.include_router(populate_router)


# Initialise env values
async def read_env_values():
    DOTENV_PATH = os.getcwd() + "/etl/fastapi_app/.env"
    dotenv.load_dotenv(DOTENV_PATH)


# Connect to database, init env values
@app.on_event("startup")
async def api_init():
    await read_env_values()
