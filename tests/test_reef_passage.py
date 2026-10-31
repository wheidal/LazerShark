import random
import sys

import pygame
import pytest

from projectile import Laser, Missile, Torpedo
import reef_passage as rp

needs_live_locals = pytest.mark.skipif(sys.version_info < (3, 13), reason='writes to frame locals')
SHARK_TOP_Y = 493  # Lowest position: the shark stays at the bottom of its range


def route_exists(samples, start_x, shark_w=rp.SHARK_BODY_W):
    """Search every position the shark's body could reach through the channel."""
    reachable = {start_x}
    half = shark_w / 2
    body_samples = rp.SHARK_BODY_H // rp.SAMPLE_SPACING + 1
    total = len(samples) * rp.SAMPLE_SPACING + 800
    scroll = 0
    while scroll < total:
        scroll += rp.SCROLL_PER_STEP
        # Sample i has scrolled down to screen y = scroll - i * spacing
        nearest = (scroll - (SHARK_TOP_Y + rp.SHARK_BODY_H)) // rp.SAMPLE_SPACING
        level = [samples[i] for i in range(nearest, nearest + body_samples) if 0 <= i < len(samples)]
        low = max((left for left, _ in level), default=-10 ** 6)
        high = min((right for _, right in level), default=10 ** 6)
        reachable = {x for x in {max(0, min(800, c + d)) for c in reachable
                                 for d in (-rp.SHARK_SPEED, 0, rp.SHARK_SPEED)}
                     if x - half > low and x + half < high}
        if not reachable:
            return False
    return True


@pytest.mark.parametrize('score', [0, 60, 200])
@pytest.mark.parametrize('start_x', [25, 400, 775])
def test_every_generated_channel_has_a_route(score, start_x):
    for seed in range(40):
        assert route_exists(rp.generate_channel(random.Random(seed), score), start_x), seed


def test_route_check_catches_an_impossible_channel():
    closed = [(0, 800)] * 50 + [(500, 300)] * 50 + [(0, 800)] * 50
    assert not route_exists(closed, 400)


def test_channel_stays_wide_enough_and_narrows_with_score():
    for score, narrowest in [(0, rp.WIDEST_CHANNEL), (500, rp.NARROWEST_CHANNEL)]:
        for seed in range(30):
            samples = rp.generate_channel(random.Random(seed), score)
            assert min(r - l for l, r in samples) >= narrowest - 2 * rp.COAST_ROUGHNESS - 2


def test_banks_start_and_end_off_screen():
    for seed in range(30):
        samples = rp.generate_channel(random.Random(seed), 0)
        for left, right in (samples[0], samples[-1]):
            assert left <= 0 and right >= 800


def test_channel_really_winds():
    samples = rp.generate_channel(random.Random(3), 0)
    start = rp.FUNNEL_LENGTH // rp.SAMPLE_SPACING
    centers = [(l + r) / 2 for l, r in samples[start:-start]]
    assert max(centers) - min(centers) > 150


def all_chunks(seed, score=0):
    director = rp.ReefPassageDirector(random.Random(seed))
    director.start(score)
    chunks = []
    while director.active:
        chunk = director.update(0, score)
        if chunk:
            chunks.append(chunk)
    return director, chunks


def test_chunks_join_without_gaps_and_end_cleanly():
    director, chunks = all_chunks(5)
    for earlier, later in zip(chunks, chunks[1:]):
        assert earlier.samples[-1] == later.samples[0]
    assert director.wait_ms == rp.PASSAGE_INTERVAL_MS


def test_clear_bonus_waits_for_the_shark_and_pays_once():
    director, _ = all_chunks(5)
    assert director.take_clear_bonus() == 0
    for _ in range(rp.BONUS_AFTER_END // rp.SCROLL_PER_STEP + 1):
        director.update(0, 0)
    assert director.take_clear_bonus() == rp.CLEAR_BONUS
    assert director.take_clear_bonus() == 0


def test_fish_appear_inside_the_channel(display):
    _, chunks = all_chunks(2)
    fish = [c for c in chunks if c.has_fish]
    assert len(fish) >= 3
    for chunk in fish:
        left, right = chunk.samples[len(chunk.samples) // 2]
        assert left < chunk.channel_center < right


def test_bank_collision_shape_matches_the_coastline(display):
    samples = [(200, 600)] * 7
    left, right = rp.ChannelChunk(samples).build()[0]
    assert left.rect.right == 200 and right.rect.left == 600
    assert left.mask.get_at((190, 24)) and right.mask.get_at((10, 24))


def test_submarines_stop_before_a_passage():
    director = rp.ReefPassageDirector(random.Random(1))
    assert director.subs_allowed
    director.wait_ms = rp.SUB_CLEAR_MS - 1
    assert not director.subs_allowed and not director.active


def add_banks(state, y, samples):
    banks, _ = rp.ChannelChunk(samples).build()
    for bank in banks:
        bank.rect.y = y
    state['banks'].add(banks)
    state['all_sprites'].add(banks)
    return banks


@needs_live_locals
def test_hitting_a_bank_costs_energy_once_and_never_traps_shark(play):
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['passage'].wait_ms = 10 ** 9
            state['shark'].rect.centerx = 60
            top = state['shark'].rect.top
            for y in range(top - 96, top + 100, rp.CHUNK_H):
                add_banks(state, y, [(250, 500)] * 7)
        if frame == 100:
            seen['energy'] = state['energy']
            seen['center'] = state['shark'].rect.centerx
            seen['over'] = state['game_over']
            seen['touching'] = bool(pygame.sprite.spritecollideany(
                state['shark'], state['banks'], pygame.sprite.collide_mask))
            return True

    play(script)
    assert not seen['over'] and not seen['touching']
    assert seen['center'] > 250
    assert 100 - rp.BANK_DAMAGE - 5 < seen['energy'] < 100 - rp.BANK_DAMAGE + 1


@needs_live_locals
@pytest.mark.parametrize('weapon', [Laser, Missile, Torpedo])
def test_coastline_survives_and_stops_every_weapon(play, weapon):
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['passage'].wait_ms = 10 ** 9
            seen['banks'] = add_banks(state, 200, [(250, 500)] * 7)
            seen['shot'] = weapon(100, 300)
            state['projectiles'].add(seen['shot'])
            state['all_sprites'].add(seen['shot'])
        return frame >= 20

    play(script)
    assert all(bank.alive() for bank in seen['banks'])
    assert not seen['shot'].alive()


@needs_live_locals
def test_shots_pass_through_open_channel(play):
    seen = {}

    def script(state, frame):
        if frame == 1:
            state['passage'].wait_ms = 10 ** 9
            add_banks(state, 200, [(250, 500)] * 7)
            seen['shot'] = Laser(400, 300)
            state['projectiles'].add(seen['shot'])
            state['all_sprites'].add(seen['shot'])
        if frame == 10:
            seen['alive'] = seen['shot'].alive()
            return True

    play(script)
    assert seen['alive']


@needs_live_locals
@pytest.mark.parametrize('seed', range(5))
def test_steering_bot_clears_a_real_passage_unharmed(play, monkeypatch, seed):
    held = {}

    class Keys:
        def __getitem__(self, key):
            return held.get(key, False)

    monkeypatch.setattr(pygame.key, 'get_pressed', lambda: Keys())
    seen = {'hit': False, 'bonus': False}

    def script(state, frame):
        if frame == 1:
            state['passage'] = rp.ReefPassageDirector(random.Random(seed))
            state['passage'].start()
        shark = state['shark']
        level = [b for b in state['banks'] if b.rect.top <= shark.rect.centery <= b.rect.bottom]
        target = level[0].channel_center if level else 400
        held[pygame.K_LEFT] = target < shark.rect.centerx - 5
        held[pygame.K_RIGHT] = target > shark.rect.centerx + 5
        seen['hit'] = seen['hit'] or state['bank_invuln'] > 0
        seen['bonus'] = seen['bonus'] or state['score'] >= rp.CLEAR_BONUS
        seen['over'] = state['game_over']
        seen['done'] = frame > 5 and not state['passage'].active and not state['banks']
        return seen['done'] and seen['bonus']

    play(script, max_frames=2500)
    assert seen['done'] and seen['bonus'] and not seen['over']
    assert not seen['hit']
