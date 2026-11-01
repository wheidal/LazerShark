import pygame

from player_enhanced import SharkWithSprites
from shark_look import MAX_LEAN, RIPPLE_MS, SHARD_MS, SHIELD_FULL, SHIELD_LOW, SHIELD_MID, SharkLook, shield_color


def test_drawing_never_changes_the_collision_shape(display):
    shark = SharkWithSprites(400, 300)
    before = pygame.mask.from_surface(shark.image).count()
    rect = shark.rect.copy()
    look = SharkLook()
    look.hit()
    for x in range(0, 100, 5):
        shark.rect.centerx = 300 + x
        look.draw_shark(display, shark, 'fan')
    assert pygame.mask.from_surface(shark.image).count() == before
    assert shark.rect.size == rect.size


def test_stray_laser_mount_dot_is_gone(display):
    shark = SharkWithSprites(400, 300)
    w, h = shark.image.get_size()
    reds = [(x, y) for x in range(w) for y in range(h)
            if shark.image.get_at((x, y)).a > 100 and shark.image.get_at((x, y)).r > 180
            and shark.image.get_at((x, y)).g < 110]
    assert not reds


def test_shark_leans_into_turns_and_back(display):
    shark = SharkWithSprites(400, 300)
    look = SharkLook()
    look.draw_shark(display, shark)
    for _ in range(30):
        shark.rect.x += 5
        look.draw_shark(display, shark)
    assert -MAX_LEAN <= look.lean < -5  # Rotating clockwise is a negative angle
    for _ in range(40):
        look.draw_shark(display, shark)
    assert abs(look.lean) < 1


def test_weapon_colour_shows_on_the_shark(display):
    shark = SharkWithSprites(400, 300)
    look = SharkLook()
    frames = {look._frame(shark.image, kind) for kind in ('laser', 'fan', 'chum', 'rapid', 'beam')}
    assert len(frames) == 5


def test_hit_flash_ends(display):
    shark = SharkWithSprites(400, 300)
    look = SharkLook()
    look.hit()
    assert look.hit_left > 0
    for _ in range(40):
        look.draw_shark(display, shark, dt=16)
    assert look.hit_left == 0


def test_shield_colour_follows_strength():
    assert shield_color(100) == SHIELD_FULL
    assert shield_color(50) == SHIELD_MID
    assert shield_color(10) == SHIELD_LOW


def test_shield_covers_the_whole_shark_in_every_direction(display):
    display.fill((0, 0, 0))
    SharkLook().draw_shield(display, (400, 300), 100, 0)
    for point in ((400, 234), (400, 366), (334, 300), (466, 300)):
        assert sum(display.get_at(point)[:3]) > 0


def test_low_shield_flickers(display):
    look = SharkLook()
    seen = set()
    for now in (0, 70):
        display.fill((0, 0, 0))
        look.draw_shield(display, (400, 300), 10, now)
        seen.add(sum(display.get_at((400, 234))[:3]) > 0)
    assert seen == {True, False}


def test_ripples_and_shards_fade_away(display):
    look = SharkLook()
    look.shield_hit((400, 300), (400, 100))
    look.shield_hit((400, 300))
    assert len(look.ripples) == 2
    look.draw_shield(display, (400, 300), 80, 0, dt=RIPPLE_MS + 1)
    assert not look.ripples
    look.shield_break((400, 300))
    assert look.shards
    look.draw_shield(display, (400, 300), 0, 0, dt=SHARD_MS + 1)
    assert not look.shards


def test_shield_blows_and_breaks_show_in_the_real_game(play):
    from obstacle import CoralReef
    seen = {}

    def script(state, frame):
        state['energy'] = 100
        shark = state['shark']
        if frame == 1:
            state['shield_active'], state['shield_strength'] = True, 100
            state['obstacles'].add(CoralReef(shark.rect.centerx, shark.rect.centery - 30))
        if frame == 3:
            seen['rippled'] = len(state['shark_look'].ripples)
            state['shield_strength'] = 10
            state['obstacles'].add(CoralReef(shark.rect.centerx, shark.rect.centery - 30))
        if frame == 5:
            seen['shards'] = len(state['shark_look'].shards)
            seen['active'] = state['shield_active']
        return frame >= 5

    play(script)
    assert seen['rippled'] == 1
    assert seen['shards'] > 0 and not seen['active']


def test_energy_hit_flashes_the_shark_in_the_real_game(play):
    from obstacle import CoralReef
    seen = {}

    def script(state, frame):
        shark = state['shark']
        if frame == 1:
            state['obstacles'].add(CoralReef(shark.rect.centerx, shark.rect.centery - 30))
        if frame == 3:
            seen['flash'] = state['shark_look'].hit_left
        return frame >= 3

    play(script)
    assert seen['flash'] > 0
