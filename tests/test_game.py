import json
import os
import sys

import pygame
import pytest

from conftest import press
from graphics_enhancements import GraphicsEnhancer, ScreenEffects
import main as game
from obstacle import CoralReef
from player import Shark
from player_enhanced import SharkWithSprites
from powerup import ShieldPowerup
from projectile import Missile
from resources import resource_path
import settings_manager

needs_live_locals = pytest.mark.skipif(sys.version_info < (3, 13), reason='writes to frame locals')
HOLD_DOWN = {'left': False, 'right': False, 'up': False, 'down': True}


@pytest.mark.parametrize('make_shark', [SharkWithSprites, Shark])
def test_shark_stays_on_screen(display, make_shark):
    shark = make_shark(400, 580)
    for _ in range(100):
        if hasattr(shark, 'update_with_input'):
            shark.update_with_input(HOLD_DOWN, 16)
        else:
            shark.update(16, HOLD_DOWN)
    assert shark.rect.bottom <= 600


def test_hazard_needs_to_touch_shark_body(display):
    shark = SharkWithSprites(400, 450)
    coral = CoralReef(0, 0)
    coral.rect.midright = (shark.rect.left + 15, shark.rect.centery)
    assert shark.rect.colliderect(coral.rect)
    assert not game.pixels_touch(shark, coral)
    coral.rect.center = shark.rect.center
    assert game.pixels_touch(shark, coral)


def test_default_keys_use_pygame_2_codes(monkeypatch, tmp_path):
    monkeypatch.setattr(settings_manager, 'settings_path', lambda name: str(tmp_path / name))
    keymap = settings_manager.SettingsManager().get('keymap')
    assert keymap['left'] == pygame.K_LEFT
    assert keymap['missile'] == pygame.K_LALT


def test_old_saved_keys_are_converted(monkeypatch, tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({'keymap': {'left': 276, 'fire': pygame.K_w}}))
    monkeypatch.setattr(settings_manager, 'settings_path', lambda name: str(path))
    keymap = settings_manager.SettingsManager().get('keymap')
    assert keymap['left'] == pygame.K_LEFT
    assert keymap['fire'] == pygame.K_w


def test_assets_found_from_any_folder(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert os.path.exists(resource_path('sounds', 'laser.wav'))


def test_overlays_are_not_rebuilt_each_frame(display, monkeypatch):
    enhancer = GraphicsEnhancer(display)

    def rebuilt(*args, **kwargs):
        raise AssertionError('overlay rebuilt during a frame')

    monkeypatch.setattr(ScreenEffects, 'build_vignette', rebuilt)
    monkeypatch.setattr(enhancer.lighting, 'create_depth_fog', rebuilt)
    enhancer.render_background()
    enhancer.render_effects()


@needs_live_locals
def test_running_out_of_energy_ends_game(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 0
        seen['over'] = state['game_over']
        return frame >= 3

    play(script)
    assert seen['over']


@needs_live_locals
def test_shield_drop_survives_kills_while_shield_is_active(play):
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['destroyed_counts'] = {'Coral Reef': 5}
            coral = CoralReef(400, 200)
            state['obstacles'].add(coral)
            state['projectiles'].add(Missile(coral.rect.centerx, coral.rect.bottom))
        seen['drops'] = sum(isinstance(p, ShieldPowerup) for p in state['powerups'])
        return frame >= 4

    play(script)
    assert seen['drops'] == 1


@needs_live_locals
def test_pause_freezes_timers(play):
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['banner_timer'] = 5000
            press(pygame.K_p)
        if frame == 3:
            seen['paused'] = state['paused']
            seen['start'] = state['banner_timer']
        if frame == 40:
            seen['end'] = state['banner_timer']
            return True

    play(script)
    assert seen['paused']
    assert seen['start'] == seen['end']


@needs_live_locals
def test_game_over_ignores_keys_briefly_then_restarts_unpaused(play):
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['energy'] = 0
        if frame == 5:
            seen['over'] = state['game_over']
            press(pygame.K_SPACE)
        if frame == 8:
            seen['still_over'] = state['game_over']
        if frame == 100:
            press(pygame.K_p)
        if frame == 103:
            seen['restarted'] = not state['game_over']
            seen['paused'] = state['paused']
            return True

    play(script)
    assert seen['over'] and seen['still_over']
    assert seen['restarted'] and not seen['paused']


@needs_live_locals
@pytest.mark.parametrize('key', [pygame.K_q, pygame.K_ESCAPE])
def test_remapped_quit_and_esc_both_exit(play, key):
    def script(state, frame):
        if frame == 2:
            press(key)
        assert frame < 10

    assert play(script, keymap={'quit': pygame.K_q}) == 'exited'


@needs_live_locals
def test_remapped_pause_replaces_p(play):
    seen = {}

    def script(state, frame):
        if frame == 2:
            press(pygame.K_p)
        if frame == 4:
            seen['p'] = state['paused']
            press(pygame.K_o)
        if frame == 6:
            seen['o'] = state['paused']
            return True

    play(script, keymap={'pause': pygame.K_o})
    assert not seen['p'] and seen['o']


@needs_live_locals
def test_game_speed_does_not_depend_on_frame_rate(play):
    def distance(clock_ms):
        seen = {}

        def script(state, frame):
            if frame == 1:
                seen['coral'] = CoralReef(400, 0)
                state['obstacles'].add(seen['coral'])
                seen['start'] = seen['coral'].rect.y
            seen['moved'] = seen['coral'].rect.y - seen['start']
            return frame * clock_ms >= 1000

        play(script, clock_ms=clock_ms)
        return seen['moved']

    assert abs(distance(16) - distance(33)) <= 6


@needs_live_locals
def test_runs_without_audio_device(play, monkeypatch):
    monkeypatch.setenv('SDL_AUDIODRIVER', 'nonexistent')
    # Toggle music and open volume in the menu, then continue
    keys = [pygame.K_DOWN] * 3 + [pygame.K_RETURN, pygame.K_DOWN, pygame.K_RETURN, pygame.K_RIGHT,
                                  pygame.K_RETURN, pygame.K_DOWN, pygame.K_DOWN, pygame.K_RETURN]
    assert play(lambda state, frame: frame >= 5, menu_keys=keys) == 'stopped'


def test_laser_recharges_at_the_rate_for_the_difficulty(play):
    from boss import LASER_RECHARGE
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['shark'].laser_energy = 0
        if frame == 61:
            seen['energy'] = state['shark'].laser_energy
            return True

    play(script)
    assert abs(seen['energy'] - LASER_RECHARGE['normal']) <= 1


def test_full_laser_lasts_several_seconds_of_steady_fire(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        pygame.event.pump()
        if state['shark'].fire_laser():
            seen['shots'] = seen.get('shots', 0) + 1
        if state['shark'].laser_energy < 3:
            seen['frames'] = frame
            return True

    play(script, max_frames=2000)
    assert seen['shots'] >= 30
