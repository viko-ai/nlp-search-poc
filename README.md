# NLP & Elasticsearch powered product search

**Note:** this README assumes you already followed the instructions in the 1.0-es-basic branch README

## Setup

Kill the old 1.0 server if it's still running and restart it with the 1.5 code

Hit <kbd>Ctrl</kbd> + <kbd>c</kbd>

Don't worry about the `asyncio.exceptions.CancelledError` - it's caused by the hot reload feature of the uvicorn server.

```shell
$ bin/server.sh
```

## Improvements

Instead of searching against a single field this code searches against the **product_type** and **attrs** fields. The
query **must** match against product_type and **should** match against the attrs. On the face of it, this now works as
expected:

```shell
$  python -m src.client 'packable jacket'
```

```json
{
    "results": [
        {
            "title": "lightweight black jacket",
            "product_type": "jacket",
            "price": 100,
            "attrs": [
                "lightweight",
                "black"
            ]
        }
    ]
}
```

## Still broken

Elasticsearch's match query uses OR by default. So the query can be translated as:

_product_type must include jacket or packable_  
_attrs should include jacket or packable_

What happens if we have a product with the word 'packable' in the product type e.g. a 'packable bag'?

## Add another product

Reset the index and ingest another product, the packable bag

```shell
$ python -m src.tools reset
productRepository  INFO      Dropping products index
...
productRepository  INFO      Ingesting packable travel bag
```

Perform the query again:

```shell
$  python -m src.client 'packable jacket'
```

```json
{
    "results": [
        {
            "title": "packable travel bag",
            "product_type": "packable bag",
            "price": 20,
            "attrs": [
                "packable"
            ]
        }
    ]
}
```

## The problem remains

The underlying problem is still there. We can do all sorts of clever things with elasticsearch - applying custom
tokenizers and analysers, boosting field, generating sophisticated queries etc. These tricks tackle the problem in the
wrong way. 

> Instead of understanding what the user is asking for, we use our data to infer what we think they should be
asking for

It's a bit like a sales assistant telling a shopper "you want a jacket? ok these bags are truly unique ..." 🤨

## NLP to the rescue

In subsequent versions of this app, we'll implement basic NLP capabilities. This will allow us to fully understand
the user's search query.