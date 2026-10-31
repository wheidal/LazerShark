"""
The in-game display: two small corner panels, so the top of the channel stays visible.
A panel fades while the shark swims beneath it.
"""
import pygame

MARGIN = 10
LOW_ENERGY = 25  # Below this the energy bar flashes
FLASH_MS = 250
FADED_ALPHA = 80

STATUS_SIZE = (196, 66)
SCORE_SIZE = (130, 66)
PANEL_COLOR = (8, 24, 44, 170)
PANEL_EDGE = (120, 170, 200, 120)
BAR_X = 68
BAR_W = 118
BAR_H = 12
ROW_Y = (6, 25, 44)
PIP_SIZE = 12
PIP_GAP = 5
MAX_AMMO = 3

ENERGY_COLOR = (70, 210, 110)
ENERGY_LOW_COLOR = (240, 70, 60)
SHIELD_COLOR = (90, 220, 255)
LASER_COLOR = (255, 90, 90)
MISSILE_COLOR = (255, 150, 40)
TORPEDO_COLOR = (60, 240, 230)
SCORE_COLOR = (255, 225, 90)
LABEL_COLOR = (225, 235, 240)
EMPTY_COLOR = (30, 44, 62)
DIM_COLOR = (120, 135, 150)


class Hud:
    def __init__(self):
        self.small = pygame.font.SysFont(None, 20)
        self.large = pygame.font.SysFont(None, 34)
        self.labels = {text: self.small.render(text, True, LABEL_COLOR)
                       for text in ('ENERGY', 'SHIELD', 'LASER', 'MISSILE', 'TORPEDO')}
        self.dim_shield = self.small.render('SHIELD', True, DIM_COLOR)
        self.triple = self.small.render('x3', True, (255, 255, 255))
        self.status = pygame.Surface(STATUS_SIZE, pygame.SRCALPHA)
        self.score_panel = pygame.Surface(SCORE_SIZE, pygame.SRCALPHA)
        self.shown_score = None
        self.score_text = None

    def _bar(self, panel, y, value, color):
        filled = int(BAR_W * max(0, min(100, value)) / 100)
        pygame.draw.rect(panel, EMPTY_COLOR, (BAR_X, y, BAR_W, BAR_H), border_radius=3)
        if filled:
            pygame.draw.rect(panel, color, (BAR_X, y, filled, BAR_H), border_radius=3)
            pygame.draw.line(panel, (255, 255, 255, 110), (BAR_X + 2, y + 2), (BAR_X + filled - 3, y + 2))
        pygame.draw.rect(panel, PANEL_EDGE, (BAR_X, y, BAR_W, BAR_H), 1, border_radius=3)

    def _clear(self, panel):
        panel.fill((0, 0, 0, 0))
        rect = panel.get_rect()
        pygame.draw.rect(panel, PANEL_COLOR, rect, border_radius=8)
        pygame.draw.rect(panel, PANEL_EDGE, rect, 1, border_radius=8)

    def _pips(self, panel, y, count, color):
        """Ammo, filled from the left."""
        x = SCORE_SIZE[0] - 8 - MAX_AMMO * (PIP_SIZE + PIP_GAP) + PIP_GAP
        for i in range(MAX_AMMO):
            rect = (x + i * (PIP_SIZE + PIP_GAP), y, PIP_SIZE, PIP_SIZE)
            fill = color if i < count else EMPTY_COLOR
            if color == TORPEDO_COLOR:
                pygame.draw.ellipse(panel, fill, rect)
                pygame.draw.ellipse(panel, PANEL_EDGE, rect, 1)
            else:
                pygame.draw.rect(panel, fill, rect, border_radius=2)
                pygame.draw.rect(panel, PANEL_EDGE, rect, 1, border_radius=2)

    def _show(self, screen, panel, topleft, shark_rect):
        rect = panel.get_rect(topleft=topleft)
        panel.set_alpha(FADED_ALPHA if rect.colliderect(shark_rect) else None)
        screen.blit(panel, rect)

    def draw(self, screen, shark_rect, energy, shield, laser, triple_laser, missiles, torpedoes, score, now):
        """shield is 0 when no shield is up. now is the time in ms, which drives the warning flash."""
        status = self.status
        self._clear(status)
        low = energy < LOW_ENERGY
        flash_off = low and (now // FLASH_MS) % 2
        energy_color = EMPTY_COLOR if flash_off else ENERGY_LOW_COLOR if low else ENERGY_COLOR
        status.blit(self.labels['ENERGY'], (8, ROW_Y[0]))
        self._bar(status, ROW_Y[0], energy, energy_color)
        status.blit(self.labels['SHIELD'] if shield > 0 else self.dim_shield, (8, ROW_Y[1]))
        self._bar(status, ROW_Y[1], shield, SHIELD_COLOR)
        status.blit(self.labels['LASER'], (8, ROW_Y[2]))
        self._bar(status, ROW_Y[2], laser, LASER_COLOR)
        if triple_laser:
            status.blit(self.triple, (BAR_X + BAR_W - self.triple.get_width() - 3, ROW_Y[2]))
        self._show(screen, status, (MARGIN, MARGIN), shark_rect)

        if score != self.shown_score:
            self.shown_score = score
            self.score_text = self.large.render(str(score), True, SCORE_COLOR)
        panel = self.score_panel
        self._clear(panel)
        # The score shrinks to fit rather than ever spilling out of its panel
        text = self.score_text
        room = SCORE_SIZE[0] - 16
        if text.get_width() > room:
            text = pygame.transform.smoothscale(text, (room, text.get_height() * room // text.get_width()))
        panel.blit(text, (SCORE_SIZE[0] - 8 - text.get_width(), 5))
        panel.blit(self.labels['MISSILE'], (8, 31))
        self._pips(panel, 31, missiles, MISSILE_COLOR)
        panel.blit(self.labels['TORPEDO'], (8, 48))
        self._pips(panel, 48, torpedoes, TORPEDO_COLOR)
        self._show(screen, panel, (screen.get_width() - SCORE_SIZE[0] - MARGIN, MARGIN), shark_rect)
