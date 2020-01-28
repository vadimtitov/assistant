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
                             device_is_charging)

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
        activate_web_api=True
    ):
        if not on_server:
            assert not os_is_raspbian(), "You are running on raspberry pi but on_server=False."

        # set parameters
        self.name = name.lower()
        self._voice_activation = voice_activation
        self._activate_web_api = activate_web_api
        self._set_personality()
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
        if self._activate_web_api: self.web_api = WebAPI(self)
        self.bot = TelegramBot(self)

    def _set_personality(self):
        with open("assistant/custom/personalities.yaml") as yaml_file:
            self.personality = yaml.load(yaml_file)[self.name]
            self.me = self.personality["calls_me"]

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

        # don't assist on server if running on another device, e.g. laptop
        if all((
            self.on_server,
            self._is_running_on_other_local()
        )):
            return

        threading.Timer(
            interval=0.4,
            function=self._listen).start()
        threading.Thread(
            target=self._respond).start()

    def _is_running_on_other_local(self, timeout=0.08):
        LAPTOP_IP = "192.168.1.69"
        try:
            return requests.get(
                f"http://{LAPTOP_IP}:5000/status",
                timeout=timeout
            ).text == "active"
        except:
            return False

    def _on_press(self, key):
        """Function to call when assistant is called by button.
        """
        if key == keyboard.Key.f7:
            threading.Thread(
                target=self._listen).start()

    def _manage_power_saving(self):
        """If device is not charging, turn off
        keyword detector to save power.
        """
        self._keyword_detector_active = True
        while True:
            if device_is_charging():
                if not self._keyword_detector_active:
                    self.voice.output("Starting keyword recognition")
                    self.detector.start(self._on_call)
                    self._keyword_detector_active = True
            else:
                try:
                    if self._keyword_detector_active:
                        self.detector.terminate()
                        self._keyword_detector_active = False
                        self.voice.output(
                            "Keyword recognition disabled to save power")
                except AttributeError:
                    pass
            time.sleep(10)

    def run(self):
        """Runs the voice and key activation threads, telegram bot,
        web api and daemons specified in modules/daemons folder.
        """
        def run_voice_activator():
            self.detector.start(self._on_call)

        def run_key_activator():
            # no need for key activator on server version (for now)
            if self.on_server:
                return
            with keyboard.Listener(on_press=self._on_press) as listener:
                listener.join()

        targets = []
        if self._voice_activation:
            targets.append(run_voice_activator)

        if not self.on_server:
            targets.append(run_key_activator)
            targets.append(self._manage_power_saving)

        if self.on_server:
            targets.append(self.bot.run)

        if self._activate_web_api:
            targets.append(self.web_api.run)

        for target in targets:
            threading.Thread(target=target).start()

        if not self.on_server:
            pass
            # set some sigmal for pi to know you are running

        print(colored('Voice assistant: active', 'OKGREEN', frame = False))


if __name__ == '__main__':
    try:
        voice = False if "False" in sys.argv[2] else True
        assistant = Assistant(name = sys.argv[1], voice_activation = voice)
    except IndexError:
        assistant = Assistant()
    assistant.run()
