import os
import requests
import random
import time
import spotipy.util as util
from ..utils import is_running

API_LINKS = {"search": "https://api.spotify.com/v1/search?"}

DBUS = "qdbus org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2 "
DBUS_METHODS = {
    "device": "org.freedesktop.DBus.Peer.GetMachineId",
    "metadata": "org.mpris.MediaPlayer2.Player.Metadata",
    "can_play": "org.mpris.MediaPlayer2.Player.CanPlay",
    "play_status": "org.mpris.MediaPlayer2.Player.PlaybackStatus",
    "next": "org.mpris.MediaPlayer2.Player.Next",
    "open_uri": "org.mpris.MediaPlayer2.Player.OpenUri",
    "pause": "org.mpris.MediaPlayer2.Player.Pause",
    "play": "org.mpris.MediaPlayer2.Player.Play",
    "play_pause": "org.mpris.MediaPlayer2.Player.PlayPause",
    "previous": "org.mpris.MediaPlayer2.Player.Previous",
    "shuffle": "org.mpris.MediaPlayer2.Player.Shuffle",
    "stop": "org.mpris.MediaPlayer2.Player.Stop",
    "volume": "org.mpris.MediaPlayer2.Player.Volume",
}


class Spotify:
    token = util.oauth2.SpotifyClientCredentials(
        client_id=os.environ["SPOTIPY_CLIENT_ID"],
        client_secret=os.environ["SPOTIPY_CLIENT_SECRET"],
    )

    def get_token(self):
        return self.token.get_access_token()

    def get_headers(self):
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.get_token(),
        }

    def get(self, url):
        return requests.get(url, headers=self.get_headers()).json()

    def search(self, q, type, limit=5, offset=5):
        q = q.replace(" ", "+")
        return self.get(
            API_LINKS["search"]
            + f"q={q}&type={type}&market=US&limit={limit}&offset={offset}"
        )

    def call_method(self, method, param=""):
        return os.popen(DBUS + DBUS_METHODS[method] + " " + param).read()

    def play(self):
        if not self.is_running():
            self.run_app()
        self.call_method("play")

    def pause(self):
        self.call_method("pause")

    def play_pause(self):
        if not self.is_running():
            self.run_app()
        self.call_method("play_pause")

    def next(self):
        self.call_method("next")

    def prev(self):
        self.call_method("previous")
        self.call_method("previous")

    def shuffle(self):
        self.call_method("shuffle")

    def get_track_data(self):
        return self.call_method("metadata")

    def find_and_play(self, query, type="track"):
        if type == "album":
            r = self.search(q=query, type=type, limit=5, offset=5)
            uri = random.choice(r[type + "s"]["items"])["uri"]
        else:
            r = self.search(q=query, type=type, limit=1, offset=1)
            uri = r[type + "s"]["items"][0]["uri"]

        if not self.is_running():
            self.run_app()

        self.call_method("open_uri", param=uri)

    def get_metadata(self):
        self.call_method("metadata")

    def is_playing(self):
        if self.call_method("play_status") == "Playing\n":
            return True
        else:
            return False

    def can_play(self):
        return self.call_method("can_play")

    def is_running(self):
        return is_running("spotify")

    def run_app(self):
        os.system("spotify &")
        time.sleep(2)
