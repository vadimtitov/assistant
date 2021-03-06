import os
import re
import subprocess
import signal
import time
import random

import psutil
from threading import Thread

COLORS = {
    "HEADER": "\033[95m",
    "OKBLUE": "\033[94m",
    "OKGREEN": "\033[92m",
    "WARNING": "\033[93m",
    "FAIL": "\033[91m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
}


def chatbot_only(func):
    def wrapper(text, interface, assistant):
        if type(interface).__name__ == "TelegramBot":
            func(text, interface, assistant)

    return wrapper


def voice_only(func):
    def wrapper(text, interface, assistant):
        if type(interface).__name__ == "VoiceInterface":
            func(text, interface, assistant)

    return wrapper


def server_only(func):
    def wrapper(text, interface, assistant):
        if assistant.on_server:
            func(text, interface, assistant)

    return wrapper


def pc_only(func):
    def wrapper(text, interface, assistant):
        if not assistant.on_server:
            func(text, interface, assistant)

    return wrapper


def pick_phrase(phrases, me=""):
    return random.choice(phrases).replace("{me}", me)


def os_is_raspbian():
    return os.uname()[1] == "raspberrypi"


def get_my_ip(timeout=30):
    start_time = time.time()
    while time.time() - start_time <= timeout:
        try:
            with os.popen("ifconfig | grep 'inet 192'") as process:
                return re.findall(r"\d{3}\.\d{3}\.\d\.\d{2,3}", process.read())[0]
        except IndexError:
            pass

def device_is_charging():
    with os.popen(
        "upower -i /org/freedesktop/UPower/devices/battery_BAT0 | grep state"
    ) as process:
        return bool(
            re.findall(r"fully-charged| charging|^(?![\s\S])", process.read())
        )


def device_has_battery():
    with os.popen(
        "upower -i /org/freedesktop/UPower/devices/battery_BAT0 | grep power"
    ) as process:
        return "yes" in process.read()


def colored(text, color="WARNING", frame=True):
    if frame:
        x = "_" * len(text) + "\n"
        b = " " * len(text) + "\n"
        return (
            COLORS["BOLD"] + COLORS[color] + x + b + text + b + x + "\033[0m"
        )
    else:
        return COLORS["BOLD"] + COLORS[color] + text + "\033[0m"


def thread(targets, wait_to_finish=False):
    for target in targets:
        thr = Thread(target=target)
        thr.start()
        if wait_to_finish is True:
            thr.join()


def screen_is_locked():
    with os.popen("loginctl show-user | grep IdleHint") as process:
        if "yes" in process.read():
            return True
        else:
            return False


def turn_screen_off():
    os.system("sleep 0.01 && xset -display :0.0 dpms force off")


def set_output_as_headphones():
    os.system(
        'pacmd set-default-sink "alsa_output.pci-0000_00_1f.3.analog-stereo"'
    )


def get_volume():
    with os.popen("amixer -D pulse") as responce:
        volume = re.findall(r"Playback.+\[(\d{1,3})%\]", responce.read())[0]
    return int(volume)


def kill_process(process):
    p = subprocess.Popen(["ps", "-A"], stdout=subprocess.PIPE)
    out, err = p.communicate()
    for line in out.splitlines():
        if process in line.decode("utf-8"):
            pid = int(line.split(None, 1)[0])
            os.kill(pid, signal.SIGKILL)


def notification(
    message,
    title=" ",
    time=1000,
    icon="~/Dropbox/Jarvis/.icons/J.png",
    urgency="normal",
):
    command = 'notify-send "{}" "{}" -t {} -i {} -u {}'.format(
        title, message, time, icon, urgency
    )  # low, critical
    os.system(command)


def is_running(process_name):
    return process_name in (p.name() for p in psutil.process_iter())
