"""
The laser upgrades, in order. Each upgrade pickup moves the shark one step up the ladder, and a hit
moves it one step back. Add a weapon by adding it to WEAPONS and to its place in LADDER.
"""
import math

import pygame

from projectile import Laser

BASE = 'laser'
LADDER = [BASE, 'shotgun', 'rapid', 'fan']

# cost: laser power per shot. cooldown: seconds between shots. power: damage per bolt.
# shots and spread (degrees either side of straight up).
WEAPONS = {
    'shotgun': {'name': 'SHOTGUN', 'color': (255, 50, 40), 'size': (11, 11), 'speed': 10, 'ball': True,
                'cost': 8, 'cooldown': 0.42, 'power': 0.5, 'shots': 9, 'spread': 58},
    'rapid': {'name': 'RAPID', 'color': (255, 240, 90), 'size': (5, 16), 'speed': 15,
              'cost': 2, 'cooldown': 0.05, 'power': 0.9, 'shots': 1, 'spread': 0},
    'fan': {'name': 'FAN', 'color': (110, 240, 130), 'size': (6, 16), 'speed': 11,
            'cost': 6, 'cooldown': 0.16, 'power': 0.7, 'shots': 7, 'spread': 30},
}
BASE_COST = 3
BASE_COOLDOWN = 0.1
UPGRADE_MS = 25000  # How long a step up the ladder lasts before it drops back one
UPGRADE_SPAWN_MS = 25000  # How often a new upgrade drifts in
OBSTACLES_FOR_UPGRADE = 10
OFF_SCREEN = pygame.Rect(-40, -60, 880, 720)

_bolts = {}
_icon = {}


def _bolt_image(kind, angle):
    key = (kind, angle)
    if key not in _bolts:
        spec = WEAPONS[kind]
        w, h = spec['size']
        image = pygame.Surface((w, h), pygame.SRCALPHA)
        if spec.get('ball'):
            pygame.draw.circle(image, spec['color'], (w // 2, h // 2), w // 2)
            pygame.draw.circle(image, (255, 190, 170), (w // 2 - 1, h // 2 - 1), w // 4)
        else:
            pygame.draw.rect(image, spec['color'] + (150,), (0, 0, w, h), border_radius=w // 2)
            pygame.draw.rect(image, (255, 255, 255), (w // 3, 1, max(1, w // 3), h - 2))
            image = pygame.transform.rotate(image, -angle)
        _bolts[key] = (image, pygame.mask.from_surface(image))
    return _bolts[key]


class Bolt(Laser):
    """A laser shot that can fly at an angle."""

    def __init__(self, x, y, kind, angle=0):
        super().__init__(x, y)
        spec = WEAPONS[kind]
        self.image, self.mask = _bolt_image(kind, round(angle))
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.pos = pygame.math.Vector2(self.rect.center)
        radians = math.radians(angle)
        self.velocity = pygame.math.Vector2(math.sin(radians), -math.cos(radians)) * spec['speed']
        self.power = spec['power']

    def update(self, *args, **kwargs):
        self.pos += self.velocity
        self.rect.center = self.pos
        if not OFF_SCREEN.colliderect(self.rect):
            self.kill()


class WeaponState:
    """Where the shark is on the ladder."""

    def __init__(self):
        self.kind = BASE
        self.time_left = 0

    @property
    def _spec(self):
        return WEAPONS.get(self.kind)

    @property
    def cost(self):
        return self._spec['cost'] if self._spec else BASE_COST

    @property
    def cooldown(self):
        return self._spec['cooldown'] if self._spec else BASE_COOLDOWN

    @property
    def label(self):
        """What the HUD shows, which is nothing for the plain laser."""
        return self._spec['name'] if self._spec else None

    @property
    def at_best(self):
        return self.kind == LADDER[-1]

    @property
    def time_share(self):
        """How much of its time this upgrade has left, from 1 down to 0. None for the plain laser."""
        return self.time_left / UPGRADE_MS if self._spec else None

    def upgrade(self):
        self.kind = LADDER[min(len(LADDER) - 1, LADDER.index(self.kind) + 1)]
        self.time_left = UPGRADE_MS

    def downgrade(self):
        self.kind = LADDER[max(0, LADDER.index(self.kind) - 1)]
        self.time_left = UPGRADE_MS

    def update(self, dt):
        if self.kind != BASE:
            self.time_left -= dt
            if self.time_left <= 0:
                self.downgrade()

    def fire(self, x, y):
        spec = self._spec
        if not spec:
            return [Laser(x, y)]
        count = spec['shots']
        if count == 1:
            return [Bolt(x, y, self.kind)]
        return [Bolt(x, y, self.kind, -spec['spread'] + i * 2 * spec['spread'] / (count - 1)) for i in range(count)]


def upgrade_icon():
    """A plain yellow hexagon. Every upgrade looks the same, as it just means 'better'."""
    if 'icon' not in _icon:
        image = pygame.Surface((28, 28), pygame.SRCALPHA)
        points = [(14 + math.cos(i * math.pi / 3 + math.pi / 6) * 13, 14 + math.sin(i * math.pi / 3 + math.pi / 6) * 13)
                  for i in range(6)]
        pygame.draw.polygon(image, (255, 220, 40), points)
        _icon['icon'] = image
    return _icon['icon']


def weapon_swatch(kind):
    """A sample of what a weapon fires, for the briefing."""
    image = pygame.Surface((34, 34), pygame.SRCALPHA)
    color = WEAPONS[kind]['color'] if kind in WEAPONS else (255, 90, 90)
    if kind == 'shotgun':
        for x, y in ((6, 20), (11, 11), (17, 7), (23, 11), (28, 20)):
            pygame.draw.circle(image, color, (x, y), 4)
    elif kind == 'fan':
        for end in ((4, 6), (17, 2), (30, 6)):
            pygame.draw.line(image, color, (17, 32), end, 3)
    elif kind == 'rapid':
        for y in (2, 13, 24):
            pygame.draw.rect(image, color, (14, y, 6, 8), border_radius=2)
    else:
        pygame.draw.rect(image, color, (13, 4, 8, 26), border_radius=3)
        pygame.draw.rect(image, (255, 255, 255), (16, 6, 2, 22))
    return image


class WeaponPowerup(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = upgrade_icon()
        self.rect = self.image.get_rect(center=(x, y))
