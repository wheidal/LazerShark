import random

import pygame
import pytest

import channel as ch
from enemies import Enemy
from obstacle import CoralReef, Jellyfish, OBSTACLE_TYPES, SeaMine, Shipwreck
from projectile import Laser


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


def test_mine_blast_chains_and_spares_distant_obstacles(play):
    def build():
        return [SeaMine(300, 200), SeaMine(400, 200), CoralReef(490, 200), CoralReef(760, 200)]

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
            if isinstance(sprite, Enemy):
                continue
            seen['kinds'].add(sprite.kind)
            if pygame.sprite.spritecollideany(sprite, state['banks'], pygame.sprite.collide_mask):
                seen['touches'] += 1
        state['energy'] = 100
        return frame >= 3000 and seen['kinds'] == set(OBSTACLE_TYPES)  # Which kinds appear is random

    play(script, quiet=False, max_frames=40000)
    assert seen['kinds'] == set(OBSTACLE_TYPES)
    assert seen['touches'] == 0


def far_shark():
    rect = pygame.Rect(0, 0, 45, 104)
    rect.center = (700, 500)
    return rect


def test_mine_ignores_a_distant_shark_and_arms_for_a_close_one(display):
    mine = SeaMine(400, 200)
    mine.sense(far_shark())
    assert mine.fuse is None
    near = pygame.Rect(0, 0, 45, 104)
    near.midtop = (mine.rect.centerx, mine.rect.centery + SeaMine.SENSE_RADIUS - 5)
    mine.sense(near)
    assert mine.fuse == SeaMine.FUSE_STEPS


def test_armed_mine_counts_down_and_stays_armed(display):
    mine = SeaMine(400, 200)
    mine.fuse = 3
    for _ in range(2):
        mine.update()
        assert not mine.fuse_done
    mine.sense(far_shark())  # Swimming away doesn't defuse it
    mine.update()
    assert mine.fuse_done


def test_there_is_time_to_get_clear_of_a_fuse(display):
    margin = SeaMine.blast_radius - SeaMine.SENSE_RADIUS
    assert SeaMine.FUSE_STEPS * 5 > margin * 2  # Even when scrolling closes part of the gap
    assert SeaMine.blast_radius > SeaMine.SENSE_RADIUS


def mine_scene(play, offset, shot=False, shield=False, beside=0):
    seen = {}

    def script(state, frame):
        shark = state['shark'].rect
        if frame == 1:
            state['energy'] = 100
            if shield:
                state['shield_active'], state['shield_strength'] = True, 100
            seen['mine'] = SeaMine(shark.centerx + beside, shark.top - offset)
            state['obstacles'].add(seen['mine'])
            seen['score'] = state['score']
            if shot:
                state['projectiles'].add(Laser(seen['mine'].rect.centerx, seen['mine'].rect.bottom + 8))
        seen['energy'] = state['energy']
        seen['gained'] = state['score'] - seen['score']
        seen['shield'] = state['shield_strength']
        return frame >= SeaMine.FUSE_STEPS + 12

    play(script)
    return seen


def test_lingering_near_a_mine_costs_the_blast_and_scores_nothing(play):
    seen = mine_scene(play, 60, beside=85)
    assert not seen['mine'].alive()
    assert seen['energy'] == pytest.approx(100 - SeaMine.blast_damage, abs=4)
    assert seen['gained'] == 0


def test_shooting_a_mine_up_close_hurts_just_as_much(play):
    seen = mine_scene(play, 80, shot=True)
    assert not seen['mine'].alive()
    assert seen['energy'] == pytest.approx(100 - SeaMine.blast_damage, abs=4)
    assert seen['gained'] == SeaMine.reward


def test_shooting_a_mine_from_afar_is_safe_and_scores(play):
    seen = mine_scene(play, SeaMine.blast_radius + 90, shot=True)
    assert not seen['mine'].alive()
    assert seen['energy'] > 95
    assert seen['gained'] == SeaMine.reward


def test_shield_absorbs_a_mine_blast(play):
    seen = mine_scene(play, 60, shield=True, beside=85)
    assert seen['energy'] > 95
    assert seen['shield'] == pytest.approx(100 - SeaMine.blast_damage, abs=1)


def test_sitting_still_in_a_mines_path_is_worse_than_its_blast(play):
    seen = mine_scene(play, 90)
    assert not seen['mine'].alive()
    assert seen['energy'] == pytest.approx(100 - SeaMine.damage, abs=4)
    assert SeaMine.damage > SeaMine.blast_damage
