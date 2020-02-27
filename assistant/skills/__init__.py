"Skills init."

import os

# get file dir path
dir_path = os.path.dirname(os.path.realpath(__file__))

# get skill names
skill_names = [name.replace(".py", "") for name in os.listdir(dir_path)]
skill_names.remove("__init__")
skill_names.remove("__pycache__")

expressions = {}
entities = {}

for skill in skill_names:
    # get a dictionary of every skill's regex expression
    exec(f"from .{skill} import regex")
    expressions.update(regex)

    # get custom entitites defined in skills
    try:
        exec(f"from .{skill} import entities as ents")
        entities.update(ents)
    except ImportError:
        pass

    # get skill functions
    exec(f"from .{skill} import *")


class Skills:

    def __init__(self, assistant):
        self.assistant = assistant

    def handle(self, text_struct, interface):
        """Call the skill function that corresponds to intent from text_struct."""
        # unknown intent
        if text_struct.text == '' or text_struct.text == ' ':
            return

        print(text_struct)

        if text_struct.intent:
            # run the function which name matches the intent name
            exec(
                f"{text_struct.intent}(text_struct, interface, self.assistant)"
            )
