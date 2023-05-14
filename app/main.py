from fastapi import FastAPI

from .auth import authenticate

app = FastAPI()

app.include_router(authenticate.router)


