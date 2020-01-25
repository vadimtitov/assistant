
import sys

print("*** Activating assistant ***")
from .assistant import Assistant

try:
    voice = False if "False" in sys.argv[2] else True

    assistant = Assistant(
        name = sys.argv[1],
        voice_activation = voice,
        on_server=False
    )
except IndexError:
    assistant = Assistant()

assistant.run()
