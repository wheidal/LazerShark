import pygame
import pytest

from areas import AREAS
from boss import VICTORY_SCORE
from bosses import BOSS_ROSTER, DrRask
from music import AREA_TRACKS, MusicDirector, _path_for, FALLBACK
from story import AREA_TAUNTS, BEATEN_TAUNTS, BOSS_TAUNTS, BOX, Radio
from conftest import press
from projectile import Laser

LEFT, RIGHT = 75, 725
SHARK = pygame.Rect(380, 450, 45, 104)


def test_the_journey_ends_at_the_lab():
    assert [area['name'] for area in AREAS] == [
        "The Reef", "The Ship Graveyard", "The Volcanic Rift", "Atlantis", "The Sunken Lab", "The Lab Core"]
    assert [cls.__name__ for cls, _ in BOSS_ROSTER] == [
        'MorayEel', 'GiantSquid', 'LavaCrab', 'Guardian', 'RivalShark', 'DrRask']
    assert BOSS_ROSTER[-1][0].final and not any(cls.final for cls, _ in BOSS_ROSTER[:-1])


def test_every_area_and_boss_has_words_and_music():
    for area in AREAS:
        assert area['name'] in AREA_TAUNTS and area['name'] in AREA_TRACKS
        assert _path_for(AREA_TRACKS[area['name']]) != FALLBACK
    for cls, _ in BOSS_ROSTER:
        assert cls.name in BOSS_TAUNTS
    for cls, _ in BOSS_ROSTER[:-1]:
        assert cls.name in BEATEN_TAUNTS
    assert _path_for('boss') != FALLBACK and _path_for('final_boss') != FALLBACK


def test_unknown_track_falls_back_rather_than_crashing():
    assert _path_for('no_such_track') == FALLBACK


def test_music_fades_out_before_changing_track(display):
    pygame.mixer.init()
    music = MusicDirector(True, True, 0.5)
    music.play('title')
    assert music.current == 'title'
    for _ in range(100):
        music.update(16)
    assert music.fade == 1
    music.play('boss')
    assert music.current == 'title' and music.waiting == 'boss'
    music.update(100)
    assert 0 < music.fade < 1
    for _ in range(100):
        music.update(16)
    assert music.current == 'boss' and music.fade == 1


def test_music_does_nothing_without_an_audio_device(display):
    music = MusicDirector(False, False, 0.5)
    music.play('title')
    music.update(16)
    music.set_preferences(True, 1.0)


def test_radio_types_out_one_message_at_a_time_then_clears(display):
    radio = Radio()
    radio.say("First message")
    radio.say("First message")
    radio.say("Second message")
    assert len(radio.queue) == 2
    radio.update(16)
    assert radio.message == "First message"
    radio.draw(display, SHARK)
    for _ in range(600):
        radio.update(16, in_fight=True)
    assert radio.message is None and not radio.queue


@pytest.mark.parametrize('text', list(AREA_TAUNTS.values()) + list(BOSS_TAUNTS.values()) + list(BEATEN_TAUNTS.values()))
def test_every_taunt_fits_in_the_box(display, text):
    radio = Radio()
    lines = radio._wrap(text)
    assert len(lines) <= 3
    assert all(radio.font.size(line)[0] <= BOX.width - 88 for line in lines)


def test_rask_turrets_shield_him_then_the_tank_takes_damage(display):
    rask = DrRask(LEFT, RIGHT)
    rask.update(SHARK)
    assert rask.guarded
    rask.on_shot([rask.tank])
    assert rask.health == rask.max_health
    for turret in rask.turrets:
        while turret['hp'] > 0:
            rask.on_shot([turret['part']])
    assert not rask.guarded and rask.health > 0
    before = rask.health
    rask.on_shot([rask.tank])
    assert before - rask.health == 2


def test_rask_can_always_be_finished_with_lasers(display):
    rask = DrRask(LEFT, RIGHT, 'hard')
    for step in range(60000):
        rask.update(SHARK)
        target = rask.targets()[0]
        if step % 6 == 0 and target.alive():
            rask.on_shot([target])
        if rask.dead:
            return
    raise AssertionError('Dr. Rask could not be beaten')


def test_rask_gets_desperate_and_keeps_attacking(display):
    rask = DrRask(LEFT, RIGHT)
    assert not rask.desperate
    rask.take_damage(rask.max_health * 0.8)
    assert rask.desperate
    kinds = set()
    for _ in range(4000):
        rask.update(SHARK)
        kinds.update(type(h).__name__ for h in rask.hazards)
    assert {'Beam', 'LavaVent', 'Orb'} <= kinds


def test_beating_rask_plays_the_ending_and_lets_you_hunt_again(play, monkeypatch):
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['next_boss'] = len(BOSS_ROSTER) - 1
            state['score'] = BOSS_ROSTER[-1][1]
        if not seen.get('won'):
            state['energy'] = 100
        fight = state['boss']
        if fight:
            seen['score_before'] = state['score']
            fight.take_damage(99999)
        if state['won'] and 'won' not in seen:
            seen['won'] = frame
            seen['score_after'] = state['score']
        if 'won' in seen and frame == seen['won'] + 90:
            press(pygame.K_a)
        if 'won' in seen and frame == seen['won'] + 93:
            seen['after'] = (state['won'], state['game_over'], state['next_boss'], state['score'])
            return True

    play(script, max_frames=8000)
    assert seen['score_after'] == seen['score_before'] + VICTORY_SCORE
    assert seen['after'] == (False, False, 0, 0)


def test_every_ending_beat_draws_when_left_to_play_out(display):
    import cutscenes
    import random
    from player_enhanced import SharkWithSprites

    class Silent:
        def play(self):
            pass

    sounds = {name: Silent() for name in ('splat', 'beam', 'scream', 'chomp', 'burp', 'blast')}
    image = SharkWithSprites(0, 0).frames[0]
    rng = random.Random(1)
    shark = cutscenes._dressed_shark(image, 1.1)
    beats = [cutscenes._security_scene(shark, cutscenes.Gibs(rng), sounds),
             cutscenes._begging_scene(cutscenes._dressed_shark(image, 3.4), sounds),
             cutscenes._chomp_scene(cutscenes.Gibs(rng), sounds),
             cutscenes._escape_scene(shark, sounds, rng), cutscenes._credits_scene(1234),
             cutscenes._gag_scene(shark)] + cutscenes._intro_beats(shark)
    for draw, length in beats:
        elapsed = 0
        while elapsed < length:
            elapsed += 33
            draw(display, elapsed, 33)
