import re, yaml
from tabulate import tabulate

from ..skills import expressions


class TextStructure(object):
    """Text structure object takes the output of 'NLU.understand' function
    and initializes a convenient to-use object
    """

    def __init__(self, result):
        self.text = result['text']
        self.intent, self.subintent = None, None
        try:
            intent = result['intent']
            if "." in intent:
                self.intent, self.subintent = intent.split(".")
            else:
                self.intent = intent
        except (KeyError, TypeError):
            pass
        self.entities = result['entities']
        self.complete_entities = result["complete_entities"]
        self.expression = result["expression"]
        self.end = result["end"]

    def __str__(self):
        result = [
            ["text", self.text],
            ["intent", self.intent],
            ["subintent", self.subintent],
            ["entities", self.entities],
            ["complete", self.is_complete()]
        ]
        return tabulate(result, tablefmt = "fancy_grid") #rst

    def __eq__(self, other):
        return all((self.intent == other.intent,
            self.subintent == other.subintent,
            self.entities == other.entities
        ))

    def update(self, other):
        """Merge entities of two text structures.
        Input 'result' overwrites the existing 'self'
        if the same entities appear. Used for contextual NLU.
        """
        if self.intent is None and other.intent is not None:
            self.intent = other.intent
            self.confidence = other.confidence
        for key in other.entities:
            if key in self.entities:
                self.text.replace(self.entities[key], other.entities[key])
        self.entities.update(other.entities)

    def is_similar_to(self, other):
        """Checks if all new entity names from _other_ are in _self_.
        Used for contextual NLU.
        """
        new = set(other.entities)
        old = set(self.entities)
        return new.issubset(old)

    def is_complete(self):
        """Returns True if the string has all the information
        required to perform an action.
        Used for FastAssist feature.
        """
        if not self.intent:
            return False

        if self.subintent:
            similar_expr = expressions[".".join((self.intent, self.subintent))]
        else:
            similar_expr = expressions[self.intent]

        # if intent has no entities at all:
        if all("<" not in e for e in similar_expr):
            return True

        # if all required entities are present
        required_entities = set(re.findall(r"<{1,2}(.*?)>{1,2}", similar_expr[0]))

        if self.complete_entities == required_entities:
            return True

        present_entities = set(self.entities.keys())
        if required_entities.issubset(present_entities):
            # if all entities are fixed <>
            if all("<<" not in e for e in similar_expr):
                return True
            # if last entity is <> and?
            if "<<" not in re.findall(r"<{1,2}.*?>{1,2}", self.expression)[-1]:
                return True
            # if last is <<>> and string is longer than postion of last >>
            if self.end < len(self.text) and self.text[-1] != "a":
                print(self.end, len(self.text))
                return True
        return False
