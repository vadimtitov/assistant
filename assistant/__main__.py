import os
import sys

print("*** Activating assistant ***")
from .assistant import Assistant

on_server = os.uname()[1] == "raspberrypi"

try:
    assistant = Assistant(
        name = sys.argv[1],
        on_server=on_server
    )
except IndexError:
    assistant = Assistant(
        on_server=on_server
    )
assistant.run()
