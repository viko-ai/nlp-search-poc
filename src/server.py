import logging

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import PlainTextResponse

from src.ner_predictor import NerPredictor
from src.product_repository import ProductRepository


class SearchCommand(BaseModel):
    query: str


app = FastAPI(title="NLP Enabled Search")
logger = logging.getLogger("uvicorn.error")
ner_predictor = NerPredictor()
product_repository = ProductRepository()


@app.on_event("startup")
def startup_event():
    pass


@app.get("/ping", response_class=PlainTextResponse)
async def ping():
    es_status = await product_repository.ping()
    return {'elasticsearch-alive': es_status}


@app.get("/predict")
def predict(cmd: SearchCommand):
    return ner_predictor.predict(cmd.query)


@app.get("/search")
async def search(cmd: SearchCommand):
    ner_prediction = ner_predictor.predict(cmd.query)
    products = []
    if ner_prediction.is_valid():
        products = await product_repository.search(ner_prediction)
    return {'results': products}


@app.on_event("shutdown")
async def shutdown_event():
    await product_repository.shutdown()
