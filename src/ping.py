import asyncio

from src.product_repository import ProductRepository


async def main():
    repo = ProductRepository()
    es_status = await repo.ping()
    print(f"Elasticsearch alive: {es_status}")
    await repo.shutdown()


asyncio.run(main())
