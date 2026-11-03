"""
Hazards that wear the shark down instead of hitting it: radiation clouds and whirlpools.
These slow drains go straight through a shield and don't cost a weapon level.
"""
import math

import pygame

CLOUD_RADIUS = 78
SMALL_CLOUD_RADIUS = 44
CLOUD_DRAIN = 0.3  # Energy per step, about 18 a second
CLOUD_GROW_STEPS = 50
SMALL_CLOUD_STEPS = 200
CLOUD_SIZES = 8
WHIRLPOOL_RADIUS = 112
WHIRLPOOL_CORE = 30
WHIRLPOOL_PULL = 3.3  # px per step at the core. Slower than the shark, so it can always swim out
WHIRLPOOL_DRAIN = 0.5
WHIRLPOOL_FRAMES = 12
WHIRLPOOL_SPAWN_MS = {'easy': 16000, 'normal': 12000, 'hard': 8000}
_art = {}


def _cloud_art(radius):
    if radius not in _art:
        size = radius * 2
        image = pygame.Surface((size, size), pygame.SRCALPHA)
        for r, alpha in ((radius, 45), (int(radius * 0.8), 45), (int(radius * 0.55), 50)):
            layer = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(layer, (120, 255, 70, alpha), (radius, radius), r)
            image.blit(layer, (0, 0))
        pygame.draw.circle(image, (190, 255, 120, 110), (radius, radius), radius, 2)
        for i in range(10):  # Motes of something unpleasant
            angle = i * 2.4
            reach = radius * (0.2 + (i % 5) * 0.14)
            pygame.draw.circle(image, (225, 255, 150, 190), (radius + math.cos(angle) * reach,
                                                             radius + math.sin(angle) * reach), 2)
        _art[radius] = image
    return _art[radius]


class RadiationCloud(pygame.sprite.Sprite):
    """Spreads from where it starts and scrolls away with the coast."""

    def __init__(self, center, radius=CLOUD_RADIUS, lifetime=None):
        super().__init__()
        self.full_radius = radius
        self.lifetime = lifetime
        self.age = 0
        self.radius = radius // CLOUD_SIZES
        self.image = _cloud_art(self.radius)
        self.rect = self.image.get_rect(center=center)

    def update(self):
        self.age += 1
        grown = min(1, self.age / CLOUD_GROW_STEPS)
        step = max(1, math.ceil(grown * CLOUD_SIZES))
        radius = self.full_radius * step // CLOUD_SIZES
        if radius != self.radius:
            self.radius = radius
            self.image = _cloud_art(radius)
            self.rect = self.image.get_rect(center=self.rect.center)
        if self.lifetime and self.age >= self.lifetime:
            self.kill()

    def drain_on(self, shark_rect):
        distance = pygame.math.Vector2(self.rect.center).distance_to(shark_rect.center)
        return CLOUD_DRAIN if distance < self.radius + 20 else 0

    def pull_on(self, shark_rect):
        return (0, 0)


def _whirlpool_art():
    if 'whirlpool' not in _art:
        size = WHIRLPOOL_RADIUS * 2
        center = WHIRLPOOL_RADIUS
        base = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(base, (10, 30, 70, 90), (center, center), WHIRLPOOL_RADIUS)
        pygame.draw.circle(base, (6, 14, 40, 170), (center, center), WHIRLPOOL_CORE)
        for arm in range(4):
            points = []
            for i in range(30):
                t = i / 29
                angle = arm * math.pi / 2 + t * 4.2
                reach = WHIRLPOOL_CORE * 0.5 + t * (WHIRLPOOL_RADIUS - 8 - WHIRLPOOL_CORE * 0.5)
                points.append((center + math.cos(angle) * reach, center + math.sin(angle) * reach))
            pygame.draw.lines(base, (150, 215, 240, 170), False, points, 3)
        _art['whirlpool'] = [pygame.transform.rotate(base, i * 360 / WHIRLPOOL_FRAMES / 4)
                             for i in range(WHIRLPOOL_FRAMES)]
    return _art['whirlpool']


class Whirlpool(pygame.sprite.Sprite):
    """Drags the shark towards its core, which hurts."""
    WIDTH = HEIGHT = WHIRLPOOL_RADIUS * 2

    def __init__(self, x, y):
        super().__init__()
        self.frames = _whirlpool_art()
        self.image = self.frames[0]
        self.rect = self.image.get_rect(midtop=(x, y))
        self.age = 0

    def update(self):
        self.age += 1
        # Turning a quarter at a time and then looping looks the same, as the arms repeat
        self.image = self.frames[self.age // 2 % WHIRLPOOL_FRAMES]
        self.rect = self.image.get_rect(center=self.rect.center)

    def drain_on(self, shark_rect):
        distance = pygame.math.Vector2(self.rect.center).distance_to(shark_rect.center)
        return WHIRLPOOL_DRAIN if distance < WHIRLPOOL_CORE + 25 else 0

    def pull_on(self, shark_rect):
        offset = pygame.math.Vector2(self.rect.center) - shark_rect.center
        distance = offset.length()
        if not 1 < distance < WHIRLPOOL_RADIUS:
            return (0, 0)
        strength = WHIRLPOOL_PULL * (1 - distance / WHIRLPOOL_RADIUS) ** 0.5
        offset = offset.normalize() * strength
        return (offset.x, offset.y)


FIELD_SPAWN_MS = 11000
SLOW_STEPS_MS = 400


def _soft_blob(color, radius, rings=4):
    image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for i in range(rings):
        layer = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(layer, color, (radius, radius), int(radius * (1 - i / rings)))
        image.blit(layer, (0, 0))
    return image


class _Field(pygame.sprite.Sprite):
    """A patch of water that scrolls with the coast and does something while you're in it."""
    RADIUS = 100
    WIDTH = HEIGHT = 200
    drain = 0
    slows = False
    covers = False  # Drawn over the shark and everything else

    def __init__(self, x, y):
        super().__init__()
        self.image = self._make()
        self.rect = self.image.get_rect(midtop=(x, y))

    def _inside(self, shark_rect):
        return pygame.math.Vector2(self.rect.center).distance_to(shark_rect.center) < self.RADIUS + 15

    def drain_on(self, shark_rect):
        return self.drain if self._inside(shark_rect) else 0

    def slows_shark(self, shark_rect):
        return self.slows and self._inside(shark_rect)

    def pull_on(self, shark_rect):
        return (0, 0)


class InkCloud(_Field):
    """Harmless, but you can't see what's in it."""
    RADIUS = 110
    WIDTH = HEIGHT = 220
    covers = True

    def _make(self):
        return _cached_blob('ink', lambda: _soft_blob((8, 8, 18, 95), self.RADIUS, 5))


class ToxicSludge(_Field):
    """A slow purple slick that drains energy and bogs the shark down."""
    RADIUS = 95
    WIDTH = HEIGHT = 190
    drain = 0.12
    slows = True

    def _make(self):
        def make():
            image = _soft_blob((120, 40, 150, 55), self.RADIUS)
            pygame.draw.circle(image, (190, 90, 220, 170), (self.RADIUS, self.RADIUS), self.RADIUS, 2)
            for i in range(9):
                angle = i * 2.3
                reach = self.RADIUS * (0.2 + (i % 4) * 0.2)
                pygame.draw.circle(image, (210, 140, 235, 200), (self.RADIUS + math.cos(angle) * reach,
                                                                 self.RADIUS + math.sin(angle) * reach), 3)
            return image
        return _cached_blob('sludge', make)


class MagneticField(_Field):
    """Old machinery on the seabed that tugs the shark's metal parts sideways towards it."""
    RADIUS = 150
    WIDTH = HEIGHT = 300
    PULL = 2.2

    def _make(self):
        def make():
            image = pygame.Surface((self.RADIUS * 2, self.RADIUS * 2), pygame.SRCALPHA)
            center = self.RADIUS
            for radius in (self.RADIUS - 2, self.RADIUS - 44, self.RADIUS - 88):
                pygame.draw.circle(image, (110, 200, 255, 70), (center, center), radius, 2)
            pygame.draw.rect(image, (72, 80, 92), (center - 22, center - 22, 44, 44), border_radius=6)
            pygame.draw.rect(image, (230, 60, 50), (center - 18, center - 18, 18, 36))
            pygame.draw.rect(image, (70, 110, 230), (center, center - 18, 18, 36))
            return image
        return _cached_blob('magnet', make)

    def pull_on(self, shark_rect):
        if not self._inside(shark_rect):
            return (0, 0)
        gap = self.rect.centerx - shark_rect.centerx
        return (max(-self.PULL, min(self.PULL, gap * 0.05)), 0)


def _cached_blob(key, make):
    if key not in _art:
        _art[key] = make()
    return _art[key]


FIELD_TYPES = {'ink': InkCloud, 'sludge': ToxicSludge, 'magnet': MagneticField}
