#!/usr/bin/env python3

import os
import time
import requests
import random
import traceback
import yaml
import threading

from assistant.modules.snowboy import snowboydecoder
from assistant.nlp import NaturalLanguageProcessor
from assistant.skills import Skills
from assistant.modules.notifier import Notifier

from assistant.interfaces import VoiceInterface, TelegramBot, WebAPI
from assistant.utils import (
    colored,
    os_is_raspbian,
    device_is_charging,
    device_has_battery,
    get_my_ip,
)
from assistant.custom import wrappers


if not os_is_raspbian():
    from pynput import keyboard


class Assistant(object):
    """The main assistant class."""

    def __init__(
        self, name="friday", on_server=False, voice_activation=True,
    ):
        if not on_server:
            assert (
                not os_is_raspbian()
            ), "You are running on raspberry pi but on_server=False."

        # set parameters
        self.name = name.lower()
        self._voice_activation = voice_activation
        self._keyword_detector_active = False
        self.on_server = on_server

        self._set_personality()
        self._set_ecosystem()

        # initialize hotword detector
        self.detector = snowboydecoder.HotwordDetector(
            "assistant/custom/snowboy_models/"
            + self.personality["keyword_file"],
            sensitivity=self.personality["sensitivity"],
            audio_gain=1,
        )
        self.detector_locked = False

        # initialize componets
        self.nlp = NaturalLanguageProcessor()
        self.skills = Skills(self)
        self.notifier = Notifier()

        # initialize interfaces
        self.web_api = WebAPI(self)
        self.bot = TelegramBot(self)
        self.voice = VoiceInterface(
            notifier=self.notifier, voice=self.personality["polly_voice"]
        )

        self.voice.output("Hello")


    def _activate_keyword_detector(self):
        while self.detector_locked:
            time.sleep(0.5)
        if not self._keyword_detector_active:
            self._keyword_detector_active = True
            self.detector.start(self._on_call)

    def _terminate_keyword_detector(self):
        while self.detector_locked:
            time.sleep(0.5)
        if self._keyword_detector_active:
            self._keyword_detector_active = False
            try:
                self.detector.terminate()
            except AttributeError:
                pass

    def _set_personality(self):
        with open("assistant/custom/personalities.yaml") as file:
            self.personality = yaml.safe_load(file)[self.name]
            self.me = self.personality["calls_me"]
            path = (
                "assistant/custom/call_responds/"
                + self.personality["responds_folder"]
            )
            self.response_filenames = os.listdir(path)

    def _set_ecosystem(self):
        with open("assistant/custom/ecosystem_config.yaml") as file:
            devices = yaml.safe_load(file)["devices"]

        # find current device priority
        my_ip = get_my_ip()
        for _, params in devices.items():
            if params["ip"] == my_ip:
                my_priority = params["priority"]
                print("my priority:", my_priority)
                break
            else:
                my_priority = 1  # ?

        # find devices with higher priority
        self.higher_priority_ips = []
        for _, params in devices.items():
            if params["priority"]:
                print(params)

                if params["priority"] < my_priority:
                    self.higher_priority_ips.append(params["ip"])
        print("higher ips:", self.higher_priority_ips)

    def _is_main_listener(self):
        for ip in self.higher_priority_ips:
            try:
                if (
                    requests.get(f"http://{ip}:5000/status", timeout=1).text
                    == "active"
                ):
                    return False
            except (
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
                ConnectionRefusedError,
            ):
                print(ip, "is not active")
        return True

    def _pick_main_detector(self):
        """Activate keyword detector only if current device
        has highest priority within the network."""

        while True:
            if self._is_main_listener():
                print("You are main listener!")
                self._activate_keyword_detector()
            else:
                print("You are not main listener!")
                self._terminate_keyword_detector()
            time.sleep(10)

    def fast_assist(self, text):
        """Process NL text if it has enough information (is_complete)."""
        for struct in self.nlp.structs(text):
            if struct.is_complete() and struct not in self.nlp.completed:
                self.skills.handle(text_struct=struct, interface=self.voice)
                self.nlp.completed.append(struct)

    def final_assist(self, text):
        """Process NL text even if it does not contain
        enough information (assume or do nothing).
        """
        for struct in self.nlp.structs(text):
            if struct not in self.nlp.completed:
                self.skills.handle(text_struct=struct, interface=self.voice)
                self.nlp.completed.append(struct)
        self.nlp.previous = self.nlp.completed
        self.nlp.completed = []

    def _respond(self):
        """Play a random pre-recorded voice response from
        call_responds folder when assistant is called by keyword.
        """
        path = (
            "assistant/custom/call_responds/"
            + self.personality["responds_folder"]
        )
        response_file = random.choice(self.response_filenames)
        os.system(f"mpg123 {path}/{response_file}")

    @wrappers.wrap_listen
    def _listen(self):
        """Initiates streaming speech recognition and
        natural language processor when assistant is called.
        """
        self.detector_locked = True
        # let the speech recognizer use the microphone
        if self._keyword_detector_active:
            self.detector.terminate()

        try:
            self.voice.recognize_as_stream(self.fast_assist, self.final_assist)
        except Exception:
            traceback.print_exc()
            self.notifier.close()
            self.voice.output("Error occured.")

        # if listener was active then activate it
        if self._keyword_detector_active:
            self.detector.start(self._on_call)
        self.detector_locked = False

    def _on_call(self):
        """Function to call when assistant is called by voice."""
        threading.Timer(interval=0.4, function=self._listen).start()
        threading.Thread(target=self._respond).start()

    def _manage_power_saving(self):
        """Turn off keyword detector when device
        is not chargingto save power.
        """
        return  # currently disabled
        while True:
            if device_is_charging():
                self._activate_keyword_detector()
            else:
                self._terminate_keyword_detector()
            time.sleep(10)

    def _activate_key_listener(self):
        def on_press(key):
            if key == keyboard.Key.f7:
                threading.Thread(target=self._listen).start()

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    @wrappers.wrap_run
    def run(self):
        """Run assistant threads."""
        targets = [self.web_api.run]

        if self._voice_activation:
            targets.append(self._activate_keyword_detector)
            if self.higher_priority_ips:
                targets.append(self._pick_main_detector)

        if not self.on_server:
            targets.append(self._activate_key_listener)
            if device_has_battery():
                targets.append(self._manage_power_saving)
        else:
            targets.append(self.bot.run)

        for target in targets:
            threading.Thread(target=target).start()

        print(colored("Voice assistant: active", "OKGREEN", frame=False))
