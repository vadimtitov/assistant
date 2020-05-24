import os

from pynput.keyboard import Controller, Key  # noqa: F401


COMMANDS = {
    "play": "xdotool key XF86AudioPlay",
    "pause": "xdotool key XF86AudioPlay",
    "next": "xdotool key XF86AudioNext",
    "previous": "xdotool key XF86AudioPrev",
    "mute": "xdotool key XF86AudioMute",
    "voldown": "xdotool key XF86AudioLowerVolume",
    "volup": "xdotool key XF86AudioRaiseVolume",
}


class Keyboard:
    def __init__(self):
        self.keyboard = Controller()

    def press(self, command):
        keys = command.split("+")
        for key in keys:
            try:  # maybe it is a key
                exec(f"self.keyboard.press(Key.{key})")
            except AttributeError:
                try:  # maybe it is letter
                    self.keyboard.press(key)
                except ValueError:
                    # media key
                    os.system(COMMANDS[command])

        for key in keys:
            try:
                exec(f"self.keyboard.release(Key.{key})")
            except AttributeError:
                try:
                    self.keyboard.release(key)
                except ValueError:
                    pass

    def type(self, text):
        self.keyboard.type(text)
