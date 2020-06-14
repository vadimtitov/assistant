import os
import sys

from .assistant import Assistant


def main():
    on_server = os.uname()[1] == "raspberrypi"

    try:
        name = sys.argv[1]
    except IndexError:
        name = "friday"

    print(f"*** Activating assistant {name}***")

    assistant = Assistant(name=name, on_server=on_server)
    assistant.run()


if __name__ == "__main__":
    main()
