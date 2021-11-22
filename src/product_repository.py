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
    colors: List[str]
    attrs: List[str]  # e.g. lightweight, cotton etc


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
        
        # Trivial mappings, almost identical to elasticsearch's defaults
        mappings = self._get_mappings()
        
        index_exists = await self._ES.indices.exists(index=self._INDEX_NAME)
        if index_exists:
            self._LOGGER.error("Index already exists")
        else:
            await self._ES.indices.create(index=self._INDEX_NAME, mappings=mappings)
            self._LOGGER.info(f"{self._INDEX_NAME} created")
    
    async def ingest(self, product: Product) -> None:
        self._LOGGER.info(f"Ingesting {product.title}")
        await self._ES.index(index=self._INDEX_NAME, document=product.dict())
    
    async def search(self, query: NerPrediction) -> List[Product]:
        """Search for a match against all fields"""
        
        product = query.product
        flat_colors = ' '.join(query.colors)
        flat_attrs = ' '.join(query.attrs)
        
        self._LOGGER.info(f"Searching for product: \"{product}\" "
                          f"with colors: \"{flat_colors}\", "
                          f"attrs: \"{flat_attrs}\", "
                          f"price from {query.price_from}, "
                          f"price to {query.price_to}")
        
        # NLU allows us to come at this from a different angle.
        # Instead of specifying the index fields that must be matched
        # we concentrate on the terms and phrases the user regards as important.
        # By understanding what product the user is looking for, along with it's
        # desirable attributes we can perform much more accurate searches
        
        # This is a very basic query, and it's not really the focus of this tutorial.
        # The aim is simply to illustrate how we can apply granular search filters, inferred via NLP/NER
        es_query: Dict = {
            "bool": {
                "must": [
                    {
                        'match': {
                            'title': product
                        }
                    }
                ]
            }
        }
        
        if query.colors:
            es_query['bool']['must'].append(self._es_color_query(query.colors))
        
        if query.price_from and query.price_to:
            es_query['bool']['must'].append(self._es_price_from_to_query(query.price_from, query.price_to))
        elif query.price_from:
            es_query['bool']['must'].append(self._es_price_from_query(query.price_from))
        elif query.price_to:
            es_query['bool']['must'].append(self._es_price_to_query(query.price_to))
        
        if query.attrs:
            es_query['bool']['should'] = [self._es_attrs_query(flat_attrs)]
        
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
    
    # Private - Keep out!
    
    @staticmethod
    def _get_mappings():
        return {
            'properties': {
                'title': {
                    'type': 'text',
                    'copy_to': ['all']
                },
                'product_type': {
                    'type': 'text',
                    'copy_to': ['all']
                },
                'colors': {
                    'type': 'keyword',
                    'copy_to': ['all']
                },
                'attrs': {
                    'type': 'keyword',
                    'copy_to': ['all']
                },
                'price': {
                    'type': 'float'
                },
                'all': {
                    'type': 'text'
                },
            }
        }
    
    @staticmethod
    def _es_color_query(colors):
        return {
            'terms': {
                'colors': colors
            }
        }
    
    @classmethod
    def _es_price_from_to_query(cls, price_from, price_to):
        return cls._price_query({
            'gte': price_from,
            'lte': price_to
        })
    
    @classmethod
    def _es_price_from_query(cls, price_from):
        return cls._price_query({
            'gte': price_from
        })
    
    @classmethod
    def _es_price_to_query(cls, price_to):
        return cls._price_query({
            'lte': price_to
        })
    
    @staticmethod
    def _es_attrs_query(attrs):
        return {
            'match': {
                'all': attrs
            }
        }
    
    @staticmethod
    def _price_query(query):
        return {
            'range': {
                'price': query
            }
        }
