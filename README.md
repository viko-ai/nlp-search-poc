# NLP & Elasticsearch powered product search

This is a trivial app which simply searches against a single field in an elasticsearch index. This version of the app is
intentionally naive, but designed to illustrate a problem. Imagine we are building the catalog search feature for an
outdoor clothing & equipment store.

1. A shopper searches for a 'packable jacket'
2. We don't sell a 'packable jacket'
3. We do sell many jackets (lightweight, waterproof, windproof etc)
4. We also sell a 'packable mosquito net'

As humans, we understand that a 'lightweight jacket' would be a good candidate for this search query. We know this
because we understand that the user is looking for a jacket first and foremost. However, elasticsearch's TF-**IDF**
algorithm thinks the 'packable mosquito net' is the best match, because it includes the word 'packable'.

Subsequent versions of this app will try to solve the problem. Firstly by changing the elasticsearch query, then finally
by employing Natural Language Understanding.

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
$ pyenv virtualenv 3.9.7 nlp-search
$ pyenv local nlp-search 
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
    "query": "packable jacket"
}
```

Postman is probably the best tool for this, but I've also included a simple client:

```shell
$ python -m src.client 'packable jacket'
```

```json
{
    "results": [
        {
            "title": "packable mosquito net",
            "product_type": "mosquito net",
            "price": 10.0,
            "attrs": [
                "packable"
            ]
        }
    ]
}
```

**Important:** If you choose to use this script you should enclose your search query in single quotes to avoid variable
expansion. This could be a problem if for example you perform this query:

```shell
$ python -m src.client "lightweight jacket less that $300"
```

## Docker (optional)

I've provided a Dockerfile in case you want to run everything inside docker

```shell
docker build -t nlp-search .
```

Then run elasticsearch and the server

```shell
docker-compose up -d
```

### Ingesting test data

If you also want to use docker to ingest the test data into elasticsearch you can do so:

```shell
docker run -it --rm --network nlp-search_default -e "ELASTIC_SEARCH_HOST=elasticsearch-7" nlp-search "python" "-m" "src.tools" "reset"
```

**Note**: The network name is determined by docker's [networking rules](https://docs.docker.com/compose/networking/)

### Querying

docker-compose.yml exposes the server's port 8000, so you can query as before:

```shell
$ python -m src.client 'packable jacket'
```