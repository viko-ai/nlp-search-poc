import logging

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import PlainTextResponse

from src.product_repository import ProductRepository


class SearchCommand(BaseModel):
    query: str


app = FastAPI(title="NLP Enabled Search")
logger = logging.getLogger("uvicorn.error")
product_repository = ProductRepository()


@app.on_event("startup")
def startup_event():
    pass


@app.get("/ping", response_class=PlainTextResponse)
async def ping():
    es_status = await product_repository.ping()
    return {'elasticsearch-alive': es_status}


@app.get("/search")
async def search(cmd: SearchCommand):
    products = await product_repository.search(cmd.query)
    return {'results': products}


@app.on_event("shutdown")
async def shutdown_event():
    await product_repository.shutdown()
