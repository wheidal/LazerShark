import pygame

import channel as ch
from areas import AREAS
from enemies import ENEMY_TYPES, GuardianStatue
from features import (GATE_OFF_STEPS, GATE_ON_STEPS, GATE_WARN_STEPS, GEYSER_ERUPT_STEPS, GEYSER_REST_STEPS,
                      GEYSER_WARN_STEPS, GEYSER_WIDTH, GateSwitch, LaserGate, LavaGeyser)
from projectile import Laser


def test_geyser_warns_long_enough_to_swim_clear(display):
    assert GEYSER_WARN_STEPS * ch.SHARK_SPEED > GEYSER_WIDTH / 2 + 45 / 2


def test_geyser_cycles_and_can_hurt_once_per_eruption(display):
    geyser = LavaGeyser(400, -600)
    group = pygame.sprite.Group(geyser)
    states = []
    for _ in range(GEYSER_REST_STEPS + GEYSER_WARN_STEPS - 1):
        group.update()
        states.append(geyser.active)
    assert not any(states)
    for _ in range(3):
        group.update()
    assert geyser.active
    geyser.active = False  # The game does this when it hurts the shark
    group.update()
    assert not geyser.active
    for _ in range(GEYSER_ERUPT_STEPS + GEYSER_REST_STEPS + GEYSER_WARN_STEPS):
        group.update()
    assert geyser.active


def test_geyser_leaves_when_it_scrolls_off(display):
    geyser = LavaGeyser(400, 590)
    group = pygame.sprite.Group(geyser)
    for _ in range(50):
        group.update()
    assert not geyser.alive()


def make_gate(y=-600):
    gate = LaserGate(100, 700, y)
    return gate, pygame.sprite.Group(gate, gate.switch)


def test_gate_warns_then_fires_then_rests(display):
    gate, _ = make_gate()
    group = pygame.sprite.Group(gate)
    keep = pygame.sprite.Group(gate.switch)
    for _ in range(GATE_OFF_STEPS + GATE_WARN_STEPS - 1):
        group.update()
        assert not gate.active
    group.update()
    group.update()
    assert gate.active and gate.image is gate.on
    for _ in range(GATE_ON_STEPS + 2):
        group.update()
    assert not gate.active
    assert keep


def test_off_time_lets_the_shark_cross(display):
    assert GATE_OFF_STEPS * ch.SCROLL_PER_STEP > ch.SHARK_BODY_H + 20


def test_gate_blocks_the_whole_span_when_on(display):
    gate, _ = make_gate()
    for x in range(20, gate.rect.width - 20, 10):
        assert gate.mask.get_at((x, 9))


def test_destroying_the_switch_shuts_the_gate(display):
    gate, _ = make_gate()
    group = pygame.sprite.Group(gate)
    gate.switch.kill()
    group.update()
    assert not gate.alive()


def test_gate_span_reaches_under_both_banks(display):
    import random
    director = ch.ChannelDirector(random.Random(3))
    director.prefill()
    for _ in range(800):
        director.update(0)
        left, right = director.gate_span()
        window = director.recent[-2:]
        assert left <= max(0, min(s[0] for s in window)) + ch.COAST_ROUGHNESS * 3 + 40
        assert right >= min(800, max(s[1] for s in window)) - ch.COAST_ROUGHNESS * 3 - 40
        assert right - left > 150


def test_statue_scrolls_with_the_coast_warns_and_fires_only_ahead(display):
    shark = pygame.Rect(380, 450, 45, 104)
    statue = GuardianStatue(400, 0, shark)
    group = pygame.sprite.Group(statue)
    shots = []
    y = statue.pos.y
    lit = False
    for _ in range(100):
        group.update()
        assert statue.pos.y == y + ch.SCROLL_PER_STEP
        y = statue.pos.y
        lit = lit or statue.image is statue.frames[True]
        shots += statue.new_shots
        statue.new_shots = []
    assert lit and len(shots) == 1 and shots[0].damage == GuardianStatue.SHOT_DAMAGE
    for _ in range(70):
        group.update()
        assert not statue.new_shots or statue.pos.y < shark.top
        statue.new_shots = []


def test_every_area_feature_is_real_and_statues_are_atlantis_only():
    assert {area.get('feature') for area in AREAS} == {None, 'geyser', 'gate'}
    assert all('hint' in area for area in AREAS[1:])
    assert 'statue' in ENEMY_TYPES
    assert [i for i, area in enumerate(AREAS) if 'statue' in area.get('enemies', [])] == [3, 5]


def scene(play, area_index, script_step, frames=9000):
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['channel'].set_area(AREAS[area_index])
        return script_step(state, frame, seen)

    play(script, quiet=False, max_frames=frames)
    return seen


def test_rift_grows_geysers_in_play(play):
    def step(state, frame, seen):
        state['energy'] = 100
        seen['most'] = max(seen.get('most', 0), sum(isinstance(s, LavaGeyser) for s in state['enemy_shots']))
        return frame >= 1500

    assert scene(play, 2, step)['most'] >= 1


def test_lab_gets_gates_and_shooting_the_switch_works_in_play(play):
    def step(state, frame, seen):
        state['energy'] = 100
        gates = [s for s in state['enemy_shots'] if isinstance(s, LaserGate)]
        if gates and 'gate' not in seen and gates[0].switch.rect.top > 100:  # On screen, where shots live
            seen['gate'] = gates[0]
            switch = gates[0].switch
            state['projectiles'].add(Laser(switch.rect.centerx, switch.rect.bottom + 15))
        if 'gate' in seen and not seen['gate'].alive():
            seen['frames_after'] = seen.get('frames_after', 0) + 1
        return seen.get('frames_after', 0) > 1

    seen = scene(play, 4, step)
    assert 'gate' in seen and not seen['gate'].switch.alive()


def test_active_gate_hurts_once_per_burst_in_play(play):
    seen = {}

    def script(state, frame):
        if frame == 1:
            shark = state['shark'].rect
            gate = LaserGate(shark.left - 100, shark.right + 100, shark.centery)
            gate.switch.rect.center = (120, -300)
            gate.step = GATE_OFF_STEPS + GATE_WARN_STEPS - 1
            state['enemy_shots'].add(gate)
            state['obstacles'].add(gate.switch)
            seen['start'] = state['energy']
        seen['energy'] = state['energy']
        return frame >= 12

    play(script)
    assert seen['start'] - seen['energy'] < LaserGate.damage + 3
    assert seen['start'] - seen['energy'] > LaserGate.damage - 3


def test_a_run_through_each_special_area_stays_clean(play):
    for index in (2, 3, 4):
        def step(state, frame, seen):
            state['energy'] = 100
            return frame >= 1500

        scene(play, index, step)


def test_switch_is_shootable_like_any_obstacle(display):
    switch = GateSwitch((400, 300))
    assert switch.toughness == 1 and switch.mask.count() > 0
