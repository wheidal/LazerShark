import json
import sys

import pygame
import pytest

from attract import AttractMode, SCORES_SHOWN_MS, TITLE_SHOWN_MS
from conftest import press
from graphics_enhancements import GraphicsEnhancer
from highscores import HighScores, InitialsEntry, SCORES_FILE, TABLE_SIZE, draw_table

needs_live_locals = pytest.mark.skipif(sys.version_info < (3, 13), reason='writes to frame locals')
KEYMAP = {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT, 'right': pygame.K_RIGHT,
          'fire': pygame.K_SPACE}


def key(code, typed=''):
    return pygame.event.Event(pygame.KEYDOWN, key=code, unicode=typed, mod=0, scancode=0)


def test_empty_table_lets_any_score_in_but_zero():
    scores = HighScores()
    assert scores.entries == [] and scores.best == 0
    assert scores.qualifies(1)
    assert not scores.qualifies(0)


def test_table_keeps_the_best_ten_in_order_and_saves_them():
    scores = HighScores()
    for points in range(5, 125, 10):  # Twelve runs
        scores.add('abc', points, 'normal')
    assert len(scores.entries) == TABLE_SIZE
    assert [entry['score'] for entry in scores.entries] == list(range(115, 15, -10))
    assert scores.entries[0]['name'] == 'ABC'
    assert not scores.qualifies(15)
    assert scores.add('ZZZ', 15, 'normal') is None
    assert HighScores().entries == scores.entries  # Read back from the file


def test_a_tie_goes_below_the_run_already_there():
    scores = HighScores()
    scores.add('OLD', 50, 'normal')
    assert scores.add('NEW', 50, 'hard') == 1
    assert [entry['name'] for entry in scores.entries] == ['OLD', 'NEW']


def test_damaged_file_gives_empty_table_and_damaged_rows_are_skipped():
    scores = HighScores()
    with open(scores.path, 'w') as f:
        f.write('{not json')
    assert HighScores().entries == []
    with open(scores.path, 'w') as f:
        json.dump([{'name': 'AAA', 'score': 10}, {'name': 'BBB'}, 'junk', {'name': 'CCC', 'score': 'x'}], f)
    assert HighScores().entries == [{'name': 'AAA', 'score': 10, 'difficulty': 'normal'}]


def test_initials_picked_with_arrows_and_fire():
    entry = InitialsEntry(KEYMAP)
    entry.handle(key(pygame.K_DOWN))  # A wraps round to Z
    entry.handle(key(pygame.K_SPACE))
    entry.handle(key(pygame.K_UP))
    entry.handle(key(pygame.K_UP))
    entry.handle(key(pygame.K_RIGHT))
    entry.handle(key(pygame.K_LEFT))  # Back again changes nothing
    assert entry.name == 'ZCA' and entry.position == 1
    entry.handle(key(pygame.K_RETURN))
    assert not entry.done
    entry.handle(key(pygame.K_RETURN))
    assert entry.done and entry.name == 'ZCA'
    assert not entry.handle(key(pygame.K_UP))


def test_initials_can_be_typed_and_corrected():
    entry = InitialsEntry(KEYMAP)
    entry.handle(key(pygame.K_j, 'j'))
    entry.handle(key(pygame.K_x, 'x'))
    entry.handle(key(pygame.K_BACKSPACE))
    entry.handle(key(pygame.K_o, 'o'))
    entry.handle(key(pygame.K_e, 'e'))
    assert entry.done and entry.name == 'JOE'


def test_initials_with_a_controller():
    entry = InitialsEntry(KEYMAP)
    entry.handle(pygame.event.Event(pygame.JOYHATMOTION, value=(0, 1), hat=0, joy=0, instance_id=0))
    entry.handle(pygame.event.Event(pygame.JOYBUTTONDOWN, button=0, joy=0, instance_id=0))
    entry.handle(pygame.event.Event(pygame.JOYBUTTONDOWN, button=1, joy=0, instance_id=0))
    entry.handle(pygame.event.Event(pygame.JOYHATMOTION, value=(1, 0), hat=0, joy=0, instance_id=0))
    assert entry.name == 'BAA' and entry.position == 1


def test_table_and_entry_draw(display):
    scores = HighScores()
    font = pygame.font.SysFont(None, 32)
    draw_table(display, font, scores, 150)
    for points in range(TABLE_SIZE):
        scores.add('ABC', 100000 + points, 'nightmare')
    draw_table(display, font, scores, 150, highlight=3)
    InitialsEntry(KEYMAP).draw(display, font, (400, 300), 0)


def test_title_screen_takes_turns_with_the_scores(display):
    scores = HighScores()
    attract = AttractMode(display, GraphicsEnhancer(display))
    attract.draw_title(TITLE_SHOWN_MS, scores)  # No scores yet: the title stays
    scores.add('ABC', 99, 'normal')
    attract.draw_title(0, scores)
    attract.draw_title(TITLE_SHOWN_MS + SCORES_SHOWN_MS // 2, scores)


def die_with(state, points):
    state['score'] = points
    state['energy'] = 0


@needs_live_locals
def test_a_new_high_score_asks_for_initials_then_saves_them(play):
    seen = {}

    def script(state, frame):
        if frame == 1:
            die_with(state, 42)
        if frame == 3:
            seen['asked'] = state['entry'] is not None
            press(pygame.K_SPACE)  # Mashing fire while the game ends types nothing
        if frame == 5:
            seen['still_a'] = state['entry'].name == 'AAA' and state['entry'].position == 0
            state['restart_lock'] = 0
            for letter in 'sky':
                pygame.event.post(key(getattr(pygame, f'K_{letter}'), letter))
        if frame == 8:
            seen['place'] = state['score_place']
            seen['over'] = state['game_over']
            press(pygame.K_a)
        if frame == 10:
            seen['waits'] = state['game_over']  # The last letter doesn't also restart
            return True

    play(script)
    assert seen['asked'] and seen['still_a']
    assert seen['place'] == 0 and seen['over'] and seen['waits']
    assert HighScores().entries == [{'name': 'SKY', 'score': 42, 'difficulty': 'normal'}]


@needs_live_locals
def test_quitting_while_typing_still_saves_the_score(play):
    def script(state, frame):
        if frame == 1:
            die_with(state, 17)
        if frame == 3:
            state['restart_lock'] = 0
            press(pygame.K_UP)
            press(pygame.K_ESCAPE)

    assert play(script) == 'exited'
    assert HighScores().entries == [{'name': 'BAA', 'score': 17, 'difficulty': 'normal'}]


@needs_live_locals
@pytest.mark.parametrize('practice', ['practice_run', 'easy_mode'])
def test_practice_runs_are_not_recorded(play, practice):
    seen = {}

    def script(state, frame):
        if frame == 1:
            state[practice] = True
            die_with(state, 42)
        if frame == 3:
            seen['asked'] = state['entry'] is not None
            return True

    play(script)
    assert not seen['asked']
    assert HighScores().entries == []


@needs_live_locals
def test_a_score_that_misses_the_table_just_shows_it(play, tmp_path):
    with open(tmp_path / SCORES_FILE, 'w') as f:
        json.dump([{'name': 'TOP', 'score': 1000 + i, 'difficulty': 'normal'} for i in range(TABLE_SIZE)], f)
    seen = {}

    def script(state, frame):
        if frame == 1:
            die_with(state, 5)
        if frame == 3:
            seen['asked'] = state['entry'] is not None
            seen['place'] = state['score_place']
            return True

    play(script)
    assert not seen['asked'] and seen['place'] is None


@needs_live_locals
@pytest.mark.parametrize('practice', [None, 'practice_run', 'easy_mode'])
def test_the_best_score_shows_during_play(play, tmp_path, practice):
    with open(tmp_path / SCORES_FILE, 'w') as f:
        json.dump([{'name': 'TOP', 'score': 50, 'difficulty': 'normal'}], f)
    seen = {}

    def script(state, frame):
        if frame == 1 and practice:
            state[practice] = True
        if frame in (1, 3):
            state['score'] = 30 if frame == 1 else 60
        if frame in (2, 4):
            seen[frame] = state['hud'].shown_best
        return frame == 4

    play(script)
    assert seen[2] == 'BEST 50'
    # Only a run that will be saved claims a new best
    assert seen[4] == ('BEST 50' if practice else 'NEW BEST!')
