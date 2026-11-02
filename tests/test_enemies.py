import random

import pygame
import pytest

import channel as ch
from enemies import (SPAWN_SPEEDUP_PER_AREA, enemy_spawn_ms, toughen, ENEMY_LIMIT, ENEMY_SPAWN_MS, ENEMY_TYPES, Barracuda, Enemy, EnemyTorpedo, EvilSub, KamikazeTuna,
                     LaserManta, MantaBeam, choose_enemy)
from obstacle import SeaMine
from projectile import Laser

SHARK = pygame.Rect(380, 450, 45, 104)


def run(sprite, steps, group=None):
    group = group or pygame.sprite.Group(sprite)
    for _ in range(steps):
        group.update()
        if not sprite.alive():
            break


def test_zones_name_real_enemies_and_the_arena_has_none():
    for zone in ch.ZONES.values():
        assert set(zone['enemies']) <= set(ENEMY_TYPES)
    assert ch.ZONES['arena']['enemies'] == []


def test_harder_means_more_enemies_sooner():
    assert ENEMY_LIMIT['easy'] < ENEMY_LIMIT['normal'] < ENEMY_LIMIT['hard']
    assert ENEMY_SPAWN_MS['easy'] > ENEMY_SPAWN_MS['normal'] > ENEMY_SPAWN_MS['hard']


def test_tougher_enemies_wait_for_a_higher_score():
    assert choose_enemy(['evil_sub'], 0) is None
    assert choose_enemy(['evil_sub'], EvilSub.min_score) is EvilSub
    assert choose_enemy(['tuna', 'evil_sub'], 0) is KamikazeTuna


def test_tuna_locks_on_then_charges_where_the_shark_was(display):
    shark = SHARK.copy()
    tuna = KamikazeTuna(400, -70, shark)
    group = pygame.sprite.Group(tuna)
    while tuna.state != 'lock':
        group.update()
    heading = pygame.math.Vector2(tuna.heading)
    shark.x = 100  # A sidestep after the lock makes it miss
    while tuna.state != 'charge':
        group.update()
    assert tuna.heading == heading
    run(tuna, 300, group)
    assert not tuna.alive()


def test_tuna_warning_gives_time_to_sidestep(display):
    # From the hover height down to the shark, against the time to swim clear
    assert KamikazeTuna.LOCK_STEPS * 5 >= 45 + 30


def test_manta_stops_to_aim_then_fires_and_finally_leaves(display):
    manta = LaserManta(400, -70, SHARK)
    group = pygame.sprite.Group(manta)
    beams, aimed = 0, False
    for _ in range(3000):
        group.update()
        aimed = aimed or manta.state == 'aim'
        beams += len(manta.new_shots)
        manta.new_shots = []
        if not manta.alive():
            break
    assert aimed and beams == LaserManta.SHOTS
    assert not manta.alive()


def test_manta_aiming_time_beats_the_beam(display):
    assert LaserManta.AIM_STEPS * 5 > MantaBeam.WIDTH / 2 + 45 / 2


def test_barracuda_pack_size_and_formation(display):
    for _ in range(30):
        pack = Barracuda.create(400, SHARK)
        assert len(pack) in (3, 5)
        assert all(abs(fish.pos.x - 400) + Barracuda.WEAVE + 12 <= Barracuda.WIDTH / 2 + 30 for fish in pack)
        assert len({(fish.pos.x, fish.pos.y) for fish in pack}) == len(pack)


def test_evil_sub_fires_torpedoes_and_lays_mines(display):
    sub = EvilSub(400, -60, SHARK)
    group = pygame.sprite.Group(sub)
    released = []
    for _ in range(600):
        group.update()
        released += sub.new_obstacles
        sub.new_obstacles = []
    kinds = {type(thing) for thing in released}
    assert kinds == {EnemyTorpedo, SeaMine}


@pytest.mark.parametrize('kind', ENEMY_TYPES.values())
def test_every_enemy_eventually_leaves_the_screen(display, kind):
    for sprite in kind.create(400, SHARK):
        group = pygame.sprite.Group(sprite)
        run(sprite, 4000, group)
        assert not sprite.alive()


def enemy_scene(play, build, per_frame=None, frames=5):
    seen = {}

    def script(state, frame):
        if frame == 1:
            seen['energy0'] = state['energy']
            seen['enemy'] = build(state)
            state['obstacles'].add(seen['enemy'])
            state['all_sprites'].add(seen['enemy'])
        if per_frame:
            per_frame(state, frame, seen)
        seen['energy'] = state['energy']
        seen['score'] = state['score']
        seen['powerups'] = len(state['powerups'])
        return frame >= frames

    play(script)
    return seen


def test_shots_wear_down_an_evil_sub_and_it_pays_out_when_destroyed(play):
    def per_frame(state, frame, seen):
        sub = seen['enemy']
        if frame == 2:
            sub.hits = sub.toughness - 1
            state['projectiles'].add(Laser(sub.rect.centerx, sub.rect.bottom + 8))

    seen = enemy_scene(play, lambda state: EvilSub(400, 200, state['shark'].rect), per_frame)
    assert not seen['enemy'].alive()
    assert seen['score'] >= EvilSub.reward
    assert seen['powerups'] == 1


def test_ramming_a_tuna_costs_its_damage_once(play):
    def build(state):
        return KamikazeTuna(*state['shark'].rect.center, state['shark'].rect)

    seen = enemy_scene(play, build)
    assert not seen['enemy'].alive()
    assert seen['energy0'] - seen['energy'] == pytest.approx(KamikazeTuna.damage, abs=1)


def test_a_shot_tuna_blast_clears_what_is_near_it(play):
    neighbour = {}

    def build(state):
        tuna = KamikazeTuna(400, 200, state['shark'].rect)
        tuna.hits = tuna.toughness - 1
        neighbour['near'] = Barracuda(450, 200, state['shark'].rect)
        state['obstacles'].add(neighbour['near'])
        state['projectiles'].add(Laser(tuna.rect.centerx, tuna.rect.bottom + 8))
        return tuna

    enemy_scene(play, build)
    assert not neighbour['near'].alive()


def test_charging_tuna_bursts_on_the_coast(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            tuna = KamikazeTuna(400, 300, state['shark'].rect)
            tuna.state = 'charge'
            tuna.heading = pygame.math.Vector2(1, 0)
            seen['tuna'] = tuna
            state['obstacles'].add(tuna)
        if not seen['tuna'].alive():
            seen['x'] = seen['tuna'].rect.centerx
            return True

    play(script, max_frames=200)
    assert seen['x'] < 790


def test_beam_hurts_once_then_fades(play):
    seen = {}

    def script(state, frame):
        if frame == 1:
            seen['start'] = state['energy']
            state['enemy_shots'].add(MantaBeam(state['shark'].rect.centerx, 0))
        seen['energy'] = state['energy']
        return frame >= 12

    play(script)
    assert seen['start'] - seen['energy'] == pytest.approx(MantaBeam.damage, abs=2)


def test_friendly_subs_are_gone():
    import powerup
    assert not hasattr(powerup, 'FriendlySubmarine')


def test_session_with_every_enemy_runs_clean(play, monkeypatch):
    for zone in ('lagoon', 'pass', 'dropoff'):
        monkeypatch.setitem(ch.ZONES[zone], 'enemies', list(ENEMY_TYPES))
    seen = {'kinds': set(), 'most': 0}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['score'] = 90
        enemies = [s for s in state['obstacles'] if isinstance(s, Enemy)]
        seen['kinds'].update(s.kind for s in enemies)
        return frame >= 4000 and set(ENEMY_TYPES) <= seen['kinds']  # Which kinds appear is random

    assert play(script, quiet=False, max_frames=40000) == 'stopped'
    assert set(ENEMY_TYPES) <= seen['kinds']


def test_slow_enemies_steer_back_into_open_water(display):
    bank = ch.ChannelChunk([(300, 700, 'pass')] * 7).build(200)
    sub = EvilSub(290, 230, SHARK)
    sub.rect.center = sub.pos
    start = sub.pos.x
    for _ in range(10):
        sub.steer_clear_of(bank)
        sub.update()
    assert sub.pos.x > start
    assert not pygame.sprite.spritecollideany(sub, pygame.sprite.Group(bank), pygame.sprite.collide_mask)


def test_mines_are_never_laid_inside_the_reef(play, monkeypatch):
    for zone in ('lagoon', 'pass', 'dropoff'):
        monkeypatch.setitem(ch.ZONES[zone], 'enemies', ['evil_sub'])
    seen = {'in_reef': 0, 'mines': 0}
    tracked = set()

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['score'] = 90
        for sprite in state['obstacles']:
            if isinstance(sprite, SeaMine) and sprite not in tracked:
                tracked.add(sprite)
                seen['mines'] += 1
                if pygame.sprite.spritecollideany(sprite, state['banks'], pygame.sprite.collide_mask):
                    seen['in_reef'] += 1
        return frame >= 5000

    play(script, quiet=False, max_frames=5000)
    assert seen['in_reef'] == 0


def test_barracuda_steer_as_a_pack_without_losing_their_weave(display):
    fish = Barracuda(290, 230, SHARK)
    fish.rect.center = fish.pos
    bank = ch.ChannelChunk([(300, 700, 'pass')] * 7).build(200)
    start = fish.home_x
    fish.steer_clear_of(bank)
    assert fish.home_x > start


def test_hovering_tuna_steers_but_a_charging_one_does_not(display):
    tuna = KamikazeTuna(290, 230, SHARK)
    tuna.rect.center = tuna.pos
    bank = ch.ChannelChunk([(300, 700, 'pass')] * 7).build(200)
    start = tuna.pos.x
    tuna.steer_clear_of(bank)
    assert tuna.pos.x > start
    tuna.state = 'charge'
    moved = tuna.pos.x
    tuna.steer_clear_of(bank)
    assert tuna.pos.x == moved


def test_enemies_steer_around_a_wreck_not_always_left(display):
    from giant_wreck import GiantWreck
    wreck = GiantWreck(400)
    wreck.rect.top = 200
    right_side = LaserManta(wreck.rect.right - 10, 300, SHARK)
    right_side.rect.center = right_side.pos
    start = right_side.pos.x
    right_side.steer_clear_of([wreck])
    assert right_side.pos.x > start


def test_enemy_torpedo_bursts_on_the_coast(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            torpedo = EnemyTorpedo(400, 300, state['shark'].rect)
            torpedo.velocity = pygame.math.Vector2(11, 0)
            seen['torpedo'] = torpedo
            state['obstacles'].add(torpedo)
        if not seen['torpedo'].alive():
            seen['x'] = seen['torpedo'].rect.centerx
            return True

    play(script, max_frames=200)
    assert seen['x'] < 790


def test_steering_keeps_enemies_off_the_reef_in_play(play, monkeypatch):
    for zone in ('lagoon', 'pass', 'dropoff'):
        monkeypatch.setitem(ch.ZONES[zone], 'enemies', ['barracuda', 'piranha', 'manta', 'evil_sub'])
    seen = {'on': 0, 'total': 0}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['score'] = 100
            state['next_boss'] = 5  # No boss to interrupt the run
        for sprite in state['obstacles']:
            if isinstance(sprite, Enemy):
                seen['total'] += 1
                seen['on'] += bool(pygame.sprite.spritecollideany(sprite, state['banks'], pygame.sprite.collide_mask))
        return frame >= 3000

    play(script, quiet=False, max_frames=3000)
    assert seen['total'] > 1000
    assert seen['on'] / seen['total'] < 0.01


def test_enemies_get_tougher_with_each_area(display):
    def toughness(area):
        tuna = KamikazeTuna(400, 0, SHARK)
        toughen([tuna], area)
        return tuna.toughness

    assert toughness(0) == KamikazeTuna.toughness
    assert toughness(5) > toughness(0)
    sub = EvilSub(400, 0, SHARK)
    toughen([sub], 5)
    assert sub.toughness == round(EvilSub.toughness * 1.4)


def test_the_class_value_stays_put_when_one_enemy_is_toughened(display):
    start = LaserManta.toughness
    toughen([LaserManta(400, 0, SHARK)], 5)
    assert LaserManta.toughness == start


def test_enemies_arrive_sooner_with_each_area():
    for level in ENEMY_SPAWN_MS:
        assert enemy_spawn_ms(level, 0) == ENEMY_SPAWN_MS[level]
        assert enemy_spawn_ms(level, 5) == pytest.approx(ENEMY_SPAWN_MS[level] * (1 - SPAWN_SPEEDUP_PER_AREA) ** 5)


def test_spawned_enemies_in_a_later_area_are_tougher_in_play(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['next_boss'] = 5
            state['channel'].set_area(state['channel'].area)
            state['score'] = 0
        for sprite in state['obstacles']:
            if isinstance(sprite, KamikazeTuna):
                seen['toughness'] = sprite.toughness
                return True

    play(script, quiet=False, max_frames=20000)
    assert seen['toughness'] > KamikazeTuna.toughness
