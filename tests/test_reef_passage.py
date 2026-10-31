import random
import sys

import pygame
import pytest

from obstacle import ReefSegment
from projectile import Laser, Missile, Torpedo
import reef_passage as rp

needs_live_locals = pytest.mark.skipif(sys.version_info < (3, 13), reason='writes to frame locals')
SHARK_NOSE_Y = 493  # Lowest (hardest) position: the shark stays at the bottom of its range


def generate_rows(seed, score):
    director = rp.ReefPassageDirector(random.Random(seed))
    director.start(score)
    rows = []
    for _ in range(rp.ROWS_PER_PASSAGE * rp.ROW_SPACING):
        row = director.update(0, score)
        if row:
            rows.append(row)
    return rows


def route_exists(rows, start_x):
    """Search every position the shark's body could reach, treating plugs as solid."""
    reachable = {start_x}
    half = rp.SHARK_BODY_W / 2
    top = SHARK_NOSE_Y
    bottom = top + rp.SHARK_BODY_H
    # Row i appears at the top of the screen after (i + 1) spacings of scrolling
    scroll = -rp.ROCK_H
    last = (len(rows) - 1) * rp.ROW_SPACING + 600 + rp.ROCK_H
    while scroll < last:
        scroll += rp.SCROLL_PER_STEP
        solid = []
        for i, row in enumerate(rows):
            y = scroll - i * rp.ROW_SPACING
            if y < bottom and y + rp.ROCK_H > top:
                solid.extend(row.rock_spans())
                if row.plug_x is not None:
                    solid.append((row.plug_x, rp.PLUG_WIDTH))
        widened = {max(0, min(800, x + dx)) for x in reachable for dx in range(-rp.SHARK_SPEED, rp.SHARK_SPEED + 1, rp.SHARK_SPEED)}
        reachable = {x for x in widened
                     if not any(x + half > sx and x - half < sx + sw for sx, sw in solid)}
        if not reachable:
            return False
    return True


@pytest.mark.parametrize('score', [0, 60, 200])
@pytest.mark.parametrize('start_x', [25, 400, 775])
def test_every_generated_passage_has_a_route(score, start_x):
    for seed in range(60):
        assert route_exists(generate_rows(seed, score), start_x), seed


def test_gaps_stay_fair_and_narrow_with_score():
    for score, width in [(0, rp.WIDEST_GAP), (500, rp.NARROWEST_GAP)]:
        for row in generate_rows(1, score):
            assert row.gap_w == width
            assert 0 <= row.gap_x and row.gap_x + row.gap_w <= 800


def test_plug_never_overlaps_gap():
    for seed in range(200):
        for row in generate_rows(seed, 0):
            if row.plug_x is not None:
                assert row.plug_x + rp.PLUG_WIDTH < row.gap_x or row.plug_x > row.gap_x + row.gap_w


def test_normal_spawning_waits_for_passage():
    director = rp.ReefPassageDirector(random.Random(1))
    assert director.subs_allowed
    director.wait_ms = rp.SUB_CLEAR_MS - 1
    assert not director.subs_allowed and not director.active
    director.start()
    assert director.active
    for _ in range(rp.ROWS_PER_PASSAGE * rp.ROW_SPACING):
        director.update(0, 0)
    assert not director.active
    assert director.wait_ms == rp.PASSAGE_INTERVAL_MS


def rock_row(state, gap_x=350):
    row = rp.ReefRow(gap_x, 160)
    rocks, plugs, foods, rewards = row.build()
    state['rocks'].add(rocks)
    state['all_sprites'].add(rocks)
    return rocks


@needs_live_locals
def test_hitting_rock_costs_energy_once_and_never_traps_shark(play):
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['shark'].rect.centerx = 60
            state['passage'].wait_ms = 10 ** 9
            seen['rocks'] = rock_row(state)
            for rock in seen['rocks']:
                rock.rect.y = state['shark'].rect.top - rp.ROCK_H - 3
        if frame == 200:
            seen['energy'] = state['energy']
            seen['clear'] = not pygame.sprite.spritecollideany(state['shark'], state['rocks'], pygame.sprite.collide_mask)
            seen['over'] = state['game_over']
            return True

    play(script)
    assert not seen['over']
    assert seen['clear']
    assert 100 - rp.ROCK_DAMAGE - 5 < seen['energy'] < 100 - rp.ROCK_DAMAGE + 1


@needs_live_locals
@pytest.mark.parametrize('weapon', [Laser, Missile, Torpedo])
def test_rock_survives_and_stops_every_weapon(play, weapon):
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['passage'].wait_ms = 10 ** 9
            seen['rocks'] = rock_row(state)
            for rock in seen['rocks']:
                rock.rect.y = 200
            seen['shot'] = weapon(100, 270)
            state['projectiles'].add(seen['shot'])
            state['all_sprites'].add(seen['shot'])
        return frame >= 15

    play(script)
    assert all(rock.alive() for rock in seen['rocks'])
    assert not seen['shot'].alive()


@needs_live_locals
def test_torpedoes_do_not_lock_onto_rock(play):
    seen = {}

    def script(state, frame):
        if frame == 1:
            rock_row(state)
            seen['targets'] = len(state['obstacles'])
        return frame >= 2

    play(script)
    assert seen['targets'] == 0


@needs_live_locals
def test_coral_plug_can_be_shot_out(play):
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['passage'].wait_ms = 10 ** 9
            seen['plug'] = ReefSegment(100, rp.PLUG_WIDTH)
            seen['plug'].rect.y = 200
            state['obstacles'].add(seen['plug'])
            state['projectiles'].add(Missile(150, 270))
        return frame >= 15

    play(script)
    assert not seen['plug'].alive()


@needs_live_locals
@pytest.mark.parametrize('seed', range(5))
def test_steering_bot_clears_a_real_passage_unharmed(play, monkeypatch, seed):
    held = {}

    class Keys:
        def __getitem__(self, key):
            return held.get(key, False)

    monkeypatch.setattr(pygame.key, 'get_pressed', lambda: Keys())
    seen = {'bonus': False, 'worst': 100}

    def script(state, frame):
        if frame == 1:
            state['passage'] = rp.ReefPassageDirector(random.Random(seed))
            state['passage'].start()
        shark = state['shark']
        ahead = sorted((r for r in state['rocks'] if r.rect.top < shark.rect.bottom), key=lambda r: -r.rect.top)
        target = ahead[0].gap_center if ahead else shark.rect.centerx
        held[pygame.K_LEFT] = target < shark.rect.centerx - 5
        held[pygame.K_RIGHT] = target > shark.rect.centerx + 5
        seen['hit'] = seen.get('hit', False) or state['rock_invuln'] > 0
        seen['bonus'] = seen['bonus'] or state['score'] >= rp.CLEAR_BONUS
        seen['over'] = state['game_over']
        seen['passes'] = not state['passage'].active and not state['rocks']
        return frame > 5 and seen['passes']

    play(script, max_frames=1500)
    assert seen['passes'] and seen['bonus'] and not seen['over']
    assert not seen['hit']
