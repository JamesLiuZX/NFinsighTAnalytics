from fastapi import FastAPI
from db.database import *

app = FastAPI()

@app.get("/")
async def root():
  await p_main()
  return { "message": "Hello World"}