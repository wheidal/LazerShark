import pygame
import pytest

import channel as ch
from areas import AREAS, INTERLUDES, area_for
from bosses import BOSS_ROSTER
from conftest import SWITCHED_OFF_ENEMIES, WHIRLPOOLS_NORMALLY_ON
from coral import PIECE_MAKERS
from enemies import ENEMY_TYPES, Anglerfish, Hammerhead, Pufferfish, choose_enemy
from hazards import FIELD_TYPES, InkCloud, MagneticField, ToxicSludge
from music import AREA_TRACKS
from obstacle import OBSTACLE_TYPES, Boulder, FishingNet, TumblingRock
from story import AREA_TAUNTS
from projectile import Laser

SHARK = pygame.Rect(380, 450, 45, 104)


def test_tuna_and_whirlpools_start_switched_off():
    assert SWITCHED_OFF_ENEMIES == {'tuna'}
    assert WHIRLPOOLS_NORMALLY_ON is False


def test_a_switched_off_enemy_never_spawns_and_nor_do_whirlpools(monkeypatch):
    import enemies
    monkeypatch.setattr(enemies, 'DISABLED_ENEMIES', {'tuna'})
    assert choose_enemy(['tuna'], 999) is None
    monkeypatch.setattr(ch, 'WHIRLPOOLS_ON', False)
    director = ch.ChannelDirector()
    director.prefill()
    assert not director.has_whirlpools()


@pytest.mark.parametrize('area', list(INTERLUDES.values()), ids=lambda area: area['name'])
def test_new_areas_name_things_that_exist_and_have_words_and_music(area):
    assert set(area['decor']) <= set(PIECE_MAKERS)
    assert set(area['obstacles']) <= set(OBSTACLE_TYPES)
    assert set(area['enemies']) <= set(ENEMY_TYPES)
    assert set(area['fields']) <= set(FIELD_TYPES)
    assert area['name'] in AREA_TAUNTS and area['name'] in AREA_TRACKS


def test_every_area_uses_real_fields():
    for area in AREAS:
        assert set(area.get('fields', [])) <= set(FIELD_TYPES)
    for zone in ch.ZONES.values():
        assert set(zone.get('fields', [])) <= set(FIELD_TYPES)
        assert set(zone['obstacles']) <= set(OBSTACLE_TYPES)


def test_interlude_comes_halfway_to_its_boss_only():
    assert area_for(1, 0.2) is AREAS[1]
    assert area_for(1, 0.6) is INTERLUDES[1]
    assert area_for(1, 1.0) is AREAS[1]
    assert area_for(2, 0.6) is AREAS[2]


def test_run_moves_into_the_interlude_when_the_score_gets_there(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['next_boss'] = 1
            state['score'] = 300
        seen['area'] = state['channel'].area
        seen['tint'] = state['graphics_enhancer'].area_tint
        return frame >= 3

    play(script)
    assert seen['area'] is INTERLUDES[1] and seen['tint'] is not None


def test_net_slows_but_does_not_hurt(play):
    seen = {}

    def script(state, frame):
        shark = state['shark']
        if frame == 1:
            seen['start'] = state['energy']
            state['obstacles'].add(FishingNet(shark.rect.centerx, shark.rect.centery - 30))
        seen['speed'] = shark.speed
        seen['energy'] = state['energy']
        return frame >= 4

    play(script)
    assert seen['speed'] < ch.SHARK_SPEED
    assert seen['start'] - seen['energy'] < 2


def test_slowness_wears_off(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['slow_timer'] = 100
        seen['speed'] = state['shark'].speed
        return frame >= 20

    play(script)
    assert seen['speed'] == ch.SHARK_SPEED


def test_boulder_takes_many_hits(display):
    assert Boulder.toughness >= 8


def test_tumbling_rock_stays_within_its_sway(display):
    rock = TumblingRock(400, 100)
    xs = set()
    for _ in range(400):
        rock.update()
        xs.add(rock.rect.centerx)
    assert max(xs) <= 400 + TumblingRock.SWAY and min(xs) >= 400 - TumblingRock.SWAY


def test_pufferfish_swells_when_close_then_bursts_into_spines(display):
    shark = SHARK.copy()
    fish = Pufferfish(shark.centerx, shark.centery - 100, shark)
    group = pygame.sprite.Group(fish)
    group.update()
    assert fish.swell_left is not None
    assert fish.image is fish.frames[True]
    spines = []
    for _ in range(Pufferfish.SWELL_STEPS + 2):
        group.update()
        spines += fish.new_shots
        fish.new_shots = []
    assert len(spines) == Pufferfish.SPINES and all(s.damage == Pufferfish.SPINE_DAMAGE for s in spines)
    assert not fish.alive()


def test_killing_a_pufferfish_first_means_no_spines(display):
    fish = Pufferfish(400, -40, SHARK)
    group = pygame.sprite.Group(fish)
    for _ in range(5):
        group.update()
    assert fish.swell_left is None and not fish.new_shots


def test_hammerhead_warns_then_crosses_the_screen_at_the_sharks_height(display):
    shark = SHARK.copy()
    fish = Hammerhead(0, 0, shark)
    assert fish.pos.y == shark.centery
    start = fish.pos.x
    group = pygame.sprite.Group(fish)
    for _ in range(Hammerhead.WARN_STEPS):
        group.update()
    assert fish.pos.x == start
    for _ in range(200):
        group.update()
    assert not fish.alive()


def test_hammerhead_warning_gives_time_to_get_clear():
    assert Hammerhead.WARN_STEPS * ch.SHARK_SPEED > 104


def test_anglerfish_waits_then_snaps_once(display):
    shark = SHARK.copy()
    fish = Anglerfish(shark.centerx, shark.top - 300, shark)
    group = pygame.sprite.Group(fish)
    for _ in range(40):
        group.update()
    assert fish.snap_left is None
    for _ in range(40):
        group.update()
    assert fish.snap_left is not None


def test_ink_only_covers_and_sludge_slows_and_drains(display):
    ink = InkCloud(400, 300)
    inside = SHARK.copy()
    inside.center = ink.rect.center
    assert ink.covers and ink.drain_on(inside) == 0 and ink.pull_on(inside) == (0, 0)
    sludge = ToxicSludge(400, 300)
    inside.center = sludge.rect.center
    assert sludge.drain_on(inside) > 0 and sludge.slows_shark(inside)
    inside.center = (sludge.rect.centerx + 400, sludge.rect.centery)
    assert sludge.drain_on(inside) == 0 and not sludge.slows_shark(inside)


def test_magnet_pulls_sideways_and_can_be_beaten(display):
    field = MagneticField(400, 100)
    shark = SHARK.copy()
    shark.center = (field.rect.centerx + 90, field.rect.centery)
    pull_x, pull_y = field.pull_on(shark)
    assert pull_x < 0 and pull_y == 0 and abs(pull_x) < ch.SHARK_SPEED


def test_shots_clear_a_net(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            seen['net'] = FishingNet(400, 200)
            seen['net'].hits = FishingNet.toughness - 1
            state['obstacles'].add(seen['net'])
            state['projectiles'].add(Laser(seen['net'].rect.centerx, seen['net'].rect.bottom))
        return frame >= 5

    play(script)
    assert not seen['net'].alive()


def test_a_run_with_all_the_new_things_stays_clean(play, monkeypatch):
    for zone in ('lagoon', 'pass', 'dropoff'):
        monkeypatch.setitem(ch.ZONES[zone], 'enemies', ['puffer', 'hammerhead', 'angler'])
        monkeypatch.setitem(ch.ZONES[zone], 'fields', list(FIELD_TYPES))
        monkeypatch.setitem(ch.ZONES[zone], 'obstacles', ['boulder', 'tumbling_rock', 'satellite', 'rocket', 'tower', 'net'])
    seen = {'kinds': set(), 'fields': set()}
    want = {'puffer', 'hammerhead', 'angler', 'boulder', 'tumbling_rock', 'satellite', 'rocket', 'tower', 'net'}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['score'] = 80
            state['next_boss'] = len(BOSS_ROSTER)
        seen['kinds'].update(sprite.kind for sprite in state['obstacles'])
        seen['fields'].update(type(d).__name__ for d in state['drains'])
        return frame >= 3000 and want <= seen['kinds'] and {'InkCloud', 'ToxicSludge', 'MagneticField'} <= seen['fields']

    assert play(script, quiet=False, max_frames=50000) == 'stopped'


def test_no_second_area_change_on_reaching_the_boss(play):
    seen = {'areas': []}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['next_boss'] = 1
            state['score'] = 300
        if frame == 5:
            state['score'] = BOSS_ROSTER[1][1]
        area = state['channel'].area['name']
        if not seen['areas'] or seen['areas'][-1] != area:
            seen['areas'].append(area)
        return frame >= 40

    play(script)
    assert seen['areas'][-1] == INTERLUDES[1]['name']
