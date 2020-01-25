#!/usr/bin/env python3

import os, json, re, yaml
from tabulate import tabulate
#import spacy
#import en_core_web_sm

from .text_structure import TextStructure
from ..skills import expressions

R_ENTITIES = re.compile(r"<{1,2}(.*?)>{1,2}")

SPACY_ENTITIES = {
    "PERSON": "person", "GPE": "location", "LANGUAGE": "language",
    "DATE": "date", "TIME": "time", "MONEY": "currency",
    "CARDINAL": "number","NORP":"social_group", "FAC": "building",
    "ORG":"organization", "LOC": "geo_object", "PRODUCT": "product",
    "EVENT": "event", "WORK_OF_ART":"work_of_art", "PERCENT": "percent",
    "ORDINAL":"ordinal", "QUANTITY": "quantity"
}

CUSTOM_ENTITIES = {
    "restaurant": (
        "McDonalds",
        "Starbucks",
        "Nando's",
        "KFC",
        "BK"
    ),
    "app_launchers": (
        "",
    ),
    "website_url": (
        "",
    )
}


def regex_prepare():
    """Convert expressions defined in skills
    into proper regex format.
    """
    processed_exprs = {}
    for intent, exprs in expressions.items():
        for expr in exprs:
            "0. Extract entities "
            entity_names = re.findall(R_ENTITIES, expr)

            "1. Create search regex"
            regex = re.sub(r"<<.*?>>",  r"(.*)", expr) #"(.*?)"
            regex = re.sub(r"<.*?>",  r"([a-zA-Z0-9_]*)", regex)

            result = {
                "value": expr,
                "regex": regex,
                "entity_names": entity_names
            }
            try:
                processed_exprs[intent].append(result)
            except:
                processed_exprs[intent] = [result]
    return processed_exprs


processed_exprs = regex_prepare()


class NaturalLanguageUnderstander(object):
    """One-off Natural Language Understander.
    Combines results from 3 ways of finding entities and 2 ways of finding intents.
    Function understand() returns a list of 1 or, in the case of multiple intents, more TextStructure objects.
    """

    def __init__(self,
        expressions=processed_exprs,
        custom_entities=CUSTOM_ENTITIES
    ):
        self.expressions = expressions
        self.custom_entities = CUSTOM_ENTITIES
        self.spacy_ents = SPACY_ENTITIES
        #self.spacy_nlp = en_core_web_sm.load()

    def understand(self, text):
        """Returns an TextStructure object that will contain
        intent, entitites, etc. of inputted text.
        """
        result = self.regex_undestand(text)
        #result["entities"].update(self.find_CUSTOM_ENTITIES(text))
        #result["entities"].update(self.find_spacy_entities(text))

        return TextStructure(result)

    def regex_undestand(self, text):
        """Extract intent and entities from a text
        based on regex expressions.
        """
        for intent in self.expressions:
            for expr in self.expressions[intent]:
                " Match text"
                p = re.compile(expr["regex"])
                found = p.findall(text)

                if found:
                    x = found[0]
                    if "" in x: x = [x]
                    entities = dict(zip(expr["entity_names"], x))
                    end = text.find(x[-1]) + len(x[-1])

                    return {
                        "text": text,
                        "expression": expr["value"],
                        "intent": intent,
                        "entities": entities,
                        "end": end
                    }
        return {
            "text": text,
            "expression": None,
            "intent":   None,
            "entities": {},
            "end": None
        }

    def find_CUSTOM_ENTITIES(self, text):
        """Extract entities from a text by matching them
        with the ones specifies in `custom_entities`.
        """
        text = text.lower()
        result = dict()
        for key, value in self.custom_entities.items():
            temp = []
            for entity in value:
                entity = entity.lower()
                start = text.find(entity)
                if start != -1:
                    end = start + len(entity)
                    temp.append(text[start:end])
                else:
                    pass
            if temp != []:
                result[key] = temp
        return result

    def find_spacy_entities(self, text):
        """Extract entities using spacy model.
        """
        result = dict()
        doc = self.spacy_nlp(text)
        try:
            for entity in doc.ents:
                name = self.spacy_ents[entity.label_]
                result[name] = []
            for entity in doc.ents:
                name = self.spacy_ents[entity.label_]
                result[name].append(entity.text)
        except KeyError:
            pass
        return result


if __name__ == '__main__':
    nlu = NaturalLanguageUnderstander()
    while True:
        text = input("Type your request: ")
        result = nlu.understand(text)
        print(result)
