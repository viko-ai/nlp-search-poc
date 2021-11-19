# NLP & Elasticsearch powered product search

This is a trivial app which simply searches against a single field in an elasticsearch index. This version of the app is
intentionally naive, but designed to illustrate a problem:

1. We have various jackets in the database (elasticsearch index)
2. We also have a 'packable mosquito net'
3. The user searches for a 'packable jacket'

As humans, we understand that a 'lightweight jacket' would be a good candidate. We know this because we understand that
the user is looking for a jacket first and foremost. However, elasticsearch's TF-**IDF** algorithm thinks the 'packable
mosquito net' is the best match, because it includes the word 'packable'.

Subsequent versions of the app (git tags) will try to solve the problem. Firstly by changing the elasticsearch query,
then finally by employing Natural Language Understanding.

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

Python dependencies and paths can be tricky, so I provided a simple script to check everything is working as expected.
Note: elasticsearch can take a few seconds to come online.

```shell
$ python -m src.ping
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

Postman is probably the best tool for this, but I've also included a shell script which uses curl and jq

```shell
$ bin/query.sh 'packable jacket'
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

**Important:** If you choose to use this script you should enclose your search query in single quotes to avoid variable
expansion. This could be a problem if for example you perform this query:

```shell
$ bin/query.sh "lightweight jacket less that $300"
```

### Cleanup

Kill the running server with Ctrl-C (don't worry about the asyncio.exceptions.CancelledError)

Drop the index

```shell
$ python -m src.tools drop
productRepository  INFO      Dropping products index
productRepository  INFO      products dropped
```

Take down elasticsearch

```shell
$ docker-compose down
Stopping elasticsearch-7 ... done
Removing elasticsearch-7 ... done
Removing network nlp-search_default
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

docker-compose exposes the server's port 8000, so you can query as before:

```shell
$ bin/query.sh 'packable jacket'
```