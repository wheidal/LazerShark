import random

import pygame
import pytest

import channel as ch
from areas import AREAS, area_for
from bosses import BOSS_ROSTER
from coral import PIECE_MAKERS
from enemies import ENEMY_TYPES
from giant_wreck import H, MIN_GAP, PASSAGE, SIDE_ESCAPE, W, GiantWreck
from obstacle import OBSTACLE_TYPES


def test_there_is_an_area_for_every_boss_and_it_never_runs_out():
    assert len(AREAS) == len(BOSS_ROSTER)
    assert area_for(99) is AREAS[-1]
    assert ch.ChannelDirector().WRECK_MIN_GAP == MIN_GAP


@pytest.mark.parametrize('area', AREAS, ids=lambda area: area['name'])
def test_areas_only_name_things_that_exist(area):
    assert set(area.get('decor', [])) <= set(PIECE_MAKERS)
    assert set(area.get('obstacles', [])) <= set(OBSTACLE_TYPES)
    assert set(area.get('enemies', [])) <= set(ENEMY_TYPES)
    assert len(area.get('reef', [0] * 5)) == 5


def test_new_pieces_fit_inside_a_chunk(display):
    rng = random.Random(1)
    for name, make in PIECE_MAKERS.items():
        assert make(rng).get_height() < ch.CHUNK_H - 2, name


def test_area_changes_what_the_channel_uses_but_not_in_an_arena(display):
    director = ch.ChannelDirector(random.Random(2))
    director.prefill()
    reef = director.obstacle_kinds()
    director.set_area(AREAS[1])
    assert director.obstacle_kinds() == AREAS[1]['obstacles'] != reef
    assert director.enemy_kinds() == AREAS[1]['enemies']
    chunk = director._next_chunk(0)
    assert chunk.decor == AREAS[1]['decor']
    chunk.build()
    director.enter_arena()
    for _ in range(3000):
        director.update(0)
    assert director.zone == 'arena'
    assert director.obstacle_kinds() == [] and director.enemy_kinds() == []


def test_reef_colours_move_towards_the_new_area(display):
    director = ch.ChannelDirector(random.Random(2))
    director.prefill()
    director.set_area(AREAS[2])
    for _ in range(60):
        chunk = director._next_chunk(0)
    assert chunk.colors[1][0] == pytest.approx(AREAS[2]['reef'][0], abs=10)  # Rounding stops it just short


def test_wreck_passages_are_wide_enough_for_the_shark(display):
    from player_enhanced import SharkWithSprites
    shark_w = max(r.width for f in SharkWithSprites(0, 0).frames for r in pygame.mask.from_surface(f).get_bounding_rects())
    assert PASSAGE[1] - PASSAGE[0] >= shark_w * 2
    assert MIN_GAP >= shark_w * 2


def test_wreck_way_through_is_clear_from_end_to_end(display):
    wreck = GiantWreck(400)
    for y in range(H):
        for x in range(PASSAGE[0] + 1, PASSAGE[1] - 1):
            assert not wreck.mask.get_at((x, y))
    assert wreck.mask.get_at((20, H // 2)) and wreck.mask.get_at((W - 20, H // 2))


def test_wreck_pushes_a_shark_to_the_nearest_open_water(display):
    wreck = GiantWreck(400)
    assert wreck.escape_x(wreck.rect.left + 10) == wreck.rect.left - SIDE_ESCAPE
    assert wreck.escape_x(wreck.rect.right - 10) == wreck.rect.right + SIDE_ESCAPE
    assert wreck.escape_x(wreck.rect.left + 90) == wreck.passage_x()


def test_graveyard_finds_room_for_wrecks_with_water_either_side(display):
    director = ch.ChannelDirector(random.Random(5))
    director.prefill()
    director.set_area(AREAS[1])
    placed = 0
    for _ in range(40000):
        director.update(100)
        x = director.wreck_spot(W, H)
        if x is not None:
            placed += 1
            window = director.recent + director.generator.peek(H // ch.SAMPLE_SPACING, 100)
            assert max(s[0] for s in window) < x - W // 2 - MIN_GAP + 3
            assert min(s[1] for s in window) > x + W // 2 + MIN_GAP - 3
            director.block_for_wreck(x - W // 2, x + W // 2, H)
    assert placed > 20


def test_other_areas_get_no_giant_wrecks(display):
    director = ch.ChannelDirector(random.Random(5))
    director.prefill()
    for area in (AREAS[0], AREAS[2]):
        director.set_area(area)
        assert director.wreck_spot(W, H) is None


def test_spawns_keep_beside_the_wreck_while_it_comes_in(display):
    director = ch.ChannelDirector(random.Random(5))
    director.prefill()
    director.set_area(AREAS[1])
    for _ in range(6000):
        director.update(100)
        x = director.wreck_spot(W, H)
        if x is not None:
            break
    left, right = x - W // 2, x + W // 2
    director.block_for_wreck(left, right, H)
    for _ in range(100):
        spot = director.spawn_x(30)
        assert spot + 15 <= left or spot - 15 >= right
        assert director.spawn_x(120, blocking=True) is None


def test_beating_a_boss_moves_on_to_the_next_area(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['score'] = BOSS_ROSTER[0][1]
        if state['boss']:
            state['boss'].take_damage(9999)
        if state['boss_phase'] == 'beaten':
            seen['area'] = state['channel'].area
            seen['tint'] = state['graphics_enhancer'].area_tint
            seen['next'] = state['banner_next']
            return True

    play(script, max_frames=6000)
    assert seen['area'] is AREAS[1]
    assert seen['tint'] is not None
    assert AREAS[1]['name'] in seen['next']


def test_restart_goes_back_to_the_reef(play):
    from conftest import press
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['channel'].set_area(AREAS[2])
            state['graphics_enhancer'].set_area_tint(AREAS[2]['tint'])
            state['energy'] = 0
        if frame == 100:
            press(pygame.K_a)
        if frame == 103:
            seen['area'] = state['channel'].area
            seen['tint'] = state['graphics_enhancer'].area_tint
            return True

    play(script)
    assert seen['area'] is AREAS[0] and seen['tint'] is None


def test_a_graveyard_run_keeps_things_out_of_the_hull_and_loot_inside_reachable(play):
    seen = {'wrecks': 0, 'in_hull': 0, 'tracked': set()}

    def script(state, frame):
        state['energy'] = 100
        if frame == 1:
            state['next_boss'] = 1
            state['channel'].set_area(AREAS[1])
        state['score'] = 0  # Stays in the Graveyard
        for wreck in [b for b in state['banks'] if isinstance(b, GiantWreck)]:
            if wreck not in seen['tracked']:
                seen['tracked'].add(wreck)
                seen['wrecks'] += 1
            for group in ('obstacles', 'powerups', 'foods'):
                for sprite in state[group]:
                    if getattr(sprite, 'shark_rect', None) is None and pygame.sprite.collide_mask(wreck, sprite):
                        seen['in_hull'] += 1
        return frame >= 4000 and seen['wrecks'] >= 2

    assert play(script, quiet=False, max_frames=40000) == 'stopped'
    assert seen['wrecks'] >= 2
    assert seen['in_hull'] == 0


def test_shark_in_the_hull_is_pushed_out_to_the_passage(play):
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        shark = state['shark']
        if frame == 1:
            wreck = GiantWreck(shark.rect.centerx + 145 - 90)
            wreck.rect.centery = shark.rect.centery
            state['banks'].add(wreck)
            seen['wreck'] = wreck
            seen['aim'] = wreck.escape_x(shark.rect.centerx)
        seen['touching'] = bool(pygame.sprite.collide_mask(shark, seen['wreck']))
        seen['x'] = shark.rect.centerx
        return frame >= 45

    play(script)
    assert not seen['touching']


def test_jumping_to_a_boss_starts_in_its_area(play, monkeypatch):
    import conftest
    real_press = conftest.press
    monkeypatch.setattr(conftest, 'press', lambda key: real_press(pygame.K_3 if key == pygame.K_a else key))
    seen = {}

    def script(state, frame):
        seen['area'] = state['channel'].area
        return True

    play(script)
    assert seen['area'] is AREAS[2]
