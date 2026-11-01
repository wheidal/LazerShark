import random

import pygame
import pytest

import boss as boss_module
from bosses import BOSS_ROSTER, GiantSquid, Guardian, LavaCrab, LavaVent, RivalShark
from projectile import Laser

LEFT, RIGHT = 75, 725
ALL_BOSSES = [cls for cls, _ in BOSS_ROSTER]


def shark_at(x=400, y=500):
    rect = pygame.Rect(0, 0, 45, 104)
    rect.center = (x, y)
    return rect


def test_roster_comes_in_score_order_with_room_between_fights():
    scores = [score for _, score in BOSS_ROSTER]
    assert scores == sorted(scores)
    for earlier, later in zip(scores, scores[1:]):
        assert later - earlier > boss_module.VICTORY_SCORE


def test_later_bosses_are_tougher():
    scales = [cls.health_scale for cls in ALL_BOSSES]
    assert scales == sorted(scales)
    assert len(set(scales)) == len(scales)


@pytest.mark.parametrize('cls', ALL_BOSSES)
@pytest.mark.parametrize('difficulty', boss_module.DIFFICULTIES)
def test_runs_long_and_draws_without_trouble(display, cls, difficulty):
    fight = cls(LEFT, RIGHT, difficulty)
    rng = random.Random(1)
    shark = shark_at()
    for step in range(5000):
        if step % 30 == 0:
            shark = shark_at(rng.randint(100, 700), rng.randint(200, 540))
        fight.update(shark)
        for part in fight.parts:
            assert -80 <= part.rect.centerx <= 880 and -80 <= part.rect.centery <= 680
        if step % 50 == 0:
            fight.draw(display)
    assert not fight.dead


@pytest.mark.parametrize('cls', ALL_BOSSES)
def test_lasers_alone_can_always_finish_it(display, cls):
    fight = cls(LEFT, RIGHT, 'hard')
    shark = shark_at()
    for step in range(60000):
        fight.update(shark)
        if step % 6 == 0:
            aim = fight.targets()
            if aim and aim[0].alive():
                fight.on_shot(pygame.sprite.Group(aim[0]).sprites(), False)
        if fight.dead:
            return
    raise AssertionError(f'{cls.__name__} could not be beaten with lasers')


def test_squid_head_is_safe_until_every_tentacle_is_gone(display):
    squid = GiantSquid(LEFT, RIGHT)
    squid.update(shark_at())
    squid.on_shot([squid.head], True)
    assert squid.health == squid.max_health
    for tentacle in squid.tentacles:
        while tentacle['hp'] > 0:
            squid.on_shot([tentacle['parts'][0]], True)
    before = squid.health
    assert before > 0
    squid.on_shot([squid.head], False)
    assert squid.health == before - boss_module.HEAD_LASER_DAMAGE


def test_squid_shot_off_mid_slam_recovers(display):
    squid = GiantSquid(LEFT, RIGHT)
    for _ in range(2000):
        squid.update(shark_at())
        if squid.state == 'slam':
            break
    squid.slamming['hp'] = 0
    squid.update(shark_at())
    assert squid.state == 'rest' and squid.slamming is None


def test_crab_shrugs_off_lasers_until_it_overheats(display):
    crab = LavaCrab(LEFT, RIGHT)
    crab.update(shark_at())
    crab.on_shot([crab.shell], False)
    assert crab.health == crab.max_health
    crab.on_shot([crab.shell], True)
    assert crab.health == crab.max_health - crab.ARMOUR_HEAVY_DAMAGE
    for _ in range(2000):
        crab.update(shark_at())
        if crab.state == 'overheat':
            break
    before = crab.health
    crab.on_shot([crab.shell], False)
    assert crab.health == before - boss_module.HEAD_LASER_DAMAGE


def test_vents_warn_long_enough_to_swim_out_and_only_hurt_when_erupting(display):
    for ranges in boss_module.DIFFICULTIES.values():
        quickest = int(ranges['warn_steps'][0] * boss_module.ANGRY_WARN_SHARE)
        assert quickest * 5 > LavaVent.RADIUS + 45 / 2
    vent = LavaVent((300, 300), 10)
    states = []
    for _ in range(9):
        vent.update()
        states.append(vent.active)
    assert not any(states)
    vent.update()
    assert vent.active
    for _ in range(LavaVent.ERUPT_STEPS):
        vent.update()
    assert not vent.alive()


def test_rival_shield_needs_the_lit_switch(display):
    rival = RivalShark(LEFT, RIGHT)
    rival.update(shark_at())
    rival.on_shot([rival.body], True)
    assert rival.health == rival.max_health and rival.shielded
    rival.on_shot([rival.switches[1 - rival.lit]], False)
    assert rival.shielded
    lit = rival.lit
    rival.on_shot([rival.switches[lit]], False)
    assert not rival.shielded
    rival.on_shot([rival.body], False)
    assert rival.health == rival.max_health - boss_module.HEAD_LASER_DAMAGE
    for _ in range(rival.SHIELD_DOWN_STEPS + 1):
        rival.update(shark_at())
    assert rival.shielded and rival.lit != lit


def test_rival_switches_are_harmless_to_swim_into(display):
    rival = RivalShark(LEFT, RIGHT)
    rival.update(shark_at())
    rival.hazards.empty()
    switch = rival.switches[rival.lit]
    shark = pygame.sprite.Sprite()
    shark.rect = switch.rect.copy()
    shark.image = switch.image
    shark.mask = switch.mask
    assert not rival.touching(shark, pygame.sprite.collide_mask)


def test_guardian_cycles_every_attack_and_opens_up_after_each(display):
    guardian = Guardian(LEFT, RIGHT)
    fired, opened = set(), 0
    state = guardian.state
    for _ in range(4000):
        guardian.update(shark_at())
        if guardian.state != state:
            if guardian.state == 'attacking':
                fired.add(guardian.attack)
            if guardian.state == 'open':
                opened += 1
            state = guardian.state
    assert fired == set(Guardian.ATTACKS)
    assert opened >= 3


def test_guardian_armour_blocks_lasers_except_when_open(display):
    guardian = Guardian(LEFT, RIGHT)
    guardian.update(shark_at())
    guardian.on_shot([guardian.body], False)
    assert guardian.health == guardian.max_health
    guardian.state = 'open'
    guardian.on_shot([guardian.body], False)
    assert guardian.health == guardian.max_health - boss_module.HEAD_LASER_DAMAGE


@pytest.mark.parametrize('index', range(1, len(BOSS_ROSTER)))
def test_each_boss_is_summoned_and_beaten_in_the_real_game(play, index):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['next_boss'] = index
            state['score'] = BOSS_ROSTER[index][1]
        fight = state['boss']
        if fight:
            seen['name'] = fight.name
            aim = fight.targets()
            if aim and aim[0].alive():
                x, bottom = aim[0].rect.centerx, aim[0].rect.bottom
                state['projectiles'].add(Laser(x, bottom + 30))
        seen['next'] = state['next_boss']
        return state['boss_phase'] == 'beaten'

    play(script, max_frames=20000)
    assert seen['name'] == BOSS_ROSTER[index][0].name
    assert seen['next'] == index + 1


def test_winning_leads_on_to_the_next_boss(play):
    seen = {'names': []}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['score'] = BOSS_ROSTER[0][1]
        fight = state['boss']
        if fight:
            if fight.name not in seen['names']:
                seen['names'].append(fight.name)
                if len(seen['names']) == 2:
                    return True
            fight.take_damage(9999)
        elif state['boss_phase'] == 'beaten' and state['score'] < BOSS_ROSTER[1][1]:
            state['score'] = BOSS_ROSTER[1][1]

    play(script, max_frames=8000)
    assert seen['names'] == [BOSS_ROSTER[0][0].name, BOSS_ROSTER[1][0].name]


def test_number_key_on_the_title_jumps_to_that_boss(play, monkeypatch):
    import conftest
    seen = {}
    real_press = conftest.press
    monkeypatch.setattr(conftest, 'press', lambda key: real_press(pygame.K_3 if key == pygame.K_a else key))

    def script(state, frame):
        state['energy'] = 100
        seen['next'] = state['next_boss']
        if state['boss']:
            seen['name'] = state['boss'].name
            return True

    play(script, max_frames=6000)
    assert seen['name'] == BOSS_ROSTER[2][0].name
