"""Telegram bot configuration variables."""

# telegram bot token
TOKEN = ""

# who do you trust your bot to? (provide telegram chat id as integer)
ALLOWED_USERS_DICT = {"admin": 123, "charlie": 666}  # this is your chat id

# custom telegram bot keyboard (can be any shape)
KEYBOARD = [["a", "b", "c"], ["", "", ""], ["", "", ""], ["", "", ""]]

# for each key provide a command to be executed with exec()
KEYS_ACTIONS = {"a": "print('a')", "b": "print('b')", "c": "print('c')"}
