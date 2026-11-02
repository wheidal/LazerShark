import pygame
import pytest

from boss import LASER_DAMAGE, MorayEel
from bosses import GiantSquid
from obstacle import CoralReef, Shipwreck
from projectile import Laser
from weapons import BASE, LADDER, OBSTACLES_FOR_UPGRADE, UPGRADE_MS, WEAPONS, Bolt, WeaponPowerup, WeaponState


def test_the_ladder_runs_laser_shotgun_rapid_fan():
    assert LADDER == ['laser', 'shotgun', 'rapid', 'fan']
    assert set(LADDER) - {BASE} == set(WEAPONS)


def test_each_upgrade_is_one_step_up_and_stops_at_the_top():
    weapon = WeaponState()
    assert weapon.kind == BASE and weapon.label is None and not weapon.at_best
    seen = []
    for _ in LADDER[1:]:
        weapon.upgrade()
        seen.append(weapon.kind)
    assert seen == LADDER[1:] and weapon.at_best
    weapon.upgrade()
    assert weapon.kind == 'fan'


def test_a_hit_is_one_step_down_and_stops_at_the_laser():
    weapon = WeaponState()
    weapon.kind = 'fan'
    weapon.downgrade()
    assert weapon.kind == 'rapid'
    weapon.downgrade()
    weapon.downgrade()
    weapon.downgrade()
    assert weapon.kind == BASE


def test_shotgun_is_the_new_name_for_the_red_balls():
    assert WEAPONS['shotgun']['name'] == 'SHOTGUN' and WEAPONS['shotgun'].get('ball')
    assert 'chum' not in WEAPONS


def test_there_are_no_letters_on_pickups():
    for spec in WEAPONS.values():
        assert 'letter' not in spec
    assert WeaponPowerup(0, 0).image is WeaponPowerup(9, 9).image


@pytest.mark.parametrize('kind', WEAPONS)
def test_each_weapon_fires_its_promised_shots(display, kind):
    weapon = WeaponState()
    weapon.kind = kind
    assert len(weapon.fire(400, 300)) == WEAPONS[kind]['shots']
    assert weapon.cost == WEAPONS[kind]['cost'] and weapon.cooldown == WEAPONS[kind]['cooldown']


def test_plain_laser_needs_no_table_entry(display):
    shots = WeaponState().fire(400, 300)
    assert len(shots) == 1 and type(shots[0]) is Laser


def test_fan_spreads_symmetrically(display):
    weapon = WeaponState()
    weapon.kind = 'fan'
    shots = weapon.fire(400, 300)
    for _ in range(20):
        for shot in shots:
            shot.update()
    xs = sorted(shot.rect.centerx for shot in shots)
    assert xs[0] < 400 - 50 and xs[-1] > 400 + 50
    assert abs((400 - xs[0]) - (xs[-1] - 400)) <= 3


def test_shotgun_spreads_almost_120_degrees_with_no_range_limit(display):
    weapon = WeaponState()
    weapon.kind = 'shotgun'
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
    weapon.kind = 'fan'
    group.add(weapon.fire(400, 300))
    for _ in range(300):
        group.update()
    assert not group


def test_shotgun_ball_counts_for_less_than_a_laser_hit(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            seen['wreck'] = Shipwreck(400, 100)
            state['obstacles'].add(seen['wreck'])
            seen['shot'] = Bolt(seen['wreck'].rect.centerx, seen['wreck'].rect.bottom + 30, 'shotgun')
            state['projectiles'].add(seen['shot'])
        return frame >= 5

    play(script)
    assert seen['wreck'].hits == WEAPONS['shotgun']['power']
    assert not seen['shot'].alive()


def test_shot_power_scales_boss_damage_including_tentacles(display):
    eel = MorayEel(75, 725)
    eel.shot_power = 0.5
    eel.on_shot([])
    assert eel.health == eel.max_health - 0.5 * LASER_DAMAGE
    squid = GiantSquid(75, 725)
    squid.update(pygame.Rect(400, 500, 45, 104))
    squid.shot_power = 0.5
    start = squid.tentacles[0]['hp']
    squid.on_shot([squid.tentacles[0]['parts'][0]])
    assert squid.tentacles[0]['hp'] == start - 0.5
    assert squid.health == squid.max_health - 0.5


def pickup_scene(play, start_kind):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['weapon'].kind = start_kind
            state['weapon'].time_left = UPGRADE_MS
            state['shark'].laser_energy = 10
            pickup = WeaponPowerup(state['shark'].rect.centerx, state['shark'].rect.centery)
            state['powerups'].add(pickup)
            state['all_sprites'].add(pickup)
        seen['kind'] = state['weapon'].kind
        seen['label'] = state['weapon'].label
        seen['laser'] = state['shark'].laser_energy
        seen['banner'] = state['banner']
        return frame >= 3

    play(script)
    return seen


def test_pickup_moves_up_one_weapon_in_the_game(play):
    seen = pickup_scene(play, 'laser')
    assert seen['label'] == 'SHOTGUN' and seen['banner'] == 'SHOTGUN!'


def test_pickup_at_the_top_recharges_the_laser_instead(play):
    seen = pickup_scene(play, 'fan')
    assert seen['kind'] == 'fan'
    assert seen['laser'] > 90 and seen['banner'] == 'LASER RECHARGED!'


def test_a_hit_in_the_game_drops_one_weapon(play):
    seen = {}

    def script(state, frame):
        shark = state['shark']
        if frame == 1:
            state['weapon'].kind = 'rapid'
            state['weapon'].time_left = UPGRADE_MS
            state['obstacles'].add(CoralReef(shark.rect.centerx, shark.rect.centery - 30))
        seen['kind'] = state['weapon'].kind
        return frame >= 3

    play(script)
    assert seen['kind'] == 'shotgun'


def test_an_upgrade_wears_off_one_step_at_a_time():
    weapon = WeaponState()
    weapon.upgrade()
    weapon.upgrade()
    assert weapon.time_share == 1
    weapon.update(UPGRADE_MS / 2)
    assert weapon.kind == 'rapid' and weapon.time_share == pytest.approx(0.5)
    weapon.update(UPGRADE_MS / 2)
    assert weapon.kind == 'shotgun' and weapon.time_share == 1
    weapon.update(UPGRADE_MS)
    assert weapon.kind == BASE and weapon.time_share is None
    weapon.update(UPGRADE_MS)
    assert weapon.kind == BASE


def test_a_new_upgrade_restarts_the_clock():
    weapon = WeaponState()
    weapon.upgrade()
    weapon.update(UPGRADE_MS - 1)
    weapon.upgrade()
    assert weapon.kind == 'rapid' and weapon.time_left == UPGRADE_MS


def test_weapon_wears_off_in_the_game_and_stops_when_paused(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['weapon'].upgrade()
            state['weapon'].time_left = 200
        seen['kind'] = state['weapon'].kind
        return frame >= 30

    play(script)
    assert seen['kind'] == BASE


def test_upgrades_only_arrive_on_their_timer_and_not_in_a_fight(play):
    seen = {'most': 0}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['upgrade_timer'] = 10 ** 7
        seen['most'] = max(seen['most'], sum(isinstance(p, WeaponPowerup) for p in state['powerups']))
        return frame >= 5

    play(script, quiet=False)
    assert seen['most'] == 1


def test_it_takes_ten_obstacles_to_earn_an_upgrade():
    assert OBSTACLES_FOR_UPGRADE == 10


def test_shield_fades_after_its_time_without_shattering(play):
    from main import SHIELD_MS
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['shield_active'], state['shield_strength'] = True, 100
            state['shield_timer'] = SHIELD_MS - 100
        seen['active'] = state['shield_active']
        seen['strength'] = state['shield_strength']
        seen['shards'] = len(state['shark_look'].shards)
        return frame >= 20

    play(script)
    assert not seen['active'] and seen['strength'] == 0 and seen['shards'] == 0


def test_new_shield_gets_a_fresh_timer(play):
    from powerup import ShieldPowerup
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['shield_active'], state['shield_strength'] = True, 50
            state['shield_timer'] = 19000
            shark = state['shark'].rect
            state['powerups'].add(ShieldPowerup(shark.centerx, shark.centery))
        if frame == 4:
            seen['timer'] = state['shield_timer']
            return True

    play(script)
    assert seen['timer'] < 1000
