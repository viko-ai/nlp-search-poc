import logging
from typing import Dict, Final, List

from elasticsearch import AsyncElasticsearch
from pydantic import BaseModel

from src.es_config import EsConfig
from src.ner_predictor import NerPrediction


class Product(BaseModel):
    title: str
    product_type: str  # e.g. jacket, shirt
    price: float  # don't use floats in production!
    attrs: List[str]  # e.g. lightweight, blue, cotton etc


class ProductRepository:
    """Wrapper around Elasticsearch"""
    
    _INDEX_NAME: Final = 'products'
    
    def __init__(self):
        es_config = EsConfig.get()
        
        self._ES: Final = AsyncElasticsearch([{
            "host": es_config.host,
            "port": es_config.port
        }])
        
        self._LOGGER: Final = logging.getLogger("productRepository")
    
    async def ping(self) -> bool:
        return await self._ES.ping()
    
    async def create_index(self) -> None:
        self._LOGGER.info(f"Creating {self._INDEX_NAME} index")
        
        # Trivial mappings
        mappings = {
            'properties': {
                'title': {
                    'type': 'text'
                },
                'product_type': {
                    'type': 'text'
                },
                'attrs': {
                    'type': 'text'
                },
                'price': {
                    'type': 'float'
                },
            }
        }
        
        index_exists = await self._ES.indices.exists(index=self._INDEX_NAME)
        if index_exists:
            self._LOGGER.error("Index already exists")
        else:
            await self._ES.indices.create(index=self._INDEX_NAME, mappings=mappings)
            self._LOGGER.info(f"{self._INDEX_NAME} created")
    
    async def ingest(self, product: Product) -> None:
        self._LOGGER.info(f"Ingesting {product.title}")
        await self._ES.index(index=self._INDEX_NAME, document=product.dict())
    
    async def search(self, query: NerPrediction):
        """Search for a match against the title field"""
        
        product = query.product
        attrs = ' '.join(query.attrs)
        self._LOGGER.info(f"Searching for product: \"{product}\" with attrs: \"{attrs}\"")
        
        # NLU allows us to come at this from a different angle.
        # Instead of specifying the index fields that must be matched
        # we concentrate on the terms and phrases the user regards as important.
        # By understanding what product the user is looking for, along with it's
        # desirable attributes we can perform much more accurate searches
        es_query: Dict = {
            'bool': {
                'must': {
                    'match': {
                        'title': product
                    }
                },
                'should': {
                    'match': {
                        'attrs': attrs
                    }
                }
            }
        }
        
        res = await self._ES.search(index=self._INDEX_NAME, query=es_query, size=1)
        products = [Product.parse_obj(hit['_source']) for hit in res['hits']['hits']]
        return products
    
    async def drop_index(self) -> None:
        self._LOGGER.info(f"Dropping {self._INDEX_NAME} index")
        
        index_exists = await self._ES.indices.exists(index=self._INDEX_NAME)
        if index_exists:
            await self._ES.indices.delete(index=self._INDEX_NAME)
            self._LOGGER.info(f"{self._INDEX_NAME} dropped")
        else:
            self._LOGGER.error("Index not found")
    
    async def shutdown(self) -> None:
        await self._ES.close()
