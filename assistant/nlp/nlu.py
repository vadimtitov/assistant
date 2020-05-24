#!/usr/bin/env python3

import re

from .text_structure import TextStructure
from ..skills import expressions, entities


def prepare_regex_expressions():
    """Convert expressions defined in skills
    into a proper regex format.
    """
    processed_exprs = {}
    entities_regex = re.compile(r"<{1,2}(.*?)>{1,2}")

    for intent, exprs in expressions.items():
        for expr in exprs:
            # extract entities
            entity_names = re.findall(entities_regex, expr)

            # create search regex
            regex = re.sub(r"<<.*?>>", r"(.*)", expr)  # "(.*?)"
            regex = re.sub(r"<.*?>", r"([a-zA-Z0-9_]*)", regex)

            result = {
                "value": expr,
                "regex": regex,
                "entity_names": entity_names,
            }
            try:
                processed_exprs[intent].append(result)
            except KeyError:
                processed_exprs[intent] = [result]
    return processed_exprs


processed_exprs = prepare_regex_expressions()


class NaturalLanguageUnderstander:
    """One-off Natural Language Understander.
    """

    def __init__(self, expressions=processed_exprs, custom_entities=entities):
        self.expressions = expressions
        self.custom_entities = custom_entities

    def understand(self, text):
        """Returns an TextStructure object that will contain
        intent, entitites, etc. of inputted text.
        """
        text = text.lower()
        result = self.regex_undestand(text)

        # custom entitites update (they are complete/final by default)
        custom_entities = self.find_custom_entities(text)
        result["entities"].update(custom_entities)
        result.update({"complete_entities": set(custom_entities.keys())})

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
                    if "" in x:
                        x = [x]
                    entities = dict(zip(expr["entity_names"], x))
                    end = text.find(x[-1]) + len(x[-1])

                    return {
                        "text": text,
                        "expression": expr["value"],
                        "intent": intent,
                        "entities": entities,
                        "end": end,
                    }
        return {
            "text": text,
            "expression": None,
            "intent": None,
            "entities": {},
            "end": None,
        }

    def find_custom_entities(self, text):
        """Extract entities from a text by matching them
        with the ones specifies in `custom_entities`.
        """
        result = dict()

        for key, ents in self.custom_entities.items():
            regex = "|".join(ents)
            match = re.findall(regex, text)

            if match:
                result.update({key: match[0]})

        return result


if __name__ == "__main__":
    nlu = NaturalLanguageUnderstander()
    while True:
        text = input("Type your request: ")
        result = nlu.understand(text)
        print(result)
