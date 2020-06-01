"""Host MySpotify class with KISS style methods for your spotify control."""

import os
import time
import random
import threading

import spotipy.util as util
import tekore as tk

scope = (
    "ugc-image-upload "
    "user-read-playback-state "
    "user-modify-playback-state "
    "user-read-currently-playing "
    "streaming "
    "app-remote-control "
    "user-read-email "
    "user-read-private "
    "playlist-read-collaborative "
    "playlist-modify-public "
    "playlist-read-private "
    "playlist-modify-private "
    "user-library-modify "
    "user-library-read "
    "user-top-read "
    "user-read-playback-position "
    "user-read-recently-played "
    "user-follow-read "
    "user-follow-modify"
)

REQUIRED_ENV_VAR = (
    "SPOTIPY_CLIENT_ID",
    "SPOTIPY_CLIENT_SECRET",
    "SPOTIPY_REDIRECT_URI",
    "SPOTIFY_USERNAME",
)


def pick_device(func):
    """Pick device wrapper"""
    def wrapper(self, *args, **kwargs):
        try:
            # this will work if there's an active device
            # or device_id is passed into func
            func(self, *args, **kwargs)
        except tk.NotFound:
            kwargs["device_id"] = self.default_device_id
            return func(self, *args, **kwargs)

    return wrapper


def play_returned_tracks(func):
    """Play returned track wrapper"""
    #ToDo
    def wrapper(self, *args, **kwargs):
        tracks = func(self, *args, **kwargs)
        print(tracks)
        if tracks:
            self.playback_start_tracks(
                track_ids=tracks, device_id=kwargs["device_id"]
            )

    return wrapper


class MySpotify(tk.Spotify):
    """Store simple spotipy methods."""

    def __init__(self, username=None, default_device_id=None):
        self.username = username if username else os.environ["SPOTIFY_USERNAME"]
        self.default_device_id = (
            default_device_id if default_device_id
            else os.environ["SPOTIFY_DEFAULT_DEVICE_ID"]
        )
        # start token refresh daemon
        threading.Thread(target=self._refresh_token_loop).start()

    def _refresh_token_loop(self):
        while True:
            self._token = util.prompt_for_user_token(self.username, scope)
            super().__init__(self._token)
            time.sleep(3500)

    def _get_device_id(self, device_name):
        devices = self.playback_devices()
        return [d.id for d in devices if d.name==device_name][0]


    @pick_device
    def play(self, device_id=None):
        """"""
        if self.playback_currently_playing():
            self.playback_resume(device_id=device_id)
        else:
            self.play_recent_tracks()

    @pick_device
    def pause(self, device_id=None):
        """"""
        self.playback_pause(device_id=device_id)

    def play_pause(self):
        """"""
        playback = self.playback()
        if playback and playback.is_playing:
            self.pause()
        else:
            self.play()

    @pick_device
    def next(self, device_id=None):
        """"""
        self.playback_next(device_id=device_id)

    @pick_device
    def previous(self, device_id=None):
        """"""
        self.playback_previous(device_id=device_id)

    @pick_device
    def play_recent_tracks(self, limit=20, device_id=None):
        """"""
        recent_tracks = self.playback_recently_played(limit=limit).items
        recent_tracks_ids = [ph.track.id for ph in recent_tracks]
        self.playback_start_tracks(
            track_ids=recent_tracks_ids, device_id=device_id
        )

    @pick_device
    def play_favourite_tracks(self, limit=20, device_id=None):
        """"""
        top_tracks = self.current_user_top_tracks(limit=limit).items
        top_tracks_ids = [t.id for t in top_tracks]
        random.shuffle(top_tracks_ids)
        self.playback_start_tracks(
            track_ids=top_tracks_ids, device_id=device_id
        )

    @pick_device
    def play_saved_tracks(self, limit=30, device_id=None):
        """"""
        saved_tracks = self.saved_tracks(limit=limit).items
        saved_tracks_ids = [saved.track.id for saved in saved_tracks]
        random.shuffle(saved_tracks_ids)
        self.playback_start_tracks(
            track_ids=saved_tracks_ids, device_id=device_id
        )

    @pick_device
    def play_recommended_tracks(self, limit=30, device_id=None):
        """"""
        saved_tracks = self.saved_tracks(limit=20).items
        top_tracks = self.current_user_top_tracks(limit=10).items
        mixed_tracks_ids = [t.id for t in top_tracks + saved_tracks]

        recommended_tracks = self.recommendations(
            track_ids=random.sample(mixed_tracks_ids, 5), limit=limit
        ).tracks
        recommended_tracks_ids = [t.id for t in recommended_tracks]

        self.playback_start_tracks(
            track_ids=recommended_tracks_ids, device_id=device_id
        )

    @pick_device
    def play_tracks_similar_to_current(self, limit=30, device_id=None):
        """"""
        current = self.playback_currently_playing()
        if current:
            similar_tracks = self.recommendations(
                track_ids=[current.item.id], limit=limit
            ).tracks

            similar_tracks_ids = [track.id for track in similar_tracks]
            self.playback_start_tracks(
                track_ids=similar_tracks_ids, device_id=device_id
            )

    def play_current_track_artist(self, limit=30, device_id=None):
        """"""
        current = self.playback_currently_playing()
        if current:
            artist_uri = current.item.artists[0].uri
            self.playback_start_context(
                context_uri=artist_uri, device_id=device_id
            )

    def play_made_for_me(self):
        """"""
        # ToDo
        pass

    def add_current_track(self):
        """"""
        current = self.playback_currently_playing()
        if current:
            self.saved_tracks_add([current.item.id])

    def add_current_track_album(self):
        """"""
        current = self.playback_currently_playing()
        if current:
            self.saved_albums_add([current.item.album.id])

    @pick_device
    def play_tracks_in_genre(self, genre, limit=30, device_id=None):
        """"""
        genre_tracks = self.recommendations(genres=[genre], limit=limit).tracks
        genre_tracks_ids = [track.id for track in genre_tracks]
        self.playback_start_tracks(
            track_ids=genre_tracks_ids, device_id=device_id
        )

    def get_genres(self):
        """"""
        return self.recommendation_genre_seeds()

    @pick_device
    def set_volume(self, volume_percent, device_id=None):
        """"""
        self.playback_volume(
            volume_percent=volume_percent, device_id=device_id
        )

    @pick_device
    def search_and_play_track(self, query, device_id=None):
        """"""
        track_id = (
            self.search(query=query, types=("track",), limit=1)[0].items[0].id
        )
        self.playback_start_tracks(track_ids=[track_id], device_id=device_id)
        # TODO: add similar tracks to the queue

    @pick_device
    def search_and_play_album(self, query, device_id=None):
        """"""
        uri = (
            self.search(query=query, types=("album",), limit=1)[0].items[0].uri
        )
        self.playback_start_context(context_uri=uri, device_id=device_id)

    @pick_device
    def search_and_play_playlist(self, query, device_id=None):
        """"""
        playlists = self.search(
            query=query, types=("playlist",), limit=5)[0].items
        uri = random.choice(playlists).uri
        self.playback_start_context(context_uri=uri, device_id=device_id)

    @pick_device
    def search_and_play_artist(self, query, device_id=None):
        uri = self.search(
            query=query, types=("artist",), limit=1)[0].items[0].uri
        self.playback_start_context(context_uri=uri, device_id=device_id)

    def get_current_track_description(self):
        current = self.playback_currently_playing()
        if current:
            track = current.item
            return (
                track.name + " by " + ", ".join(a.name for a in track.artists)
            )
