#!/usr/bin/env python3

import sys
import os
import subprocess
import time
import requests
import random
import traceback
import yaml
import threading

from assistant.modules.snowboy import snowboydecoder
from assistant.nlp import NaturalLanguageProcessor
from assistant.skills import Skills

from assistant.interfaces import (VoiceInterface,
                                  TelegramBot,
                                  WebAPI)
from assistant.utils import (colored,
                             os_is_raspbian,
                             device_is_charging,
                             device_has_battery,
                             get_my_ip)

if not os_is_raspbian():
    from pynput import keyboard


class Assistant(object):
    """The main assistant class.
    * Assistant can have several personalities which are passed as a 'name'
      variable which can be specified in modules/personalities.yaml file
    * Voice activation can be switched off for battery saving purposes.
    """
    def __init__(
        self,
        name="friday",
        on_server=False,
        voice_activation=True,
    ):
        if not on_server:
            assert not os_is_raspbian(), "You are running on raspberry pi but on_server=False."

        # set parameters
        self.name = name.lower()
        self._voice_activation = voice_activation
        self._keyword_detector_active = False

        self._set_personality()
        self._set_ecosystem()
        self.on_server = on_server

        # initialize hotword detector
        self.detector = snowboydecoder.HotwordDetector(
            "assistant/custom/snowboy_models/" + self.personality['keyword_file'],
            sensitivity=self.personality["sensitivity"],
            audio_gain=1
        )

        # initialize componets
        self.nlp = NaturalLanguageProcessor()
        self.skills = Skills(self)

        # initialize interfaces
        self.voice = VoiceInterface(voice=self.personality["polly_voice"])
        self.web_api = WebAPI(self)
        self.bot = TelegramBot(self)

    def _activate_keyword_detector(self):
        if not self._keyword_detector_active:
            self._keyword_detector_active = True
            self.detector.start(self._on_call)

    def _terminate_keyword_detector(self):
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

    def _set_ecosystem(self):
        with open("assistant/custom/ecosystem_config.yaml") as file:
            devices = yaml.safe_load(file)["devices"]

        # find current device priority
        my_ip = get_my_ip()
        for _, params in devices.items():
            if params["ip"] == my_ip:
                my_priority = params["priority"]
                print("my priority:", my_priority)

        # find devices with higher priority
        self.higher_priority_ips = []
        for _, params in devices.items():
            if params["priority"]:
                if params["priority"] < my_priority:
                    self.higher_priority_ips.append(params["ip"])
        print("Higher ips:", self.higher_priority_ips)

    def _is_main_listener(self):
        for ip in self.higher_priority_ips:
            try:
                if requests.get(
                    f"http://{ip}:5000/status",
                    timeout=1
                ).text == "active":
                    return False
            except: # (ConnectionRefusedError, ConnectTimeoutError)
                print(ip, "is not active")
        return True

    def _pick_main_detector(self):
        """If assistant runs on multiple devices on the same network
        only activate keyword detector for the one with highest priority.
        """
        while True:
            if self._is_main_listener():
                print("You are main listener!")
                self._activate_keyword_detector()
            else:
                print("You are not main listener!")
                self._terminate_keyword_detector()
            time.sleep(10)

    def fast_assist(self, text):
        """Calls handle funtion if text has enough
        information (is_complete) to do so.
        """
        for struct in self.nlp.structs(text):
            if struct.is_complete() and struct not in self.nlp.completed:
                self.skills.handle(
                    text_struct = struct,
                    interface = self.voice
                )
                self.nlp.completed.append(struct)

    def final_assist(self, text):
        """Calls handle function even if there is not enough
        info in the text, handle function will then either
        assume lacking information or do nothing.
        """
        for struct in self.nlp.structs(text):
            if struct not in self.nlp.completed:
                self.skills.handle(
                    text_struct = struct,
                    interface = self.voice
                )
                self.nlp.completed.append(struct)
        self.nlp.previous = self.nlp.completed
        self.nlp.completed = []

    def _respond(self):
        """Plays a random pre-recorded voice response from
        call_responds folder when assistant is called by keyword.
        """
        path = "assistant/custom/call_responds/" +\
            self.personality["responds_folder"]

        respond = random.choice(os.listdir(path))
        os.system(f'mpg123 {path}/{respond}')

    def _listen(self):
        """Initiates streaming speech recognition and
        natural language processor when assistant is called.
        """
        # let the speech recognizer use the microphone
        self.detector.terminate()

        try:
            self.voice.recognize_as_stream(
                self.fast_assist,
                self.final_assist)
        except Exception:
            traceback.print_exc()
            self.voice.output("Error occured.")

        self.detector.start(self._on_call)

    def _on_call(self):
        """Functions to call when assistant is called by voice.
        """
        #if not on raspberry
        #keyboard.press('ctrl') # to activate screen
        #os.system("pkill mpg123") # stop assistant if it was talking
        threading.Timer(
            interval=0.4,
            function=self._listen).start()
        threading.Thread(
            target=self._respond).start()

    def _manage_power_saving(self):
        return
        """If device is not charging, turn off
        keyword detector to save power.
        """
        while True:
            if device_is_charging():
                self._activate_keyword_detector()
            else:
                self._terminate_keyword_detector()
            time.sleep(10)

    def _activate_key_listener(self):
        # no need for key activator on server version (for now)
        def on_press(key):
            if key == keyboard.Key.f7:
                threading.Thread(
                    target=self._listen).start()

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    def run(self):
        """Runs the voice and key activation threads,
        telegram bot and web api.
        """
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

        print(colored('Voice assistant: active', 'OKGREEN', frame = False))
