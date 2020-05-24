import os
import _thread
import socket
import webbrowser

from flask import Flask, request
from assistant.utils import colored

app = Flask(__name__)


class WebAPI:
    def __init__(self, _assistant):
        global assistant
        assistant = _assistant

    @app.route("/<request>")
    def get(request):
        if request == "status":
            return "active"

        if request == "kill":
            print("kill bitch")
            _thread.interrupt_main()
            return "killed"

    @app.route("/telegram/<method>", methods=["POST"])
    def telegram(method):
        payload = request.get_json()

        if method == "output":
            assistant.bot.output(
                text=payload["text"], chat_id=payload["chat_id"]
            )

        return "_"

    @app.route("/voice/<method>", methods=["POST"])
    def voice(method):
        payload = request.get_json()

        if method == "output":
            assistant.voice.output(text=payload["text"])

    @app.route("/web_browser/<method>", methods=["POST"])
    def web_browser(method):
        payload = request.get_json()

        if method == "open":
            webbrowser.open(payload["url"])

        return "_"

    @app.route("/system/<method>/<command>", methods=["POST"])
    def system_control(method, command):
        # payload = request.get_json()

        print(method, command)

        if method == "volume":
            if command == "up":
                os.system("xdotool key XF86AudioRaiseVolume")
            elif command == "down":
                os.system("xdotool key XF86AudioLowerVolume")
            elif command == "set":
                pass
                # payload = request.get_json()
                # payload["level"]
        elif method == "button":
            if command == "next":
                os.system("xdotool key XF86AudioNext")
            elif "prev" in command:
                os.system("xdotool key XF86AudioPrev")

    def run(self):
        # getting local ip
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        IP = s.getsockname()[0]
        s.close()

        print(colored("Web API: active", "OKGREEN", frame=False))

        app.run(IP)


if __name__ == "__main__":
    service = WebAPI(None)
    service.run()
