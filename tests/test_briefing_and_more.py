import pygame
import pytest

import channel as ch
from areas import AREAS, INTERLUDES
from enemies import ENEMY_TYPES, HarpoonDiver, RockMoray, UrchinDrone
from features import CABLE_OFF_STEPS, CABLE_ON_STEPS, CABLE_WARN_STEPS, ElectricCable
from obstacle import DepthCharge, OBSTACLE_TYPES
from projectile import Laser
from weapons import WEAPONS, Bolt, WeaponState

SHARK = pygame.Rect(380, 450, 45, 104)


def test_everything_new_is_used_somewhere():
    used_enemies = set()
    used_obstacles = set()
    for area in AREAS + list(INTERLUDES.values()):
        used_enemies |= set(area.get('enemies', []))
        used_obstacles |= set(area.get('obstacles', []))
    for zone in ch.ZONES.values():
        used_enemies |= set(zone['enemies'])
        used_obstacles |= set(zone['obstacles'])
    assert {'rock_moray', 'diver', 'urchin'} <= used_enemies <= set(ENEMY_TYPES)
    assert 'depth_charge' in used_obstacles
    assert any(area.get('cables') for area in AREAS + list(INTERLUDES.values()))


def test_rock_moray_waits_warns_lunges_and_goes_back(display):
    shark = SHARK.copy()
    shark.centery = 600
    moray = RockMoray(80, 0, shark, -1)
    group = pygame.sprite.Group(moray)
    start = moray.pos.x
    for _ in range(40):
        group.update()
    assert moray.state == 'waiting'
    shark.centery = moray.pos.y
    states = []
    for _ in range(200):
        group.update()
        states.append(moray.state)
    assert {'warning', 'lunge', 'hold', 'retract', 'done'} <= set(states)
    assert max(moray.out for _ in [0]) == 0  # Back in its hole
    assert abs(moray.pos.x - start) < 2


def test_rock_moray_warning_gives_time_to_get_clear():
    assert RockMoray.WARN_STEPS * ch.SHARK_SPEED > RockMoray.REACH - 50


def test_diver_fires_harpoons_only_from_ahead(display):
    shark = SHARK.copy()
    diver = HarpoonDiver(60, 0, shark, -1)
    group = pygame.sprite.Group(diver)
    fired = []
    for _ in range(400):
        group.update()
        fired += [(diver.pos.y, shot) for shot in diver.new_shots]
        diver.new_shots = []
    assert fired
    assert all(y < shark.top for y, _ in fired)
    assert all(shot.damage == 12 for _, shot in fired)


def test_urchin_sprays_needles_when_destroyed(display):
    urchin = UrchinDrone(400, 100, SHARK)
    needles = urchin.on_destroyed()
    assert len(needles) == UrchinDrone.NEEDLES and all(n.damage == UrchinDrone.NEEDLE_DAMAGE for n in needles)


def test_destroying_an_urchin_in_play_releases_needles(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            urchin = UrchinDrone(400, 150, state['shark'].rect)
            urchin.hits = urchin.toughness - 1
            state['obstacles'].add(urchin)
            state['projectiles'].add(Laser(400, 200))
        seen['needles'] = max(seen.get('needles', 0), len(state['enemy_shots']))
        return frame >= 6

    play(script)
    assert seen['needles'] >= UrchinDrone.NEEDLES


def test_depth_charge_sinks_and_blows_on_its_own_timer(display):
    charge = DepthCharge(400, 0)
    far = pygame.Rect(0, 0, 45, 104)
    far.center = (700, 500)
    charge.sense(far)
    start = charge.rect.y
    steps = charge.fuse
    for _ in range(steps):
        charge.update()
    assert charge.fuse_done
    assert charge.rect.y - start >= steps * DepthCharge.SINK - 2


def test_depth_charge_in_play_goes_off_without_the_shark_near(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            seen['charge'] = DepthCharge(100, 100)
            seen['charge'].fuse = 5
            state['obstacles'].add(seen['charge'])
        seen['energy'] = state['energy']
        return frame >= 12

    play(script)
    assert not seen['charge'].alive() and seen['energy'] > 95


def test_cable_sparks_then_arcs_once_per_cycle(display):
    cable = ElectricCable(100, 700, -800, -1)
    assert cable.rect.left == 100 and cable.rect.width == int(600 * 0.6)
    group = pygame.sprite.Group(cable)
    for _ in range(CABLE_OFF_STEPS + CABLE_WARN_STEPS - 1):
        group.update()
        assert not cable.active
    group.update()
    group.update()
    assert cable.active
    right = ElectricCable(100, 700, 0, 1)
    assert right.rect.right == 700


def test_homing_bolt_turns_towards_a_target_ahead(display):
    target = pygame.sprite.Sprite()
    target.image = pygame.Surface((20, 20))
    target.rect = target.image.get_rect(center=(550, 150))
    group = pygame.sprite.Group(target)
    bolt = Bolt(400, 400, 'homing', 0, lambda: group.sprites())
    for _ in range(25):
        bolt.update()
    assert bolt.rect.centerx > 430
    plain = Bolt(400, 400, 'fan', 0, lambda: group.sprites())
    for _ in range(25):
        plain.update()
    assert plain.rect.centerx == 400


def test_homing_is_the_top_of_the_ladder(display):
    weapon = WeaponState()
    weapon.kind = 'homing'
    assert weapon.at_best and len(weapon.fire(400, 300, lambda: [])) == WEAPONS['homing']['shots']


def test_coast_dwellers_spawn_against_the_bank_in_play(play, monkeypatch):
    for zone in ('lagoon', 'pass', 'dropoff'):
        monkeypatch.setitem(ch.ZONES[zone], 'enemies', ['rock_moray', 'diver'])
    seen = {'gaps': []}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['score'] = 60
            state['next_boss'] = 9
        for sprite in state['obstacles']:
            if isinstance(sprite, (RockMoray, HarpoonDiver)) and not hasattr(sprite, 'checked'):
                sprite.checked = True
                left = state['channel'].coast_x(-1)
                right = state['channel'].coast_x(1)
                seen['gaps'].append(min(abs(sprite.rect.left - left), abs(sprite.rect.right - right)))
        return frame >= 3000 and len(seen['gaps']) >= 4

    play(script, quiet=False, max_frames=30000)
    assert len(seen['gaps']) >= 4
    assert all(gap < 160 for gap in seen['gaps'])
