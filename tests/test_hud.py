import pygame

from hud import FADED_ALPHA, Hud, MARGIN, STATUS_SIZE

FAR_AWAY = pygame.Rect(400, 500, 45, 104)


def draw(hud, screen, shark=FAR_AWAY, energy=100, shield=0, laser=100, triple=None,
         missiles=3, torpedoes=1, score=0, now=0):
    hud.draw(screen, shark, energy, shield, laser, triple, missiles, torpedoes, score, now)


def test_panels_stay_in_the_corners_at_any_value(display):
    hud = Hud()
    for values in ({'energy': -20}, {'energy': 250, 'shield': 500, 'laser': 500},
                   {'score': 123456789012}, {'missiles': 0, 'torpedoes': 0}, {'triple': 'CHUM 3'}):
        display.fill((0, 0, 0))
        draw(hud, display, **values)
        assert display.get_at((400, 300))[:3] == (0, 0, 0)  # The play area stays untouched
    assert hud.score_panel.get_width() < 200


def test_low_energy_flashes_only_when_low(display):
    hud = Hud()
    bar_pixel = (MARGIN + 72, MARGIN + 11)
    seen = {True: set(), False: set()}
    for low, energy in ((True, 10), (False, 80)):
        for now in (0, 250):
            display.fill((0, 0, 0))
            draw(hud, display, energy=energy, now=now)
            seen[low].add(tuple(display.get_at(bar_pixel))[:3])
    assert len(seen[True]) == 2 and len(seen[False]) == 1


def test_panel_fades_when_the_shark_is_beneath_it(display):
    hud = Hud()
    draw(hud, display)
    assert hud.status.get_alpha() in (None, 255)
    draw(hud, display, shark=pygame.Rect(MARGIN + STATUS_SIZE[0] - 5, MARGIN, 45, 104))
    assert hud.status.get_alpha() == FADED_ALPHA
