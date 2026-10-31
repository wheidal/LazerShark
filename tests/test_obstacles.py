import random

import pygame
import pytest

import channel as ch
from obstacle import CoralReef, Jellyfish, OBSTACLE_TYPES, SeaMine, Shipwreck
from projectile import Laser, Missile


def test_every_zone_only_uses_real_obstacles():
    for zone in ch.ZONES.values():
        assert set(zone['obstacles']) <= set(OBSTACLE_TYPES)


@pytest.mark.parametrize('kind', OBSTACLE_TYPES.values())
def test_sprites_fit_their_declared_size_and_start_off_screen(display, kind):
    for _ in range(30):
        for sprite in kind.create(400):
            assert sprite.rect.bottom <= 0
            assert sprite.rect.top >= -kind.HEIGHT
            assert sprite.rect.height <= kind.HEIGHT
            reach = sprite.rect.width // 2 + getattr(kind, 'SWAY', 0) + abs(sprite.rect.centerx - 400)
            assert reach <= kind.WIDTH // 2 + 2


def test_shadow_does_not_count_as_a_hit(display):
    coral = CoralReef(0, 0)
    w, h = coral.image.get_size()
    solid = coral.mask.count()
    assert 0 < solid < w * h
    corner_pixels = [coral.mask.get_at((x, h - 1)) for x in range(w)]
    assert not all(corner_pixels)


def run_shot(play, build, shot):
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['energy'] = 100
            seen['obstacles'] = build()
            state['obstacles'].add(seen['obstacles'])
            state['projectiles'].add(shot(seen['obstacles'][0]))
        seen['alive'] = [o for o in seen['obstacles'] if o.alive()]
        seen['energy'] = state['energy']
        return frame >= 4

    play(script)
    return seen


def test_laser_needs_many_hits_on_a_wreck(play):
    seen = run_shot(play, lambda: [Shipwreck(400, 200)], lambda o: Laser(o.rect.centerx, o.rect.centery))
    assert seen['obstacles'][0].hits == 1 and seen['alive']


def test_missile_destroys_a_wreck_outright(play):
    seen = run_shot(play, lambda: [Shipwreck(400, 200)], lambda o: Missile(o.rect.centerx, o.rect.centery))
    assert not seen['alive']


def test_mine_blast_chains_and_spares_distant_obstacles(play):
    def build():
        return [SeaMine(150, 200), SeaMine(250, 200), CoralReef(340, 200), CoralReef(700, 200)]

    seen = run_shot(play, build, lambda o: Laser(o.rect.centerx, o.rect.centery))
    assert seen['alive'] == [seen['obstacles'][3]]


def test_shot_mine_hurts_a_shark_in_range_but_not_one_far_away(play):
    near = run_shot(play, lambda: [SeaMine(400, 430)], lambda o: Laser(o.rect.centerx, o.rect.centery))
    far = run_shot(play, lambda: [SeaMine(400, 40)], lambda o: Laser(o.rect.centerx, o.rect.centery))
    assert far['energy'] > 95
    assert near['energy'] < far['energy'] - 15


def test_jellyfish_stay_within_their_sway(display):
    jelly = Jellyfish(400, 100)
    xs = set()
    for _ in range(600):
        jelly.update()
        xs.add(jelly.rect.centerx)
    assert max(xs) <= 400 + Jellyfish.SWAY and min(xs) >= 400 - Jellyfish.SWAY
    assert len(xs) > 10


def test_large_spawns_clear_the_coast_ahead_of_them(display):
    rng = random.Random(4)
    director = ch.ChannelDirector(rng)
    director.prefill()
    placed = 0
    for _ in range(6000):
        director.update(100)
        x = director.spawn_x(Shipwreck.WIDTH, blocking=True, height=Shipwreck.HEIGHT)
        if x is None:
            continue
        placed += 1
        rows = Shipwreck.HEIGHT // ch.SAMPLE_SPACING
        for left, right, _ in director.generator.peek(rows, 100):
            assert left < x - Shipwreck.WIDTH // 2 and right > x + Shipwreck.WIDTH // 2
    assert placed > 500


def test_every_kind_keeps_clear_of_the_coast_in_play(play, monkeypatch):
    for zone in ch.ZONES.values():
        monkeypatch.setitem(zone, 'obstacles', list(OBSTACLE_TYPES))
    seen = {'touches': 0, 'kinds': set()}

    def script(state, frame):
        for sprite in state['obstacles']:
            seen['kinds'].add(sprite.kind)
            if pygame.sprite.spritecollideany(sprite, state['banks'], pygame.sprite.collide_mask):
                seen['touches'] += 1
        state['energy'] = 100
        return frame >= 3000

    play(script, quiet=False, max_frames=3000)
    assert seen['kinds'] == set(OBSTACLE_TYPES)
    assert seen['touches'] == 0
