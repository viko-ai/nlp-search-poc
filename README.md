# NLP & Elasticsearch powered product search

Sample app intended to illustrate how **Natural Language Processing (NLP)**, specifically **Named Entity Recognition (
NER)** can be used to improve the accuracy of Elasticsearch queries and the overall user experience. There are two key
benefits to using NLP alongside Elasticsearch (or any other full text search engine):

## Pre-selecting search filters

Given the query _'black jacket costing less than $200'_, we can infer the color and max price, and apply these search
filters for the user. This concept can be extended to other fields (e.g. brand) and also support conjugations e.g.
_'black or dark green barbour jacket'_

## Distinguishing between essential and desirable query terms

Imagine you work for an outdoor clothing and equipment store. You're building a catalog search feature. Given the query
'packable jacket', how should the database choose between a 'packable mosquito net' and a 'lightweight jacket'.
Both products partially match. TF-**IDF** will most likely select the mosquito net as there will be fewer instances
of 'packable' than 'jacket' in the corpus. However when looking at the query it's clear that the lightweight jacket
would be the better match.

We typically solve this problem by boosting certain document fields e.g. by attaching more weight to the title or
product type fields than the description. This sort of works, but the logic is wrong. We're essentially telling the
shopper "based on what we sell, this is what we think is important to you".

Humans understand that given the query 'packable jacket', the shopper wants a jacket first and foremost. That's
because we understand that 'jacket' is a product type and 'packable' is an attribute of the product. Natural
Language Processing (NLP) allows us to apply this same reasoning programmatically. In simple terms we can perform an
elasticsearch bool query in which we **must** have a match for 'jacket' and **should** have a match for 'packable'.

## Caveats

Firstly, and most importantly this is not a production implementation. The NLP model used for this example is really
basic. For production use we'd build something far more robust, trained with historic search data. We'd also employ Part
of Speech Tagging along with Dependency Parsing to get a better understanding of the sentences and fragments of text.

Secondly, the elasticsearch code is very basic. For production use we'd want to use custom tokenizers, analysers &
synonyms. Of course, we'd have many more fields and lots more documents.

Finally, there's no error handling!.

So please treat this in the spirit in which it was created - **a proof of concept!**

## Getting started

1. Setup your environment
2. Fire up an elasticsearch instance
3. Create the index and mapping
4. Import some test data
5. Fire up a simple webserver to handle search queries
6. Cleanup

### Setup your environment

The python code needs a 3.9.7+ environment. I recommend running this in a virtualenv using
either [venv](https://docs.python.org/3/library/venv.html)
or [pyenv/virtualenv](https://github.com/pyenv/pyenv-virtualenv)

```shell
$ pyenv install 3.9.7
$ pyenv virtualenv 3.9.7 nlp-search-poc
$ pyenv local nlp-search-poc 
$ pip install -U pip
$ pip install -r requirements.txt
```

### Run elasticsearch

I've provided a docker-compose.yml file, so you can fire up a simple elasticsearch instance

```shell
$ docker-compose up -d elasticsearch-7
```

### Test the setup

Python dependencies and paths can be tricky, so I provided a simple utility to check everything is working as expected.
**Note:** elasticsearch can take a few seconds to come online.

```shell
$ python -m src.tools ping
Elasticsearch alive: True
```

### Create the index & import test data

```shell
$ python -m src.tools create
productRepository  INFO      Creating products index
productRepository  INFO      products created
$ python -m src.tools ingest
productRepository  INFO      Ingesting lightweight black jacket
productRepository  INFO      Ingesting midweight black jacket
...
```

### Run the server

I created a wrapper shell script to fire up uvicorn/fastapi

```shell
$ bin/server.sh
uvicorn.error    INFO      Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
...
```

### Perform the search

Make a GET request to http://localhost:8000 passing a json body:

```json
{
    "query": "lightweight black jacket less than $100"
}
```

Postman is probably the best tool for this, but I've also included a simple client:

```shell
$ python -m src.client 'lightweight black jacket less than $100'
```

```json
{
    "ner_prediction": {
        "text": "lightweight black jacket less than $100",
        "product": "jacket",
        "price_from": null,
        "price_to": 100,
        "colors": [
            "black"
        ],
        "attrs": [
            "lightweight"
        ]
    },
    "results": [
        {
            "title": "lightweight black jacket",
            "product_type": "jacket",
            "price": 100,
            "colors": [
                "black"
            ],
            "attrs": [
                "lightweight"
            ]
        }
    ]
}
```

**Important:** If you choose to use this script you should enclose your search query in single quotes to avoid variable
expansion.

### Cleanup

#### Kill the running server

Hit <kbd>Ctrl</kbd> + <kbd>c</kbd>

Don't worry about the `asyncio.exceptions.CancelledError` - it's caused by the hot reload feature of the uvicorn server.

#### Drop the index

```shell
$ python -m src.tools drop
productRepository  INFO      Dropping products index
productRepository  INFO      products dropped
```

#### Take down elasticsearch

```shell
$ docker-compose down
Stopping elasticsearch-7 ... done
Removing elasticsearch-7 ... done
Removing network nlp-search-poc_default
```

## Docker (optional)

I've provided a Dockerfile in case you want to run everything inside docker

```shell
$ docker build -t nlp-search-poc .
```

Then run elasticsearch and the server

```shell
$ docker-compose up -d
```

### Ingesting test data

If you also want to use docker to ingest the test data into elasticsearch you can do so:

```shell
$ docker run -it --rm --network nlp-search-poc_default -e "ELASTIC_SEARCH_HOST=elasticsearch-7" nlp-search-poc "python" "-m" "src.tools" "reset"
```

**Note**: The network name is determined by docker's [networking rules](https://docs.docker.com/compose/networking/)

### Querying

docker-compose.yml exposes the server's port 8000, so you can query as before:

```shell
$ python -m src.client 'packable jacket'
```