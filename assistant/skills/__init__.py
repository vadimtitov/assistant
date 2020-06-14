"Skills init."

import os
import importlib
import collections
from contextlib import suppress

# get file dir path
dir_path = os.path.dirname(os.path.realpath(__file__))

# get skill names
skill_names = [
    name.replace(".py", "") for name in os.listdir(dir_path)
    if not name.startswith("_") and (name.endswith(".py") or "." not in name)
]

expressions = collections.OrderedDict()
entities = {}

for name in skill_names:
    # import skill by name
    skill = importlib.import_module(f".{name}", __name__)

    # update regular expression for a skill
    expressions.update(skill.regex)

    # update custom entitites if defined in a skill
    with suppress(AttributeError):
        entities.update(skill.entities)

    # update defined skill functions
    globals().update({
        key: attr for key, attr in skill.__dict__.items()
        if not key.startswith("_") and callable(attr)
    })


class Skills:

    def __init__(self, assistant):
        self.assistant = assistant

    def handle(self, text_struct, interface):
        """Call the skill function that corresponds to intent from text_struct."""
        # unknown intent
        if text_struct.text == ' ': return

        print(text_struct)

        if text_struct.intent:
            # run the function which name matches the intent name
            skill = globals()[text_struct.intent]
            skill(text_struct, interface, self.assistant)
