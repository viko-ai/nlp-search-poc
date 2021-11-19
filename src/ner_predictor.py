from typing import List, Optional

import spacy
from pydantic import BaseModel


class NerPrediction(BaseModel):
    text: str
    product: Optional[str] = None
    attrs: List[str] = []
    
    def is_valid(self):
        return self.product is not None


class NerPredictor:
    """Predict product and product attributes using NER"""
    
    def __init__(self):
        # ner_outdoor_equipment_sm is a really simple nlp model, trained on around 200 phrases
        # It's certainly not suitable for production use
        self._NLP = spacy.load("nlp_models/ner_outdoor_equipment_sm")
    
    def predict(self, text: str) -> NerPrediction:
        """Use the NER component of the spacy NLP pipeline to predict products and attributes in text"""
        
        # For production use we would do preprocessing (custom tokenizer)
        # and probably also employ part of speech tagging and dependency parsing
        # to get a better understanding of the text
        doc = self._NLP(text)
        response = NerPrediction(text=text)
        for ent in doc.ents:
            if ent.label_ == "PRODUCT":
                response.product = ent.text
            elif ent.label_ == "ATTRIBUTE":
                response.attrs.append(ent.text)
        return response
