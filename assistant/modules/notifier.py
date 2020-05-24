"""Module to show user updatable system notifications."""

import os

if os.uname()[1] == "raspberrypi":

    class Notifier:
        """Dummy notifier class - no notifications on Raspberry Pi."""

        def new(self, text):
            pass

        def update(self, text):
            pass

        def close(self):
            pass

        def quick(self, title, text, duration):
            pass


else:
    # pgi module is designed to work in virtual environment
    assert (
        "VIRTUAL_ENV" in os.environ
    ), "You are not using virtual environment!"

    import time
    import pgi
    from pgi.repository import Notify

    pgi.require_version("Notify", "0.7")
    Notify.init("Test")

    class Notifier:
        """Simple interface for updatable system notifications."""

        def __init__(
            self,
            title=" ",
            text="Listening...",
            icon="~/Dropbox/Jarvis/.icons/J.png",
        ):
            self.icon = icon
            self.notification = Notify.Notification.new(title, text, icon)
            self.notification.set_urgency(2)

        def new(self, text):
            """Show new notification."""
            self.notification.show()
            self.update(text)

        def update(self, text):
            """Update existing notification."""
            self.notification.update(" ", text, self.icon)
            self.notification.show()

        def close(self):
            """Close existing notification"""
            self.notification.close()

        def quick(self, title, text, duration=5):
            """Show a notification and close it after specifier duration."""
            self.new(text)
            time.sleep(duration)
            self.close()
