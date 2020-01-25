
import os
import random

from ...utils import pick_phrase

regex = {
    "add_skill": [
        "(?:new|add) skill as(?: a)? <type> name(?: it)? <<name>>",
        "(?:new|add) skill name(?: it)? <<name>>",
        "(?:new|add) skill as(?: a)? <type>",
        "(?:new|add) skill"
    ]
}

ask_name = [
    "How would you like to name it?",
    "And how do I name it?",
    "And the name for the skill?",
    "How do you wish to name this skill?"
]

positive_responces = {
    "yes", "yeah", "yep",
    "that's right", "that is right",
    "that's correct", "that is correct"
}

done = [
    "done", "done {me}", "created",
    "here we go", "roger that", "simple magic",
    "tadam", "voila", "there it is"
]

def add_skill(text, interface, assistant):

    if "type" not in text.entities:
        while True:
            answer = interface.input(
                "file or folder?",
                regex=r"file|folder")
            if "file" in answer:
                text.entities["type"] = "file"
                break
            elif "folder" in answer:
                text.entities["type"] = "folder"
                break
            else:
                interface.output("I didn't get that.")

    if "name" not in text.entities:
        name = interface.input(
            random.choice(ask_name)
        )
        name = __filter_name(name)

        while True:
            result = interface.input(f"{name}. Is that correct?")

            if any(item in result for item in positive_responces):
                break
            else:
                name = interface.input(
                    random.choice(ask_name)
                )
                name = __filter_name(name)
        text.entities["name"] = name

    text.entities["name"] = text.entities["name"].replace(" ", "_")

    __create_skill(
        name=text.entities["name"].lower(),
        type=text.entities["type"]
    )
    interface.output(
        pick_phrase(done, assistant.me)
    )


def __create_skill(name, type):
    path = "assistant/skills"

    with open(f"{path}/add_skill/sample_skill.txt") as file:
        sample_content = file.read()

    if type == "file":
        file_path = f"{path}/{name}.py"
        # create .py file
        with open(file_path, "w") as file:
            content = sample_content.replace("{skill}", name)
            file.write(content)

    elif type == "folder":
        dir = f"{path}/{name}"
        file_path = f"{dir}/{name}.py"
        os.mkdir(dir)

        # create init file
        with open(f"{path}/add_skill/sample_init.txt") as file:
            sample_init = file.read()

        with open(f"{dir}/__init__.py", "w") as file:
            content = sample_init.replace("{skill}", name)
            file.write(content)

        # create .py file
        with open(f"{dir}/{name}.py", "w") as file:
            content = sample_content.replace("{skill}", name)
            file.write(content)

    # open file in atom
    os.system(f"atom {file_path}")


def __filter_name(name):
    filter_out = ("a ", "name", " it ", "maybe", "let ")
    for item in filter_out:
        name.replace(item, "")
    return name.strip()
