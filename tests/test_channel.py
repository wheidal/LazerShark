import random
import sys

import pygame
import pytest

import channel as ch
from food import SmallFish
from projectile import Laser, Missile, Torpedo

needs_live_locals = pytest.mark.skipif(sys.version_info < (3, 13), reason='writes to frame locals')
SHARK_TOP_Y = 493  # Lowest position: the shark stays at the bottom of its range
LONG_RUN = 1500  # Samples, or about 67 seconds of play


def route_exists(samples, start_x):
    """Search every position the shark's body could reach through the channel."""
    reachable = {start_x}
    half = ch.SHARK_BODY_W / 2
    body_samples = ch.SHARK_BODY_H // ch.SAMPLE_SPACING + 1
    scroll = 0
    while scroll < len(samples) * ch.SAMPLE_SPACING + 800:
        scroll += ch.SCROLL_PER_STEP
        # Sample i has scrolled down to screen y = scroll - i * spacing
        nearest = (scroll - (SHARK_TOP_Y + ch.SHARK_BODY_H)) // ch.SAMPLE_SPACING
        level = [samples[i] for i in range(nearest, nearest + body_samples) if 0 <= i < len(samples)]
        low = max((s[0] for s in level), default=-10 ** 6)
        high = min((s[1] for s in level), default=10 ** 6)
        reachable = {x for x in {max(0, min(800, c + d)) for c in reachable
                                 for d in (-ch.SHARK_SPEED, 0, ch.SHARK_SPEED)}
                     if x - half > low and x + half < high}
        if not reachable:
            return False
    return True


def samples_for(seed, score, count=LONG_RUN):
    return ch.ChannelGenerator(random.Random(seed)).take(count, score)


@pytest.mark.parametrize('score', [0, 60, 500])
def test_every_generated_channel_has_a_route(score):
    for seed in range(25):
        assert route_exists(samples_for(seed, score), 400), seed


def test_route_check_catches_an_impossible_channel():
    closed = [(0, 800, 'pass')] * 50 + [(500, 300, 'pass')] * 50 + [(0, 800, 'pass')] * 50
    assert not route_exists(closed, 400)


def test_visited_zones_keep_their_promised_widths():
    seen = set()
    for seed in range(20):
        for left, right, zone in samples_for(seed, 500, 3000):
            seen.add(zone)
            assert min(800, right) - max(0, left) >= ch.NARROWEST_PASS - 2 * ch.COAST_ROUGHNESS - 2
    assert seen == set(ch.ZONES)


def test_passes_narrow_with_score_but_never_too_far():
    def narrowest(score):
        return min(r - l for seed in range(10) for l, r, z in samples_for(seed, score, 3000) if z == 'pass')

    assert narrowest(0) > narrowest(500) >= ch.NARROWEST_PASS - 2 * ch.COAST_ROUGHNESS - 2


def test_channel_really_winds():
    centers = [(l + r) / 2 for l, r, _ in samples_for(3, 0, 3000)]
    assert max(centers) - min(centers) > 250


def test_chunks_join_without_gaps():
    director = ch.ChannelDirector(random.Random(5))
    chunks = [chunk for chunk, _ in director.prefill()]
    chunks += [director._next_chunk(0) for _ in range(40)]
    for earlier, later in zip(chunks, chunks[1:]):
        assert earlier.samples[-1] == later.samples[0]


def test_bank_collision_shape_matches_the_coastline(display):
    left, right = ch.ChannelChunk([(200, 600, 'pass')] * 7).build()
    assert left.rect.right == 200 + ch.ART_OVERHANG and right.rect.left == 600 - ch.ART_OVERHANG
    assert left.mask.get_at((190, 24)) and right.mask.get_at((10, 24))


def test_spawns_stay_in_channel_and_blockers_leave_room():
    director = ch.ChannelDirector(random.Random(1))
    director.prefill()
    blocked = placed = 0
    for _ in range(60000):
        director.update(500)
        window = director.recent + director.generator.peek(ch.SPAWN_SAMPLES_ABOVE, 500)
        left = max(0, max(s[0] for s in window))
        right = min(800, min(s[1] for s in window))
        fallback = (director.last_sample[0] + director.last_sample[1]) // 2
        assert left < director.spawn_x(26) < right or director.spawn_x(26) == fallback
        x = director.spawn_x(90, blocking=True)
        if x is None:
            blocked += 1
            continue
        placed += 1
        assert x - 45 > left and x + 45 < right
        assert max(x - 45 - left, right - x - 45) >= ch.OBSTACLE_PASS_ROOM
    assert blocked and placed


def add_banks(state, y, samples):
    banks = ch.ChannelChunk(samples).build(y)
    state['banks'].add(banks)
    state['all_sprites'].add(banks)
    return banks


def freeze_coast(state):
    """Replace the channel with an empty one so a test controls every bank."""
    state['banks'].empty()
    state['channel'].update = lambda score: None


@needs_live_locals
def test_spawned_sprites_never_touch_the_coast(play):
    seen = {'touches': 0, 'spawned': set()}

    def script(state, frame):
        for group in ('obstacles', 'foods', 'powerups', 'subs'):
            for sprite in state[group]:
                seen['spawned'].add(sprite)
                if pygame.sprite.spritecollideany(sprite, state['banks'], pygame.sprite.collide_mask):
                    seen['touches'] += 1
        state['energy'] = 100
        return frame >= 3000

    play(script, quiet=False, max_frames=3000)
    assert len(seen['spawned']) > 30
    assert seen['touches'] == 0


@needs_live_locals
def test_screen_starts_covered_by_coastline_with_no_seams(play):
    seen = {}

    def script(state, frame):
        if frame == 1:
            seen['start'] = sorted({bank.rect.y for bank in state['banks']})
        if frame == 40:
            seen['later'] = sorted({bank.rect.y for bank in state['banks']})
            seen['hit'] = state['bank_invuln'] > 0
            return True

    play(script)
    for tops in (seen['start'], seen['later']):
        assert tops[0] <= 0 and tops[-1] + ch.CHUNK_H >= 600
        assert all(b - a == ch.CHUNK_H for a, b in zip(tops, tops[1:]))
    assert not seen['hit']


@needs_live_locals
def test_restart_gets_a_fresh_covered_screen(play):
    seen = {}

    def script(state, frame):
        if frame == 1:
            seen['channel'] = state['channel']
            state['energy'] = 0
        if frame == 100:
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, mod=0, unicode='', scancode=0))
        if frame == 103:
            seen['new'] = state['channel'] is not seen['channel']
            seen['banks'] = len(state['banks'])
            seen['over'] = state['game_over']
            return True

    play(script)
    assert seen['new'] and seen['banks'] and not seen['over']


@needs_live_locals
def test_hitting_a_bank_costs_energy_once_and_never_traps_shark(play):
    seen = {}

    def script(state, frame):
        if frame == 1:
            freeze_coast(state)
            state['shark'].rect.centerx = 60
            top = state['shark'].rect.top
            for y in range(top - 96, top + 100, ch.CHUNK_H):
                add_banks(state, y, [(250, 500, 'pass')] * 7)
        if frame == 100:
            seen['energy'] = state['energy']
            seen['center'] = state['shark'].rect.centerx
            seen['touching'] = bool(pygame.sprite.spritecollideany(
                state['shark'], state['banks'], pygame.sprite.collide_mask))
            return True

    play(script)
    assert not seen['touching']
    assert seen['center'] > 250
    assert 100 - ch.BANK_DAMAGE - 5 < seen['energy'] < 100 - ch.BANK_DAMAGE + 1


@needs_live_locals
@pytest.mark.parametrize('weapon', [Laser, Missile, Torpedo])
def test_coastline_survives_and_stops_every_weapon(play, weapon):
    seen = {}

    def script(state, frame):
        if frame == 1:
            freeze_coast(state)
            seen['banks'] = add_banks(state, 200, [(250, 500, 'pass')] * 7)
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
            freeze_coast(state)
            add_banks(state, 200, [(250, 500, 'pass')] * 7)
            seen['shot'] = Laser(400, 300)
            state['projectiles'].add(seen['shot'])
            state['all_sprites'].add(seen['shot'])
        if frame == 10:
            seen['alive'] = seen['shot'].alive()
            return True

    play(script)
    assert seen['alive']


@needs_live_locals
@pytest.mark.parametrize('seed', range(4))
def test_steering_bot_follows_every_zone_unharmed(play, monkeypatch, seed):
    held = {}

    class Keys:
        def __getitem__(self, key):
            return held.get(key, False)

    monkeypatch.setattr(pygame.key, 'get_pressed', lambda: Keys())
    seen = {'hit': False, 'zones': set()}

    def script(state, frame):
        if frame == 1:
            state['banks'].empty()
            channel = ch.ChannelDirector(random.Random(seed))
            state['channel'] = channel
            for chunk, y in channel.prefill():
                banks = chunk.build(y)
                state['banks'].add(banks)
                state['all_sprites'].add(banks)
            return False
        shark = state['shark']
        level = [b for b in state['banks'] if b.rect.top <= shark.rect.centery <= b.rect.bottom]
        target = level[0].channel_center if level else shark.rect.centerx
        held[pygame.K_LEFT] = target < shark.rect.centerx - 5
        held[pygame.K_RIGHT] = target > shark.rect.centerx + 5
        seen['hit'] = seen['hit'] or state['bank_invuln'] > 0
        seen['zones'].add(state['channel'].zone)
        state['energy'] = 100
        return len(seen['zones']) == len(ch.ZONES) and frame > 1200

    play(script, max_frames=9000)
    assert seen['zones'] == set(ch.ZONES)
    assert not seen['hit']


def test_coral_art_covers_the_hit_shape_and_reaches_past_it():
    left, right = ch.ChannelChunk([(200, 600, 'pass')] * 7).build()
    for bank in (left, right):
        for y in range(ch.CHUNK_H):
            for x in range(bank.rect.width):
                if bank.mask.get_at((x, y)):
                    assert bank.image.get_at((x, y)).a == 255
    assert left.rect.right == 200 + ch.ART_OVERHANG
    assert right.rect.left == 600 - ch.ART_OVERHANG


def test_reef_rows_line_up_across_chunk_joins():
    director = ch.ChannelDirector(random.Random(3))
    lower = director._next_chunk(0)
    upper = director._next_chunk(0)
    assert upper.world_y == lower.world_y + ch.CHUNK_H
    assert upper.samples[0] == lower.samples[-1]
    assert upper.colors[0] == lower.colors[1]
