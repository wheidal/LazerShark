"""Runs the real game headlessly so tests can script it."""
import json
import os
import sys

import pytest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

import main as game
import settings_manager


class Finished(Exception):
    """Raised by the harness to leave the game loop."""


@pytest.fixture
def display():
    pygame.quit()
    pygame.init()
    yield pygame.display.set_mode((800, 600))
    pygame.quit()


@pytest.fixture
def play(monkeypatch, tmp_path):
    """Run main() through the menus, calling script(state, frame) each gameplay frame.

    state is main()'s live local variables; writing to them needs Python 3.13.
    The script returns True to stop. Returns 'stopped', or 'exited' if the game quit itself.
    """
    def run(script, clock_ms=16, keymap=None, menu_keys=None, quiet=True, max_frames=2000):
        settings = tmp_path / 'game_settings.json'
        if keymap:
            settings.write_text(json.dumps({'keymap': keymap}))
        monkeypatch.setattr(settings_manager, 'settings_path', lambda name: str(settings))

        class FakeClock:
            def tick(self, fps=0):
                return clock_ms

        monkeypatch.setattr(pygame.time, 'Clock', FakeClock)
        real_flip = pygame.display.flip
        pending = list(menu_keys if menu_keys is not None else [pygame.K_DOWN] * 6 + [pygame.K_RETURN])
        frame = [0]

        def flip():
            real_flip()
            state = sys._getframe(1).f_locals
            if state.get('in_settings'):
                for key in pending:
                    press(key)
                pending.clear()
            elif state.get('splash'):
                press(pygame.K_s if pending else pygame.K_a)
            elif 'briefing' in state and 'running' not in state:
                press(pygame.K_a)
            elif 'running' in state:
                if quiet:
                    for timer in ('spawn_timer', 'powerup_timer', 'enemy_timer'):
                        state[timer] = 0
                frame[0] += 1
                if script(state, frame[0]) or frame[0] >= max_frames:
                    raise Finished

        monkeypatch.setattr(pygame.display, 'flip', flip)
        pygame.quit()
        try:
            game.main()
        except Finished:
            return 'stopped'
        except SystemExit:
            return 'exited'
        finally:
            pygame.quit()

    return run


def press(key):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode='', scancode=0))
