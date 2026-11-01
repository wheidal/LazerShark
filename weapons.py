"""
Laser upgrades. Collecting a new type swaps to it; collecting the same type powers it up.
Add a weapon by adding an entry to WEAPONS, with one row per level.
"""
import math

import pygame

from projectile import Laser

MAX_LEVEL = 3
BASE = 'laser'
OFF_SCREEN = pygame.Rect(-40, -60, 880, 720)

# cost: laser power per shot. cooldown: seconds between shots. power: damage per bolt.
# shots and spread (degrees either side of straight up). reach: px a bolt travels.
WEAPONS = {
    'fan': {
        'name': 'FAN', 'letter': 'F', 'color': (110, 240, 130), 'size': (6, 16), 'speed': 11, 'pierce': False,
        'levels': [
            {'cost': 4, 'cooldown': 0.16, 'power': 0.7, 'shots': 3, 'spread': 12, 'reach': 900},
            {'cost': 5, 'cooldown': 0.16, 'power': 0.7, 'shots': 5, 'spread': 20, 'reach': 900},
            {'cost': 6, 'cooldown': 0.16, 'power': 0.7, 'shots': 7, 'spread': 30, 'reach': 900},
        ],
    },
    'chum': {
        'name': 'CHUM', 'letter': 'C', 'color': (255, 50, 40), 'size': (11, 11), 'speed': 10, 'pierce': False,
        'ball': True,
        'levels': [
            {'cost': 8, 'cooldown': 0.45, 'power': 0.5, 'shots': 7, 'spread': 58, 'reach': 900},
            {'cost': 8, 'cooldown': 0.42, 'power': 0.5, 'shots': 9, 'spread': 58, 'reach': 900},
            {'cost': 8, 'cooldown': 0.38, 'power': 0.6, 'shots': 11, 'spread': 58, 'reach': 900},
        ],
    },
    'rapid': {
        'name': 'RAPID', 'letter': 'R', 'color': (255, 240, 90), 'size': (5, 16), 'speed': 15, 'pierce': False,
        'levels': [
            {'cost': 2, 'cooldown': 0.06, 'power': 0.8, 'shots': 1, 'spread': 0, 'reach': 900},
            {'cost': 2, 'cooldown': 0.05, 'power': 0.9, 'shots': 1, 'spread': 0, 'reach': 900},
            {'cost': 2, 'cooldown': 0.04, 'power': 1.0, 'shots': 1, 'spread': 0, 'reach': 900},
        ],
    },
    'beam': {
        'name': 'BEAM', 'letter': 'B', 'color': (120, 210, 255), 'size': (12, 64), 'speed': 20, 'pierce': True,
        'levels': [
            {'cost': 12, 'cooldown': 0.55, 'power': 5, 'shots': 1, 'spread': 0, 'reach': 900},
            {'cost': 12, 'cooldown': 0.45, 'power': 6, 'shots': 1, 'spread': 0, 'reach': 900},
            {'cost': 12, 'cooldown': 0.35, 'power': 8, 'shots': 1, 'spread': 0, 'reach': 900},
        ],
    },
}
BASE_COST = 3
BASE_COOLDOWN = 0.1
EARNED_WEAPON = 'fan'  # What destroying enough obstacles gives a shark still on the plain laser
EARNED_LEVEL = 2

_bolts = {}
_icons = {}


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
    """A laser shot that can fly at an angle, run out of range, or pass through what it hits."""

    def __init__(self, x, y, kind, stats, angle=0):
        super().__init__(x, y)
        spec = WEAPONS[kind]
        self.image, self.mask = _bolt_image(kind, round(angle))
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.pos = pygame.math.Vector2(self.rect.center)
        radians = math.radians(angle)
        self.velocity = pygame.math.Vector2(math.sin(radians), -math.cos(radians)) * spec['speed']
        self.power = stats['power']
        self.pierce = spec['pierce']
        self.reach = stats['reach']

    def update(self, *args, **kwargs):
        self.pos += self.velocity
        self.rect.center = self.pos
        self.reach -= self.velocity.length()
        if self.reach <= 0 or not OFF_SCREEN.colliderect(self.rect):
            self.kill()


class WeaponState:
    """The shark's current laser type and level."""

    def __init__(self):
        self.kind = BASE
        self.level = 1

    @property
    def _stats(self):
        return WEAPONS[self.kind]['levels'][self.level - 1] if self.kind != BASE else None

    @property
    def cost(self):
        return self._stats['cost'] if self._stats else BASE_COST

    @property
    def cooldown(self):
        return self._stats['cooldown'] if self._stats else BASE_COOLDOWN

    @property
    def label(self):
        """What the HUD shows, which is nothing for the plain laser."""
        return None if self.kind == BASE else f"{WEAPONS[self.kind]['name']} {self.level}"

    def collect(self, kind):
        if kind == self.kind:
            self.level = min(MAX_LEVEL, self.level + 1)
        else:
            self.kind, self.level = kind, 1

    def earn(self):
        """A reward for destroying obstacles."""
        if self.kind == BASE:
            self.kind, self.level = EARNED_WEAPON, EARNED_LEVEL
        else:
            self.level = min(MAX_LEVEL, self.level + 1)

    def lose_level(self):
        """Taking a hit costs a level, and the last one drops back to the plain laser."""
        if self.level > 1:
            self.level -= 1
        else:
            self.kind = BASE

    def fire(self, x, y):
        stats = self._stats
        if not stats:
            return [Laser(x, y)]
        count = stats['shots']
        if count == 1:
            return [Bolt(x, y, self.kind, stats)]
        return [Bolt(x, y, self.kind, stats, -stats['spread'] + i * 2 * stats['spread'] / (count - 1))
                for i in range(count)]


def weapon_icon(kind):
    if kind not in _icons:
        spec = WEAPONS[kind]
        image = pygame.Surface((32, 32), pygame.SRCALPHA)
        points = [(16 + math.cos(i * math.pi / 3) * 15, 16 + math.sin(i * math.pi / 3) * 15) for i in range(6)]
        pygame.draw.polygon(image, spec['color'] + (70,), [(16 + (x - 16) * 1.06, 16 + (y - 16) * 1.06) for x, y in points])
        pygame.draw.polygon(image, (12, 24, 40), points)
        pygame.draw.polygon(image, spec['color'], points, 3)
        letter = pygame.font.SysFont(None, 26).render(spec['letter'], True, (255, 255, 255))
        image.blit(letter, letter.get_rect(center=(16, 16)))
        _icons[kind] = image
    return _icons[kind]


class WeaponPowerup(pygame.sprite.Sprite):
    def __init__(self, x, y, kind):
        super().__init__()
        self.kind = kind
        self.image = weapon_icon(kind)
        self.rect = self.image.get_rect(center=(x, y))
