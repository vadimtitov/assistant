"""Telegram bot interface."""

import os
import time
import secrets

import telegram
from telegram.ext import (Updater,
                          CommandHandler,
                          MessageHandler,
                          Filters)

from assistant.utils import *

# we import all to include custom functions/objects
# but mainly we import TOKEN, ALLOWED_USERS_DICT, KEYBOARD, KEYS_ACTIONS
from assistant.custom.telegram_config import *

KEYS = set(key for row in KEYBOARD for key in row)
ALLOWED_USERS = ALLOWED_USERS_DICT.keys()
ADMIN_ID = ALLOWED_USERS_DICT["admin"]


def user_is_allowed(bot, update):
    allowed_ids = {ALLOWED_USERS_DICT[user] for user in ALLOWED_USERS}
    if update.message.chat_id in allowed_ids:
        return True
    return False


def handle_buttons(bot, update):
    text = update.message.text
    if  text in KEYS:
        exec(KEYS_ACTIONS[text])
        return True


class TelegramBot(Updater):
    """Telegram bot interface."""

    def __init__(
        self,
        assistant,
        token=TOKEN,
        admin_id=ADMIN_ID,
        allowed_users=ALLOWED_USERS_DICT
    ):
        """Init."""
        Updater.__init__(self, token=token)

        self.assistant = assistant
        self.admin_id = admin_id
        self.users = allowed_users

        self.nlp = assistant.nlp

    @property
    def last_id(self):
        try:
            return self.last_update.message.chat_id
        except NameError:
            return self.users["admin"]

    def _send_keyboard(self, update, text="Custom keyboard."):
        """Send custom keyboard to a user from `update`"""
        reply_markup = telegram.ReplyKeyboardMarkup(KEYBOARD)
        self.bot.send_message(
            chat_id=update.message.chat_id,
            text=text,
            reply_markup=reply_markup)

    def handle_text(self, text):
        """Calls handle function even if there not enough
        info in the text, handle function will then
        either assume the lacking information or do nothing.
        """

        for struct in self.nlp.structs(text):
            if struct not in self.nlp.completed:
                self.assistant.skills.handle(
                    text_struct = struct,
                    interface = self
                )
                self.nlp.completed.append(struct)
        self.nlp.previous = self.nlp.completed
        self.nlp.completed = []

    def handle_message(self, bot, update):
        """A text message handler method."""
        self._describe_message(update)

        if user_is_allowed(bot, update):
            self.last_update = update

            text = update.message.text
            print(text)

            if not handle_buttons(bot, update):
                self.handle_text(text)
        else:
            self.output(
                text="Access denied.",
                chat_id=update.message.chat_id
            )

    def _describe_message(self, update):
        if not update.message.chat.first_name:
            update.message.chat.first_name = ''
        if not update.message.chat.last_name:
            update.message.chat.last_name = ''

        name = colored(update.message.chat.first_name + ' ' +
                       update.message.chat.last_name, 'OKBLUE',
                       frame = False)
        sender_id = update.message.chat_id
        report = f'{name} ({sender_id}): {update.message.text}'
        print(report)

    def input(self, text, regex=None, chat_id=None):
        if not chat_id: chat_id = self.last_id
        print(" *** UPDATES ***")
        print(self.bot.get_updates())

        last_message_id = self.bot.get_updates()[-1].message.message_id
        self.bot.send_message(chat_id=chat_id, text=text)

        # wait for the answer
        while True:
            update = self.bot.get_updates()[-1]
            if all(
                update.message.message_id != last_message_id,
                update.message.chat_id == chat_id
            ):
                return update.message.text
            time.sleep(0.1)

    def output(self, text, chat_id=None, prob=1):
        if prob is 1 or random.random() < prob:
            if not chat_id:
                chat_id = self.last_id
            self.bot.send_message(chat_id=chat_id, text=text)

    def run(self):
        """Run telegram bot."""
        print(colored('Telegram bot: active', 'OKGREEN',frame = False))
        text_message_handler = MessageHandler(Filters.text, self.handle_message)
        self.dispatcher.add_handler(text_message_handler)
        self.start_polling(clean=True)
