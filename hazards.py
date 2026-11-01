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
