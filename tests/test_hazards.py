import pygame
import pytest

import channel as ch
from enemies import RadioactivePiranha
from food import SmallFish, ZombieFish
from hazards import (CLOUD_DRAIN, CLOUD_RADIUS, SMALL_CLOUD_STEPS, WHIRLPOOL_CORE, WHIRLPOOL_PULL, WHIRLPOOL_RADIUS,
                     RadiationCloud, Whirlpool)
from obstacle import EmpJellyfish, RadiationBarrel
from projectile import Laser

SHARK = pygame.Rect(0, 0, 45, 104)


def at(x, y):
    rect = SHARK.copy()
    rect.center = (x, y)
    return rect


def test_barrel_leaks_after_blinking(display):
    barrel = RadiationBarrel(400, 0)
    start = barrel.image
    for _ in range(RadiationBarrel.BLINK_FROM + 12):
        barrel.update()
    assert barrel.image is not start or barrel.frames[1] is not start
    for _ in range(RadiationBarrel.LEAK_STEPS):
        barrel.update()
    assert barrel.leaking


def test_cloud_grows_then_drains_only_inside_it(display):
    cloud = RadiationCloud((400, 300))
    small = cloud.radius
    for _ in range(80):
        cloud.update()
    assert cloud.radius == CLOUD_RADIUS > small
    assert cloud.rect.center == (400, 300)
    assert cloud.drain_on(at(400, 300)) == CLOUD_DRAIN
    assert cloud.drain_on(at(400, 300 + CLOUD_RADIUS + 60)) == 0


def test_small_cloud_fades_away(display):
    group = pygame.sprite.Group(RadiationCloud((1, 1), 44, SMALL_CLOUD_STEPS))
    for _ in range(SMALL_CLOUD_STEPS + 1):
        group.update()
    assert not group


def test_whirlpool_pull_can_always_be_beaten_and_core_drains(display):
    pool = Whirlpool(400, 100)
    center = pool.rect.center
    assert WHIRLPOOL_PULL < ch.SHARK_SPEED
    for distance in (WHIRLPOOL_RADIUS - 5, 60, WHIRLPOOL_CORE + 5, 5):
        pull = pygame.math.Vector2(pool.pull_on(at(center[0] + distance, center[1])))
        assert pull.length() <= WHIRLPOOL_PULL
        assert pull.x < 0  # Towards the middle
    assert pool.pull_on(at(center[0] + WHIRLPOOL_RADIUS + 5, center[1])) == (0, 0)
    assert pool.drain_on(at(*center)) > 0
    assert pool.drain_on(at(center[0] + 90, center[1])) == 0


def test_whirlpool_keeps_turning_without_drifting(display):
    pool = Whirlpool(400, 100)
    center = pool.rect.center
    images = set()
    for _ in range(40):
        pool.update()
        images.add(id(pool.image))
    assert len(images) > 3 and pool.rect.center == center


def test_piranhas_chase_then_give_up(display):
    fish = RadioactivePiranha(400, -40, at(100, 500))
    group = pygame.sprite.Group(fish)
    start = fish.pos.distance_to(at(100, 500).center)
    for _ in range(100):
        group.update()
    assert fish.pos.distance_to(at(100, 500).center) < start
    for _ in range(1200):
        group.update()
    assert not fish.alive()


def test_zombie_fish_look_different_and_bite(display):
    assert ZombieFish.bite > 0 and SmallFish.bite == 0
    assert ZombieFish(0, 0).image.get_size() == SmallFish(0, 0).image.get_size()


def scene(play, setup, each=None, frames=4):
    seen = {}

    def script(state, frame):
        if frame == 1:
            setup(state, seen)
            seen['start'] = state['energy']
        if each:
            each(state, frame, seen)
        seen['energy'] = state['energy']
        seen['shield'] = state['shield_strength']
        seen['label'] = state['weapon'].label
        seen['jam'] = state['laser_jam']
        seen['score'] = state['score']
        return frame >= frames

    play(script)
    return seen


def test_eating_a_zombie_fish_costs_energy_and_no_score(play):
    def setup(state, seen):
        state['energy'] = 80
        fish = ZombieFish(state['shark'].rect.centerx, state['shark'].rect.centery)
        state['foods'].add(fish)

    seen = scene(play, setup)
    assert seen['start'] - seen['energy'] == pytest.approx(ZombieFish.bite, abs=1)
    assert seen['score'] == 0


def test_radiation_goes_through_the_shield_and_keeps_weapon_level(play):
    def setup(state, seen):
        state['shield_active'], state['shield_strength'] = True, 100
        state['weapon'].collect('fan')
        cloud = RadiationCloud(state['shark'].rect.center)
        cloud.age = 100
        state['drains'].add(cloud)

    seen = scene(play, setup, frames=30)
    assert seen['energy'] < seen['start'] - 5
    assert seen['shield'] == 100
    assert seen['label'] == 'FAN 1'


def test_emp_sting_jams_the_laser_even_through_a_shield(play):
    def setup(state, seen):
        state['shield_active'], state['shield_strength'] = True, 100
        shark = state['shark'].rect
        jelly = EmpJellyfish(shark.centerx, shark.centery - 20)
        state['obstacles'].add(jelly)

    seen = scene(play, setup)
    assert seen['jam'] > 1000


def test_jammed_laser_cannot_fire(play, monkeypatch):
    seen = {}

    class Held:
        def __getitem__(self, key):
            return key == pygame.K_SPACE

    monkeypatch.setattr(pygame.key, 'get_pressed', lambda: Held())

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['laser_jam'] = 200
            state['projectiles'].empty()  # Fired before the jam began
        seen.setdefault('during', 0)
        if frame < 8:
            seen['during'] = max(seen['during'], len(state['projectiles']))
        seen['after'] = len(state['projectiles'])
        return frame >= 40

    play(script)
    assert seen['during'] == 0
    assert seen['after'] > 0


def test_shot_barrel_never_leaks_and_piranha_leaves_a_cloud(play):
    def setup(state, seen):
        barrel = RadiationBarrel(400, 200)
        fish = RadioactivePiranha(250, 200, state['shark'].rect)
        fish.update()
        state['obstacles'].add(barrel, fish)
        state['projectiles'].add(Laser(400, 250), Laser(250, 230))
        seen['barrel'], seen['fish'] = barrel, fish

    def each(state, frame, seen):
        seen['clouds'] = len(state['drains'])

    seen = scene(play, setup, each, frames=8)
    assert not seen['barrel'].alive() and not seen['fish'].alive()
    assert seen['clouds'] == 1


def test_ignored_barrel_leaks_in_the_game(play):
    def setup(state, seen):
        barrel = RadiationBarrel(120, -300)
        barrel.age = RadiationBarrel.LEAK_STEPS - 2
        state['obstacles'].add(barrel)

    def each(state, frame, seen):
        seen['clouds'] = len(state['drains'])

    assert scene(play, setup, each)['clouds'] == 1


def test_whirlpool_drags_a_still_shark_in_the_game(play):
    def setup(state, seen):
        shark = state['shark'].rect
        pool = Whirlpool(shark.centerx + 80, shark.centery - Whirlpool.HEIGHT // 2)
        state['drains'].add(pool)
        seen['x'] = shark.centerx

    def each(state, frame, seen):
        state['energy'] = 100
        seen['moved'] = state['shark'].rect.centerx - seen['x']

    assert scene(play, setup, each, frames=10)['moved'] > 3


def test_a_run_with_every_new_hazard_stays_clean(play, monkeypatch):
    for zone in ('lagoon', 'pass', 'dropoff'):
        monkeypatch.setitem(ch.ZONES[zone], 'obstacles', ['barrel', 'emp_jelly'])
        monkeypatch.setitem(ch.ZONES[zone], 'enemies', ['piranha'])
        monkeypatch.setitem(ch.ZONES[zone], 'whirlpools', True)
    seen = {'kinds': set(), 'pools': 0, 'clouds': 0}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['score'] = 40
        seen['kinds'].update(sprite.kind for sprite in state['obstacles'])
        seen['pools'] += sum(isinstance(d, Whirlpool) for d in state['drains'])
        seen['clouds'] += sum(isinstance(d, RadiationCloud) for d in state['drains'])
        # Which kinds appear is random
        return frame >= 5000 and {'barrel', 'emp_jelly', 'piranha'} <= seen['kinds'] and seen['pools']

    assert play(script, quiet=False, max_frames=40000) == 'stopped'
    assert {'barrel', 'emp_jelly', 'piranha'} <= seen['kinds']
    assert seen['pools'] and seen['clouds']
