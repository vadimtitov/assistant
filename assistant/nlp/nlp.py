#!/usr/bin/env python3

import re

from .nlu import NaturalLanguageUnderstander


class NaturalLanguageProcessor(object):

    def __init__(self):
        self.nlu = NaturalLanguageUnderstander()
        self.completed = []
        self.previous = []

    def structs(self, text):
        """Returns a generator of one or more TextStructure objects each of which
        corresponds to a unique intent found in the text.
        """
        for item in self.completed:
            text = text.replace(item.text, '')
        parts = re.split(' and also | and | also ', text)
        for part in parts:
            yield self.nlu.understand(part)

    def context_structs(self, text):
        for struct in self.structs(text):
            pass #if struct.intent is None and struct.similarTo:


if __name__ == '__main__':
    nlp = NaturalLanguageProcessor()
    while True:
        text = input("Type your request: ")

        print(list(nlp.structs(text)))

        #nlp.finalAssist(text)
