"""
Signature hazards of the later areas: lava geysers in the Rift and laser gates in the Lab.
They scroll with the coast, and hurt once each time they fire.
"""
import pygame

from boss import Hazard

GEYSER_WIDTH = GEYSER_HEIGHT = 124
GEYSER_REST_STEPS = 60
GEYSER_WARN_STEPS = 45
GEYSER_ERUPT_STEPS = 38
GATE_OFF_STEPS = 95
GATE_WARN_STEPS = 30
GATE_ON_STEPS = 60
GATE_HEIGHT = 18
SWITCH_INSET = 70
OFF_BOTTOM = 620
_art = {}


def _geyser_art():
    if 'geyser' not in _art:
        size = GEYSER_WIDTH
        center = size // 2
        rest = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(rest, (40, 22, 22), (center, center), 20)
        pygame.draw.circle(rest, (150, 50, 20), (center, center), 9)
        warn = rest.copy()
        pygame.draw.circle(warn, (255, 120, 30, 170), (center, center), center - 2, 4)
        pygame.draw.circle(warn, (255, 170, 60), (center, center), 13)
        erupt = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(erupt, (205, 40, 10), (center, center), center - 2)
        pygame.draw.circle(erupt, (255, 130, 20), (center, center), center - 14)
        pygame.draw.circle(erupt, (255, 235, 130), (center, center), center // 2)
        _art['geyser'] = (rest, warn, erupt, pygame.mask.from_surface(erupt))
    return _art['geyser']


class LavaGeyser(Hazard):
    """Rests, glows as a warning, then erupts, over and over as it scrolls past."""
    single_use = False
    damage = 18

    def __init__(self, x, y, start_step=0):
        super().__init__()
        self.rest, self.warn, self.erupt, self.mask = _geyser_art()
        self.image = self.rest
        self.rect = self.image.get_rect(midtop=(x, y))
        self.active = False
        self.step = start_step

    def update(self):
        self.rect.y += 3
        if self.rect.top > OFF_BOTTOM:
            self.kill()
            return
        self.step = (self.step + 1) % (GEYSER_REST_STEPS + GEYSER_WARN_STEPS + GEYSER_ERUPT_STEPS)
        if self.step < GEYSER_REST_STEPS:
            self.image = self.rest
            self.active = False
        elif self.step < GEYSER_REST_STEPS + GEYSER_WARN_STEPS:
            self.image = self.warn if self.step // 5 % 2 else self.rest
            self.active = False
        else:
            if self.image is not self.erupt:  # Each eruption can hurt once
                self.active = True
            self.image = self.erupt


def _switch_art():
    if 'switch' not in _art:
        image = pygame.Surface((34, 34), pygame.SRCALPHA)
        pygame.draw.rect(image, (14, 16, 24), (0, 0, 34, 34), border_radius=6)
        pygame.draw.rect(image, (70, 90, 104), (2, 2, 30, 30), border_radius=5)
        pygame.draw.circle(image, (110, 255, 140), (17, 17), 10)
        pygame.draw.circle(image, (235, 255, 240), (15, 15), 4)
        _art['switch'] = image
    return _art['switch']


class GateSwitch(pygame.sprite.Sprite):
    """Destroying this shuts down its gate. It lives with the obstacles, so any shot can hit it."""
    kind = 'gate_switch'
    name = "Gate Switch"
    toughness = 1
    damage = 5
    reward = 3
    counts_for_rewards = False
    blast_radius = 0
    blast_damage = 0
    drops_pickup = False
    bursts_on_coast = False
    debris_color = (120, 255, 150)

    def __init__(self, center):
        super().__init__()
        self.image = _switch_art()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=center)
        self.hits = 0


class LaserGate(Hazard):
    """A wall of laser across the channel that switches on and off."""
    single_use = False
    damage = 15

    def __init__(self, left, right, y):
        super().__init__()
        width = max(1, right - left)
        self.off = pygame.Surface((width, GATE_HEIGHT), pygame.SRCALPHA)
        for x in (0, width - 16):
            pygame.draw.rect(self.off, (70, 90, 104), (x, 0, 16, GATE_HEIGHT), border_radius=3)
        self.warn = self.off.copy()
        pygame.draw.line(self.warn, (255, 90, 90), (16, GATE_HEIGHT // 2), (width - 16, GATE_HEIGHT // 2), 1)
        self.on = self.off.copy()
        self.on.fill((255, 50, 60, 225), (16, 3, max(1, width - 32), GATE_HEIGHT - 6))
        self.on.fill((255, 235, 235), (16, GATE_HEIGHT // 2 - 2, max(1, width - 32), 4))
        self.mask = pygame.mask.from_surface(self.on)
        self.image = self.off
        self.rect = self.image.get_rect(topleft=(left, y))
        self.active = False
        self.step = 0
        self.switch = GateSwitch((left + SWITCH_INSET, y - 26))

    def update(self):
        self.rect.y += 3
        if self.rect.top > OFF_BOTTOM:
            self.kill()
            return
        if not self.switch.alive():
            self.kill()
            return
        self.step = (self.step + 1) % (GATE_OFF_STEPS + GATE_WARN_STEPS + GATE_ON_STEPS)
        if self.step < GATE_OFF_STEPS:
            self.image = self.off
            self.active = False
        elif self.step < GATE_OFF_STEPS + GATE_WARN_STEPS:
            self.image = self.warn if self.step // 4 % 2 else self.off
            self.active = False
        else:
            if self.image is not self.on:  # Each burst can hurt once
                self.active = True
            self.image = self.on
