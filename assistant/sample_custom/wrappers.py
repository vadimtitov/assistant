"""Host custom Assistant.listen method wrapper."""


def wrap_run(func):
    """Wrap Assistant.run to enable custom actions before running assistant."""
    def wrapper(*args, **kwargs):
        # insert what to do before running assistant
        func(*args, **kwargs)
    return wrapper


def wrap_listen(func):
    """Wrap Assistant.listen to enable custom actions before/after listening."""
    def wrapper(*args, **kwargs):
        # insert what to do before assistant starts listening
        func(*args, **kwargs)
        # insert what to do after
    return wrapper


def wrap_voice_output(func):
    """Wrap Assistant.voice.output to enable custom actions for voice output."""
    def wrapper(*args, **kwargs):
        # insert what to do before assistant starts talking
        func(*args, **kwargs)
        # insert what to do after

    return wrapper
