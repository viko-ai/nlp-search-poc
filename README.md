# NLP & Elasticsearch powered product search

**Note:** this README assumes you previously followed the instructions in the 2.0-ner-basic branch README

## Extending NLP

E-commerce search is typically composed of full-text search along with pre-defined filters (color, price range etc.).
The 2.0-ner-basic branch of this code used NLP/NER to improve the accuracy of the full text search, but we can go much
further. We can also use NER to identify and apply search filters. For example. given the query"

`'lightweight black jacket between $200 and $300'`

We can:

1. Identify the desired product type is a jacket
2. With the attribute of being lightweight
3. Preselect the black color filter
4. Fill in (or select) the price filters

## Getting started

Firstly remember to kill any old versions of the server that may still be running:

<kbd>Ctrl</kbd> + <kbd>c</kbd>

Import the new structured data

```shell
$ python -m src.tools reset
...
productRepository INFO Ingesting burgundy organic cotton jacket
```

Rerun the server

```shell
$ bin/server.sh
```

## Query again

Try a query which includes a color and price

```shell
$ python -m src.client 'black waterproof jacket less than $200'
```

```json
{
    "text": "black waterproof jacket less than $200",
    "product": "jacket",
    "price_from": null,
    "price_to": 200.0,
    "colors": [
        "black"
    ],
    "attrs": [
        "waterproof"
    ]
}
```

## Code changes

There are a few significant changes to the code and NLP model. Firstly the NER model has been extended to include a new
entity "PRICE" alongside the existing "PRODUCT" and "ATTRIBUTE" entities. The model has been trained on UK and US prices
e.g. $100, £200. The model has also been trained with colors, although we didn't introduce a "COLOR" attribute ...

In a real world e-commerce application, a color filter would be restricted to a small finite set or colors. Full text
search allows the user to type anything. Being statistical, the NER model may identify colours that are not in the
search filter. It may identify colors that didn't even appear in the NLP training data.

NLP is not 100% accurate. Good models (this sample model is not good!) are pretty accurate, but we can't guarantee that
the model will only identify colors as such. The model could decide that 'sustainable' is a color. Searching for a
product in color 'sustainable' will not result in any matches. However, searching for a product with an attribute of '
maroon' or 'champagne' would work.

So, from an NLP/NER perspective, we treat colors like all other generic attributes. We then use rules to identify known
colors that match our search filters. This gives us the best of both worlds. Search filters work as expected, but we
still support long tail searches for wacky colors. 

As a bonus, this also improves the overall accuracy of the model. Unlike most NLP applications, we have a limited amount
of _context_ available to us in the search query. Trying to identify too many attributes that are grammatically 
similar will reduce the overall model performance.