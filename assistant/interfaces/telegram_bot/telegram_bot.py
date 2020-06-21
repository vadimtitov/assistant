"""Telegram bot interface."""

import time
import random
import requests

import telegram
from telegram.ext import (
    Updater,
    MessageHandler,
    CommandHandler,
    Filters,
)

from assistant.utils import colored

from assistant.custom.telegram_config import (
    TOKEN,
    ALLOWED_USERS_DICT,
    KEYBOARD,
    KEYS_ACTIONS,
)
# custom functions/objects
from assistant.custom.telegram_config import *   # noqa: F403, F401


KEYS = set(key for row in KEYBOARD for key in row)


def handle_buttons(bot, update):
    text = update.message.text
    if text in KEYS:
        exec(KEYS_ACTIONS[text])
        return True


def get_full_name(update):
    name = (update.message.chat.first_name, update.message.chat.last_name)
    return " ".join(w for w in name if w)


def allowed_users_only(func):
    def wrapper(self, bot, update):
        if update.message.chat_id in ALLOWED_USERS_DICT.values():
            func(self, bot, update)
        else:
            bot.send_message(text="Access denied.",
                             chat_id=update.message.chat_id)
            # let admin know
            msg = (
                "Unauthorized user "
                f"{get_full_name(update)}({update.message.chat_id}) "
                f"sent message: {update.message.text}"
            )
            bot.send_message(text=msg, chat_id=ALLOWED_USERS_DICT["admin"])
    return wrapper


class TelegramBot(Updater):
    """Telegram bot interface."""

    def __init__(
        self,
        assistant,
        token=TOKEN,
        allowed_users=ALLOWED_USERS_DICT,
    ):
        """Init."""
        Updater.__init__(self, token=token)

        self.assistant = assistant
        self.admin_id = allowed_users["admin"]
        self.users = allowed_users
        self.nlp = assistant.nlp

    @property
    def last_id(self):
        try:
            return self.last_update.message.chat_id
        except NameError:
            return self.users["admin"]

    @allowed_users_only
    def send_keyboard(self, bot, update):
        """Send custom keyboard to user"""
        reply_markup = telegram.ReplyKeyboardMarkup(KEYBOARD)
        bot.send_message(
            chat_id=update.message.chat_id,
            text="Custom keyboard",
            reply_markup=reply_markup,
        )

    @allowed_users_only
    def handle_message(self, bot, update):
        """A text message handler method."""
        self._describe_message(update)
        self.last_update = update

        text = update.message.text
        print(text)

        if not handle_buttons(bot, update):
            self._handle_text(text)

    @allowed_users_only
    def handle_voice(self, bot, update):
        self.last_update = update
        voice_bytes = bytes(
            update.message.voice.get_file(
            ).download_as_bytearray()
        )
        text = self.assistant.voice.recognize_from_bytes(voice_bytes)
        self._handle_text(text)

    def _handle_text(self, text):
        """Calls handle function even if there not enough
        info in the text, handle function will then
        either assume the lacking information or do nothing.
        """

        for struct in self.nlp.structs(text):
            if struct not in self.nlp.completed:
                self.assistant.skills.handle(
                    text_struct=struct, interface=self
                )
                self.nlp.completed.append(struct)
        self.nlp.previous = self.nlp.completed
        self.nlp.completed = []

    def _describe_message(self, update):
        name = colored(
            get_full_name(update),
            "OKBLUE",
            frame=False,
        )
        sender_id = update.message.chat_id
        report = f"{name} ({sender_id}): {update.message.text}"
        print(report)

    def input(self, text, regex=None, chat_id=None):
        if not chat_id:
            chat_id = self.last_id
        print(" *** UPDATES ***")
        print(self.bot.get_updates())

        last_message_id = self.bot.get_updates()[-1].message.message_id
        self.bot.send_message(chat_id=chat_id, text=text)

        # wait for the answer
        while True:
            update = self.bot.get_updates()[-1]
            if all(
                update.message.message_id != last_message_id,
                update.message.chat_id == chat_id,
            ):
                return update.message.text
            time.sleep(0.1)

    def output(self, text, chat_id=None, prob=1):
        if prob == 1 or random.random() < prob:
            if not chat_id:
                chat_id = self.last_id
            self.bot.send_message(chat_id=chat_id, text=text)

    def run(self):
        """Run telegram bot."""
        print(colored("Telegram bot: active", "OKGREEN", frame=False))
        text_message_handler = MessageHandler(
            Filters.text, self.handle_message
        )
        voice_message_handler = MessageHandler(
            Filters.voice, self.handle_voice
        )
        keyboard_handler = CommandHandler("keyboard", self.send_keyboard)

        self.dispatcher.add_handler(text_message_handler)
        self.dispatcher.add_handler(voice_message_handler)
        self.dispatcher.add_handler(keyboard_handler)

        self.start_polling(clean=True)
