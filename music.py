"""
Plays one looping track at a time, fading between them. Files live in sounds/music/ under the track's
name, so a real piece of music can replace a placeholder just by taking its name.
"""
import os

import pygame

from resources import resource_path

FADE_MS = 700
FALLBACK = resource_path('sounds', 'shark.wav')
AREA_TRACKS = {"The Reef": 'reef', "The Ship Graveyard": 'graveyard', "The Volcanic Rift": 'rift',
               "Atlantis": 'atlantis', "The Sunken Lab": 'lab', "The Lab Core": 'core'}


def _path_for(track):
    for extension in ('ogg', 'mp3', 'wav'):
        path = resource_path('sounds', 'music', f'{track}.{extension}')
        if os.path.exists(path):
            return path
    return FALLBACK


class MusicDirector:
    def __init__(self, available, enabled, volume):
        self.available = available
        self.enabled = enabled
        self.volume = volume
        self.current = None  # The track playing, or on its way in
        self.waiting = None  # The track to start once the fade out ends
        self.fade = 1.0
        self.fading_out = False

    def set_preferences(self, enabled, volume):
        self.enabled = enabled
        self.volume = volume
        if self.available:
            self._apply_volume()
            if enabled:
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.pause()

    def _apply_volume(self):
        pygame.mixer.music.set_volume(self.volume * self.fade)

    def _start(self, track):
        self.current = track
        self.waiting = None
        self.fading_out = False
        self.fade = 0.0
        try:
            pygame.mixer.music.load(_path_for(track))
            self._apply_volume()
            pygame.mixer.music.play(-1)
            if not self.enabled:
                pygame.mixer.music.pause()
        except pygame.error as e:
            print(f"Warning: could not play music '{track}': {e}")

    def play(self, track):
        """Move to this track. Nothing happens if it's already playing or on its way."""
        if track == (self.waiting or self.current):
            return
        if not self.available:
            self.current = track
            return
        if self.current is None:
            self._start(track)
        else:
            self.waiting = track
            self.fading_out = True

    def update(self, dt):
        if not self.available:
            return
        step = dt / FADE_MS
        if self.fading_out:
            self.fade = max(0.0, self.fade - step)
            if self.fade <= 0:
                self._start(self.waiting)
        elif self.fade < 1:
            self.fade = min(1.0, self.fade + step)
        self._apply_volume()
