import logging
from typing import Dict, Final, List

from elasticsearch import AsyncElasticsearch
from pydantic import BaseModel

from src.es_config import EsConfig


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
    
    async def search(self, query: str) -> List[Product]:
        """Search for a match against the title field"""
        
        self._LOGGER.info(f"Searching for: {query}")
        
        # On the face of it this works i.e. a query for "packable jacket" returns a lightweight jacket.
        # However, by default a match query performs an OR i.e. product_type must include 'packable' or 'jacket'
        # What would happen if a product type included the word 'packable' e.g. 'packable bag' ?
        es_query: Dict = {
            'bool': {
                'must': {
                    'match': {
                        'product_type': query
                    }
                },
                'should': {
                    'match': {
                        'attrs': query
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
