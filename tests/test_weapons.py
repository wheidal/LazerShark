import pygame
import pytest

from bosses import BOSS_ROSTER, GiantSquid
from boss import LASER_DAMAGE, MorayEel
from obstacle import CoralReef, Shipwreck
from projectile import Laser
from weapons import BASE, EARNED_LEVEL, EARNED_WEAPON, MAX_LEVEL, WEAPONS, Bolt, WeaponPowerup, WeaponState


def test_collecting_swaps_and_powers_up():
    weapon = WeaponState()
    assert weapon.kind == BASE and weapon.label is None
    weapon.collect('fan')
    assert (weapon.kind, weapon.level) == ('fan', 1)
    for _ in range(5):
        weapon.collect('fan')
    assert weapon.level == MAX_LEVEL
    weapon.collect('beam')
    assert (weapon.kind, weapon.level, weapon.label) == ('beam', 1, 'BEAM 1')


def test_hits_drop_a_level_then_back_to_the_plain_laser():
    weapon = WeaponState()
    weapon.collect('rapid')
    weapon.collect('rapid')
    weapon.lose_level()
    assert (weapon.kind, weapon.level) == ('rapid', 1)
    weapon.lose_level()
    assert weapon.kind == BASE
    weapon.lose_level()
    assert weapon.kind == BASE


def test_earning_gives_fan_or_a_level():
    weapon = WeaponState()
    weapon.earn()
    assert (weapon.kind, weapon.level) == (EARNED_WEAPON, EARNED_LEVEL)
    weapon.collect('beam')
    weapon.earn()
    assert (weapon.kind, weapon.level) == ('beam', 2)


@pytest.mark.parametrize('kind', WEAPONS)
def test_every_level_fires_the_promised_shots_and_fits_the_table(display, kind):
    assert len(WEAPONS[kind]['levels']) == MAX_LEVEL
    weapon = WeaponState()
    for level in range(1, MAX_LEVEL + 1):
        weapon.kind, weapon.level = kind, level
        stats = WEAPONS[kind]['levels'][level - 1]
        assert len(weapon.fire(400, 300)) == stats['shots']
        assert weapon.cost == stats['cost'] and weapon.cooldown == stats['cooldown']


def test_fan_spreads_symmetrically(display):
    weapon = WeaponState()
    weapon.kind, weapon.level = 'fan', 3
    shots = weapon.fire(400, 300)
    for _ in range(20):
        for shot in shots:
            shot.update()
    xs = sorted(shot.rect.centerx for shot in shots)
    assert xs[0] < 400 - 50 and xs[-1] > 400 + 50
    assert abs((400 - xs[0]) - (xs[-1] - 400)) <= 3


def test_chum_cannon_spreads_almost_120_degrees_with_no_range_limit(display):
    weapon = WeaponState()
    weapon.kind, weapon.level = 'chum', 1
    shots = weapon.fire(400, 590)
    headings = [shot.velocity.angle_to(pygame.math.Vector2(0, -1)) for shot in shots]
    assert max(headings) - min(headings) == pytest.approx(116, abs=1)
    middle = [shot for shot in shots if abs(shot.velocity.x) < 0.01]
    assert len(middle) == 1  # One always flies straight ahead, so aiming still counts
    group = pygame.sprite.Group(middle)
    for _ in range(55):
        group.update()
    assert middle[0].alive() and middle[0].rect.top < 50


def test_bolts_leave_the_screen(display):
    group = pygame.sprite.Group()
    weapon = WeaponState()
    weapon.kind, weapon.level = 'fan', 3
    group.add(weapon.fire(400, 300))
    for _ in range(300):
        group.update()
    assert not group


def fire_at(play, build, make_shot, frames=3):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            seen['targets'] = build()
            state['obstacles'].add(seen['targets'])
            seen['shot'] = make_shot(seen['targets'][0])
            state['projectiles'].add(seen['shot'])
        return frame >= frames

    play(script)
    return seen


def bolt_for(kind, level=1):
    return lambda target: Bolt(target.rect.centerx, target.rect.bottom + 30, kind,
                               WEAPONS[kind]['levels'][level - 1])


def test_chum_ball_counts_for_less_than_a_laser_hit(play):
    seen = fire_at(play, lambda: [Shipwreck(400, 100)], bolt_for('chum'), frames=5)
    assert seen['targets'][0].hits == WEAPONS['chum']['levels'][0]['power']
    assert not seen['shot'].alive()


def test_beam_passes_through_and_hurts_each_obstacle_once(play):
    seen = fire_at(play, lambda: [Shipwreck(400, 250), Shipwreck(400, 40)], bolt_for('beam'), frames=30)
    power = WEAPONS['beam']['levels'][0]['power']
    assert seen['targets'][0].hits == power
    assert seen['targets'][1].hits == power


def test_shot_power_scales_boss_damage_including_tentacles(display):
    eel = MorayEel(75, 725)
    eel.shot_power = 0.5
    eel.on_shot([], False)
    assert eel.health == eel.max_health - 0.5 * LASER_DAMAGE
    squid = GiantSquid(75, 725)
    squid.update(pygame.Rect(400, 500, 45, 104))
    squid.shot_power = 0.5
    start = squid.tentacles[0]['hp']
    squid.on_shot([squid.tentacles[0]['parts'][0]], False)
    assert squid.tentacles[0]['hp'] == start - 0.5
    assert squid.health == squid.max_health - 0.5


def test_beam_hurts_a_boss_once_per_shot(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['score'] = BOSS_ROSTER[0][1]
        fight = state['boss']
        if fight:
            fight.state = 'exposed'
            fight.timer = 9999
            fight.y, fight.head_x = 200, 400
            if 'shot' not in seen and fight.parts:
                seen['start'] = fight.health
                seen['shot'] = Bolt(400, 300, 'beam', WEAPONS['beam']['levels'][0])
                state['projectiles'].add(seen['shot'])
            if 'shot' in seen and not seen['shot'].alive():
                seen['end'] = fight.health
                return True

    play(script, max_frames=6000)
    assert seen['start'] - seen['end'] == WEAPONS['beam']['levels'][0]['power'] * 2


def test_picking_up_a_weapon_in_the_game(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            pickup = WeaponPowerup(state['shark'].rect.centerx, state['shark'].rect.centery, 'rapid')
            state['powerups'].add(pickup)
            state['all_sprites'].add(pickup)
        seen['label'] = state['weapon'].label
        return frame >= 3

    play(script)
    assert seen['label'] == 'RAPID 1'


def test_firing_uses_the_weapon_and_a_hit_costs_a_level(play):
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['weapon'].collect('fan')
            state['weapon'].collect('fan')
            state['shark'].fire_cooldown = 0
            shots = state['weapon'].fire(400, 300)
            seen['count'] = len(shots)
            coral = CoralReef(state['shark'].rect.centerx, state['shark'].rect.centery - 30)
            state['obstacles'].add(coral)
        seen['label'] = state['weapon'].label
        return frame >= 3

    play(script)
    assert seen['count'] == 5
    assert seen['label'] == 'FAN 1'


def test_plain_laser_needs_no_table_entry(display):
    shots = WeaponState().fire(400, 300)
    assert len(shots) == 1 and type(shots[0]) is Laser
