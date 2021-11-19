import re
from typing import Final, List, Optional

import spacy
from pydantic import BaseModel


class NerPrediction(BaseModel):
    text: str
    product: Optional[str] = None
    price_from: Optional[float] = None
    price_to: Optional[float] = None
    colors: List[str] = []
    attrs: List[str] = []
    
    def is_valid(self):
        return self.product is not None


class NerPredictor:
    """Predict product and product attributes using NER & simple regex"""
    
    _COLORS: Final = {'black', 'white', 'brown', 'red', 'blue', 'green', 'orange', 'green', 'yellow'}
    
    def __init__(self):
        # ner_outdoor_equipment_sm is a really simple nlp model, trained on around 200 phrases
        # It's certainly not suitable for production use
        nlp = spacy.load("nlp_models/ner_outdoor_equipment_md")
        NerPredictor._add_entity_ruler(nlp)
        self._NLP = nlp
    
    def predict(self, text: str) -> NerPrediction:
        """Use the NER component of the spacy NLP pipeline to predict products and attributes in text"""
        
        # For production use we would do preprocessing (custom tokenizer)
        # and probably also employ part of speech tagging and dependency parsing
        # to get a better understanding of the text
        doc = self._NLP(text)
        
        product = None
        attrs = []
        prices = []
        
        for ent in doc.ents:
            if ent.label_ == "PRODUCT":
                product = ent.text
            elif ent.label_ == "ATTRIBUTE":
                attrs.append(ent.text)
            elif ent.label_ == "PRICE":
                prices.append(ent.text)
        
        (colors, other_attrs) = self._parse_colors(attrs)
        (price_from, price_to) = self._parse_prices(prices)
        
        return NerPrediction(text=text, product=product, colors=colors,
                             attrs=other_attrs, price_from=price_from, price_to=price_to)
    
    # Private - Keep out!
    
    @classmethod
    def _parse_prices(cls, prices):
        # Pretty naive implementation which parses the prices and assumes that when given two prices,
        # the first is price from and the second is price to. In production we would use a more
        # sophisticated NER model along with dependency parsing to accurately identify the different prices
        
        float_prices = [cls._parse_price(price) for price in prices]
        float_prices = [p for p in float_prices if p is not None]
        
        if len(float_prices) == 1:
            return None, float_prices[0]
        elif len(float_prices) == 2:
            return float_prices[0], float_prices[1]
        else:
            return None, None
    
    @staticmethod
    def _parse_price(price):
        # Spacy's NER pipeline component will return something like $100 or £50
        # so we want to parse it as a number.
        
        numeric_string = re.sub(r"[^0-9.]", "", price)
        try:
            return float(numeric_string)
        except ValueError:
            return None
    
    @classmethod
    def _parse_colors(cls, attrs):
        # We could introduce another NER label 'COLOR' and train the model with suitable examples.
        # We would most likely want to use the predicted color not only for the search itself, but
        # also to pre select a search filter in the UI. This will be composed of a finite selection
        # of values (checkboxes or multi-select). NER predictions are infinite so this won't work.
        #
        # If we treat everything as an attribute and pick known colors we get the best of both worlds.
        # The user can still search for a color that's not in the UI search filter, but specific colors
        # also populate the UI.
        
        colors, other_attrs = [], []
        for attr in attrs:
            colors.append(attr) if attr in cls._COLORS else other_attrs.append(attr)
        return colors, other_attrs
    
    @classmethod
    def _add_entity_ruler(cls, nlp):
        """Use rules to improve NER accuracy"""
        
        # See https://spacy.io/usage/rule-based-matching#entityruler
        
        price_pattern = {
            "label": "PRICE",
            "pattern": [
                {
                    "ORTH": {
                        "IN": ["$", "£"]
                    }
                },
                {
                    "IS_DIGIT": True
                }
            ]
        }
        
        color_pattern = {
            "label": "COLOR",
            "pattern": [
                {
                    "LOWER": {
                        "IN": list(cls._COLORS)
                    }
                }
            ]
        }
        
        ruler = nlp.add_pipe("entity_ruler")
        ruler.add_patterns([price_pattern, color_pattern])
