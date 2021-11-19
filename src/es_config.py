from __future__ import annotations

import os
from typing import NamedTuple


class EsConfig(NamedTuple):
    """Allows us to override the elastic search host when running inside docker"""
    host: str
    port: int
    
    @staticmethod
    def get() -> EsConfig:
        elastic_search_host = os.environ.get('ELASTIC_SEARCH_HOST', "localhost")
        elastic_search_port = int(os.environ.get('ELASTIC_SEARCH_PORT', "9200"))
        return EsConfig(elastic_search_host, elastic_search_port)
