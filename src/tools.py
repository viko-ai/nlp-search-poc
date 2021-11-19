import asyncio
import json
import logging.config

import plac  # type: ignore

from src.product_repository import Product, ProductRepository


async def ingest(product_repo):
    with open('data/products.json') as f:
        data = json.load(f)
        for record in data:
            product = Product.parse_obj(record)
            await product_repo.ingest(product)


async def get_task(product_repo, cmd):
    """Return a coroutine which creates the index, drops it or ingests data"""
    if cmd == 'ping':
        es_status = await product_repo.ping()
        print(f"Elasticsearch alive: {es_status}")
    elif cmd == 'create':
        await product_repo.create_index()
    elif cmd == 'ingest':
        await ingest(product_repo)
    elif cmd == 'drop':
        await product_repo.drop_index()
    elif cmd == 'reset':
        await product_repo.drop_index()
        await product_repo.create_index()
        await ingest(product_repo)


@plac.pos('cmd', "Command", choices=['ping', 'create', 'drop', 'ingest', 'reset'])
def main(cmd):
    product_repo = ProductRepository()
    task = get_task(product_repo, cmd)
    if task is not None:
        try:
            asyncio.run(task)
        finally:
            asyncio.run(product_repo.shutdown())


if __name__ == '__main__':
    logging.config.fileConfig('conf/logging.conf')
    plac.call(main)
