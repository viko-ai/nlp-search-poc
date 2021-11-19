# NLP & Elasticsearch powered product search

Sample app intended to illustrate how **Natural Language Processing (NLP)**, specifically **Named Entity Recognition (
NER)** can be used to improve the accuracy of Elasticsearch queries and the overall user experience. There are two key
benefits to using NLP alongside Elasticsearch (or any other full text search engine):

## Pre-selecting search filters

Given the query _'black jacket costing less than $200'_ we can infer the color and max price, and apply these search
filters for the user. This concept can be extended to other fields (e.g. brand) and also support conjugations e.g.
_'black or dark green barbour jacket'_

## Distinguishing between essential and desirable query terms

Imagine you work for an outdoor clothing and equipment store. You're building a catalog search feature. Given the query
_'packable jacket'_, how should the search engine (e.g. Elasticsearch) choose between a _'packable mosquito net'_ and a
_'lightweight jacket'_. Both products partially match. TF-**IDF** will most likely select the mosquito net as there will
be fewer instances of _'packable'_ than _'jacket'_ in the corpus. However when looking at the query it's clear that the
lightweight jacket would be the better match.

We typically solve this problem by boosting certain document fields e.g. by attaching more weight to the title or
product type fields than the description. This sort of works, but the logic is wrong. We're essentially telling the
shopper "based on what we sell, this is what we think is important to you".

We humans understand that given the query _'packable jacket'_, the shopper wants a jacket first and foremost. That's
because we understand that _'jacket'_ is a product type and _'packable'_ is an attribute of the product. NLP allows us
to apply this same reasoning programmatically. In simple terms we can perform an elasticsearch bool query in which we **
must**
have a match for _'jacket'_ and **should** have a match for _'packable'_

## Caveats

Firstly, and most importantly this is not a production implementation. The NLP model used for this example is really
basic. For production use we'd build something far more robust, trained with historic search data. We'd also employ Part
of Speech Tagging along with Dependency Parsing to get a better understanding of the sentences and fragments of text.

Secondly, the elasticsearch code is very basic. For production use we'd want to use custom tokenizers, analysers &
synonyms. Of course, we'd have many more fields and lots more documents.

Finally, there's no error handling (eeks!).

So please treat this in the spirit in which it was created - **a proof of concept!**

## Getting started

1. Setup your environment
2. Fire up an elasticsearch instance
3. Create the index and mapping
4. Import some test data
5. Fire up a simple webserver to handle search queries
6. Cleanup

### Setup your environment

The python code needs a 3.10.0 environment (it uses the new pattern matching features). There are many ways of doing
this, but personally I prefer pyenv-virtualenv / pyenv-virtualenvwrapper:

```shell
$ pyenv install 3.10.0
$ pyenv virtualenv 3.10.0 search-demo
$ pyenv local search-demo 
$ pip install -U pip
$ pip install -r requirements.txt
```

### Run elasticsearch

We've provided a docker-compose.yml file, so you fire up a simple elasticsearch instance

```shell
$ docker-compose up -d elasticsearch-7
```

### Test the setup

Python dependencies and paths can be tricky, so we provided a simple script to check everything is working as expected.
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

We created a wrapper shell script to fire up uvicorn/fastapi

```shell
$ bin/server.sh
uvicorn.error    INFO      Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
...
```

### Perform the search

Make a GET request to http://localhost:8000 passing a json body:

```json
{
    "query": "lightweight jacket"
}
```

Postman is probably the best tool for this, but I've also included a shell script which uses curl and jq

```shell
$ bin/query.sh 'lightweight black jacket less than $100'
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
expansion. This could be a problem if for example you perform this query:

```shell
$ bin/query.sh "lightweight jacket less that $300"
```

## Sample queries

Firstly take a look at the sample data in `data/products.json` As you can see we have various lightweight jackets, along
with a packable mosquito net and packable bag. We don't have a 'packable jacket' in the catalog.

Try searching for `'packable jacket'`

TF-IDF alone would select either the mosquito net or packable bag. In our case, we're able to tell elasticsearch that
any products must contain the word 'jacket'. It will select the lightweight jacket.

In the response you will see the NLP predictions alongside the search results:

```json
{
    "ner_prediction": {
        "text": "packable jacket",
        "product": "jacket",
        "attrs": [
            "packable"
        ]
    },
    "results": [
        {
            "title": "lightweight black jacket"
        }
    ]
}
```

If you're only interested in the NLP predictions you can hit the `/predict` endpoint or use the provided script (
bin/predict.sh).

Let's try adding some color to the query (literally!)

```shell
$  bin/predict.sh 'lightweight black jacket'
```

Notice how the NLP prediction detects the color:

```json
{
    "ner_prediction": {
        "text": "lightweight black jacket",
        "product": "jacket",
        "colors": [
            "black"
        ],
        "attrs": [
            "lightweight"
        ]
    },
    "results": [
        {
            "title": "lightweight black jacket"
        }
    ]
}
```

I'm cheating here because the NLP model was explicitly trained with the word `lightweight`. Try something else, e.g. '
showerproof' or 'windproof' (the model hasn't seen either of these words before):

```shell
$ bin/predict.sh 'black showerproof jacket'
```

```json
{
    "text": "showerproof black jacket",
    "product": "jacket",
    "colors": [
        "black"
    ],
    "attrs": [
        "showerproof"
    ]
}
```

It still works! That's because NLP, like all AI is able to generalise and make predictions.

### Note

Color is a special case. The NLP model treats color as a generic product attribute. We identify colors by looking for
certain known colors within the identified product attributes. The reason for this is that we would typically want to
use this logic not only to fetch the search results, but also to preselect a color filter in the UI. The choice of
colors available in the search filter is finite.

For example try searching for a `'beige jacket'`. The NLP model identifies it as an attribute but our code doesn't
identify it as a color. Assuming we have a jacket in the catalogue with the attribute 'beige', or we search against
a generated field (copy_to), we'd still find it.

### Cleanup

Kill the running server with Ctrl-C (don't worry about the asyncio.exceptions.CancelledError)

Drop the index

```shell
$ python -m src.tools drop
productRepository  INFO      Dropping products index
productRepository  INFO      products dropped
```

## Docker (optional)

I've provided a Dockerfile in case you want to run everything inside docker

```shell
docker build -t search-demo .
```

Then run elasticsearch and the server

```shell
docker-compose up -d
```

### Ingesting test data

If you also want to use docker to ingest the test data into elasticsearch you can do so:

```shell
docker run -it --rm --network search-demo_default -e "ELASTIC_SEARCH_HOST=elasticsearch-7" search-demo "python" "-m" "src.tools" "reset"
```

**Note**: The network name is determined by docker's [networking rules](https://docs.docker.com/compose/networking/)