import pygame

from attract import AttractMode, BRIEFING_MS, Briefing
from graphics_enhancements import GraphicsEnhancer
from conftest import press
import main as game


def test_demo_plays_itself_for_a_long_time_and_stays_in_the_channel(display):
    attract = AttractMode(display, GraphicsEnhancer(display))
    in_bank = 0
    destroyed_or_seen = set()
    for _ in range(6000):
        attract.update(16)
        destroyed_or_seen.update(attract.obstacles)
        if pygame.sprite.spritecollideany(attract.shark, attract.banks, pygame.sprite.collide_mask):
            in_bank += 1
        assert display.get_rect().contains(attract.shark.rect)
    attract.draw_title(0)
    assert len(destroyed_or_seen) > 20
    assert in_bank < 60  # Only ever a graze on the sharpest bends


def test_briefing_finishes_by_itself(display):
    briefing = Briefing(display, {action: pygame.K_a for action in ('fire', 'missile', 'torpedo', 'pause')})
    assert not briefing.finished
    for _ in briefing.pages:
        briefing.draw(BRIEFING_MS)
    assert briefing.finished


def test_game_starts_after_title_and_briefing(play):
    assert play(lambda state, frame: frame >= 3) == 'stopped'


def test_settings_reached_from_title_then_game_starts(play):
    keys = [pygame.K_DOWN] * 6 + [pygame.K_RETURN]
    seen = {}

    def script(state, frame):
        seen['frame'] = frame
        return frame >= 3

    assert play(script, menu_keys=keys) == 'stopped'
    assert seen['frame'] == 3
