import os
import sys

from .assistant import Assistant


def main():
    print("*** Activating assistant ***")
    on_server = os.uname()[1] == "raspberrypi"

    try:
        assistant = Assistant(name=sys.argv[1], on_server=on_server)
    except IndexError:
        assistant = Assistant(on_server=on_server)
    assistant.run()


if __name__ == "__main__":
    main()
