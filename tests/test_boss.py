import json
import random

import pygame

import boss
import channel as ch
from conftest import press
from boss import MorayEel
from projectile import Laser

LEFT, RIGHT = 75, 725
BOT_SHARK = pygame.Rect(400, 450, 45, 104)


def run_until(eel, state, shark=BOT_SHARK, limit=2000):
    for _ in range(limit):
        eel.update(shark)
        if eel.state == state:
            return
    raise AssertionError(f'never reached {state}')


def test_arena_opens_wide_and_straight_then_leads_back(display):
    director = ch.ChannelDirector(random.Random(2))
    director.prefill()
    director.enter_arena()
    steps = 0
    while not director.arena_ready:
        director.update(0)
        steps += 1
        assert steps < 3000
    left, right = director.arena_edges
    assert abs(right - left - 650) <= 2 * ch.COAST_ROUGHNESS
    assert abs((left + right) / 2 - 400) <= ch.COAST_ROUGHNESS
    director.leave_arena()
    for _ in range(3000):
        director.update(0)
    assert director.zone in ch.ROUTE_ZONES


def test_entering_the_arena_stays_fair_on_bends(display):
    for seed in range(10):
        generator = ch.ChannelGenerator(random.Random(seed))
        generator.take(400, 500)
        generator.enter_arena()
        samples = generator.take(1500, 500)
        slopes = [max(abs(a[0] - b[0]), abs(a[1] - b[1])) / ch.SAMPLE_SPACING for a, b in zip(samples, samples[1:])]
        assert max(slopes) < ch.SHARK_SPEED / ch.SCROLL_PER_STEP + 1


def test_warning_gives_time_to_get_clear_before_a_lunge(display):
    eel = MorayEel(LEFT, RIGHT)
    run_until(eel, 'warning')
    assert not eel.parts
    # Long enough, even when angry, to swim clear of a lunge aimed at the shark's middle
    clearance = BOT_SHARK.height / 2 + 27
    for ranges in boss.DIFFICULTIES.values():
        assert int(ranges['warn_steps'][0] * boss.ANGRY_WARN_SHARE) * ch.SHARK_SPEED > clearance


def test_lunge_always_leaves_room_to_shoot_from_below(display):
    assert boss.LUNGE_Y_RANGE[1] + 27 + BOT_SHARK.height < ch.SCREEN_H
    eel = MorayEel(LEFT, RIGHT)
    for _ in range(3000):
        eel.update(pygame.Rect(400, 500, 45, 100))
        assert boss.LUNGE_Y_RANGE[0] <= eel.y <= boss.LUNGE_Y_RANGE[1]


def test_eel_stays_between_lair_and_reach_on_both_sides(display):
    eel = MorayEel(LEFT, RIGHT)
    sides = set()
    for _ in range(6000):
        eel.update(BOT_SHARK)
        for part in eel.parts:
            assert LEFT - 60 <= part.rect.centerx <= RIGHT + 60
        if eel.state == 'exposed':
            sides.add(eel.side)
            assert eel.head.alive()
    assert sides == {-1, 1}


def test_gets_faster_when_hurt(display):
    eel = MorayEel(LEFT, RIGHT)
    assert not eel.angry
    eel.take_damage(eel.max_health * 0.6)
    assert eel.angry
    run_until(eel, 'warning')
    assert eel.timer <= int(eel.warn_steps * boss.ANGRY_WARN_SHARE)


def fight(play, script_step, score=boss.BOSS_SCORE, max_frames=6000):
    seen = {'phases': []}

    def script(state, frame):
        if frame == 1:
            state['score'] = score
        if state['boss_phase'] not in seen['phases']:
            seen['phases'].append(state['boss_phase'])
        return script_step(state, frame, seen)

    play(script, max_frames=max_frames)
    return seen


def test_full_fight_reaches_the_arena_and_ends_in_victory(play):
    def step(state, frame, seen):
        state['energy'] = 100
        shark = state['shark']
        eel = state['eel']
        if eel:
            seen['saw_eel'] = True
            for part in eel.parts:
                shark.rect.centerx = part.rect.centerx
                shark.rect.top = part.rect.bottom + 60
                laser = Laser(part.rect.centerx, part.rect.bottom + 2)
                state['projectiles'].add(laser)
                state['all_sprites'].add(laser)
                break
        return state['boss_phase'] == 'beaten'

    seen = fight(play, step)
    assert seen['phases'][-3:] == ['approach', 'fight', 'beaten']
    assert seen['saw_eel']


def test_coast_holds_still_during_the_fight_and_scrolls_after(play):
    def step(state, frame, seen):
        state['energy'] = 100
        if state['eel']:
            state['eel'].state = 'hidden'
            state['eel'].timer = 999
            seen.setdefault('fight_frame', frame)
            seen.setdefault('y', sorted(b.rect.y for b in state['banks']))
            if frame - seen['fight_frame'] == 60:
                seen['same'] = seen['y'] == sorted(b.rect.y for b in state['banks'])
                state['eel'].take_damage(9999)
        return 'same' in seen and state['boss_phase'] == 'beaten' and frame - seen['fight_frame'] > 90

    seen = fight(play, step)
    assert seen['same']


def test_contact_costs_energy_once_per_second(play):
    def step(state, frame, seen):
        eel = state['eel']
        if not eel:
            state['energy'] = 100
            return False
        if 'start' not in seen:
            seen['start'] = frame
            state['energy'] = 100
        seen['bite'] = eel.bite_damage
        eel.state = 'exposed'
        eel.timer = 9999
        eel.y = state['shark'].rect.centery
        eel.head_x = state['shark'].rect.centerx
        seen['energy'] = state['energy']
        return frame - seen['start'] >= 30

    seen = fight(play, step)
    assert 100 - seen['bite'] - 3 <= seen['energy'] <= 100 - seen['bite'] + 1


def test_restart_clears_the_boss(play):
    def step(state, frame, seen):
        if state['eel'] and 'died' not in seen:
            seen['died'] = frame
            state['energy'] = -1
        elif 'died' not in seen:
            state['energy'] = 100
        elif frame == seen['died'] + 90:
            press(pygame.K_a)
        elif frame > seen['died'] + 90 and not state['game_over']:
            seen['after'] = (state['eel'], state['boss_phase'], state['score'])
            return True
        return False

    seen = fight(play, step)
    assert seen['after'] == (None, None, 0)


def test_full_lunges_shake_loose_more_when_angry(display):
    eel = MorayEel(LEFT, RIGHT)
    run_until(eel, 'exposed')
    assert eel.rubble_due == 1
    eel.rubble_due = 0
    eel.take_damage(eel.max_health * 0.6)
    run_until(eel, 'hidden')
    run_until(eel, 'exposed')
    assert eel.rubble_due == 2


def test_rubble_falls_during_the_fight(play):
    def step(state, frame, seen):
        state['energy'] = 100
        if state['eel']:
            seen['start'] = seen.get('start', frame)
            seen['most'] = max(seen.get('most', 0), len(state['obstacles']))
            return frame - seen['start'] > 600
        return False

    assert fight(play, step)['most'] >= 1


def test_game_carries_on_after_a_win_with_everything_spawning(play, monkeypatch):
    def script(state, frame):
        if frame == 1:
            state['score'] = boss.BOSS_SCORE
        state['energy'] = 100
        if state['eel']:
            state['eel'].take_damage(9999)
        if state['boss_phase'] == 'beaten':
            seen['after'] = seen.get('after', 0) + 1
            seen['zones'].add(state['channel'].zone)
            seen['obstacles'] += len(state['obstacles'])
            return seen['after'] >= 3000

    seen = {'zones': set(), 'obstacles': 0}
    assert play(script, quiet=False, max_frames=6000) == 'stopped'
    assert seen['after'] >= 3000
    assert 'arena' in seen['zones'] and seen['zones'] & ch.ROUTE_ZONES
    assert seen['obstacles'] > 0


def test_arena_is_straight_top_to_bottom_when_the_coast_stops(display):
    for seed in range(15):
        director = ch.ChannelDirector(random.Random(seed))
        director.prefill()
        chunks = []
        for _ in range(random.Random(seed).randint(0, 800)):
            chunk = director.update(100)
        director.enter_arena()
        while not director.arena_ready:
            chunk = director.update(100)
            if chunk:
                chunks.append(chunk)
        on_screen = chunks[-(ch.SCREEN_H // ch.CHUNK_H + 1):]
        for chunk in on_screen:
            for left, right, _ in chunk.samples:
                assert abs(left - 75) <= ch.COAST_ROUGHNESS + 2
                assert abs(right - 725) <= ch.COAST_ROUGHNESS + 2


def test_each_fight_rolls_values_within_its_difficulty(display):
    for name, ranges in boss.DIFFICULTIES.items():
        eels = [MorayEel(LEFT, RIGHT, name) for _ in range(200)]
        for attribute, key in (('max_health', 'health'), ('bite_damage', 'bite'), ('warn_steps', 'warn_steps')):
            values = {getattr(eel, attribute) for eel in eels}
            assert min(values) >= ranges[key][0] and max(values) <= ranges[key][1]
            assert len(values) > 1


def test_harder_levels_are_harder_on_every_value():
    easy, normal, hard = (boss.DIFFICULTIES[name] for name in ('easy', 'normal', 'hard'))
    assert easy['health'] < normal['health'] < hard['health']
    assert easy['bite'] < normal['bite'] < hard['bite']
    assert easy['warn_steps'] > normal['warn_steps'] > hard['warn_steps']


def test_unknown_difficulty_falls_back_to_normal(display):
    low, high = boss.DIFFICULTIES['normal']['health']
    assert low <= MorayEel(LEFT, RIGHT, 'nightmare').max_health <= high


def test_menu_choice_is_saved_and_used_by_the_fight(play, tmp_path):
    keys = [pygame.K_DOWN] * 5 + [pygame.K_RETURN, pygame.K_DOWN, pygame.K_RETURN]  # Normal becomes hard
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['score'] = boss.BOSS_SCORE
        state['energy'] = 100
        seen['difficulty'] = state['difficulty']
        if state['eel']:
            seen['health'] = state['eel'].max_health
            return True

    play(script, menu_keys=keys, max_frames=6000)
    assert seen['difficulty'] == 'hard'
    assert boss.DIFFICULTIES['hard']['health'][0] <= seen['health'] <= boss.DIFFICULTIES['hard']['health'][1]
    assert json.loads((tmp_path / 'game_settings.json').read_text())['difficulty'] == 'hard'
