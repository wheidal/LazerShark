"""
How the shark and its shield look. All of it is display only: collisions still use the shark's
own image and rect, so nothing drawn here changes what can hit it.
"""
import math
import random

import pygame

from weapons import BASE, WEAPONS

BASE_COLOR = (255, 70, 60)  # The plain laser's glow
MAX_LEAN = 15  # Degrees
LEAN_PER_PX = 3.2  # Degrees per px moved sideways in a frame
LEAN_EASING = 0.22
LEAN_STEP = 3  # Leans are cached at this spacing
HIT_FLASH_MS = 260
HIT_RED = (170, 10, 0)

SHIELD_RADIUS = 68
SHIELD_FULL = (90, 200, 255)
SHIELD_MID = (255, 215, 80)
SHIELD_LOW = (255, 80, 60)
MID_AT = 66
LOW_AT = 33
FLICKER_BELOW = 20
FLICKER_MS = 70
RIPPLE_MS = 380
SHARDS = 22
SHARD_MS = 650
STEEL = (150, 160, 172)
STEEL_DARK = (72, 80, 92)
RIVET = (214, 220, 226)


def _dress(image, color):
    """A copy of a shark frame with its cyborg parts bolted on, in this weapon's colour."""
    dressed = image.copy()
    w, h = dressed.get_size()
    # Measured from the middle of the sprite, so a fallback shark of another size still works
    cx = w // 2

    def at(x, y):
        return cx + x * w / 113, y * h / 107

    # Armour along the front of each fin
    for side in (-1, 1):
        plate = [at(side * 12, 25), at(side * 22, 30), at(side * 23, 35), at(side * 12, 31)]
        pygame.draw.polygon(dressed, STEEL_DARK, plate)
        pygame.draw.polygon(dressed, STEEL, plate, 1)
    # Metal jaw plate, down one side of the snout
    jaw = [at(-3, 3), at(-8, 8), at(-10, 20), at(-5, 19), at(-3, 10)]
    pygame.draw.polygon(dressed, STEEL_DARK, jaw)
    pygame.draw.polygon(dressed, STEEL, jaw, 1)
    pygame.draw.circle(dressed, RIVET, at(-7, 16), 1)
    # The eye on the other side glows
    eye = at(7, 13)
    glow = pygame.Surface((10, 10), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 40, 30, 110), (5, 5), 5)
    dressed.blit(glow, (eye[0] - 5, eye[1] - 5))
    pygame.draw.circle(dressed, (255, 70, 50), eye, 2)
    # Laser cannon on top of the head. It reaches the sprite's top, where the shots start.
    pygame.draw.rect(dressed, (20, 24, 32), (*at(-3, 0), 6 * w / 113, 14 * h / 107))
    pygame.draw.rect(dressed, STEEL, (*at(-2, 1), 4 * w / 113, 12 * h / 107))
    pygame.draw.line(dressed, color, at(0, 2), at(0, 12), 1)
    pygame.draw.circle(dressed, (20, 24, 32), at(0, 17), 6)
    pygame.draw.circle(dressed, STEEL_DARK, at(0, 17), 5)
    pygame.draw.circle(dressed, color, at(0, 17), 3)
    pygame.draw.circle(dressed, (255, 255, 255), at(0, 17), 1)
    # A power line back along the spine, in the weapon's colour
    pygame.draw.line(dressed, color, at(0, 23), at(0, 40), 1)
    return dressed


def shield_color(strength):
    if strength > MID_AT:
        return SHIELD_FULL
    return SHIELD_MID if strength > LOW_AT else SHIELD_LOW


def _bubble(color):
    size = SHIELD_RADIUS * 2 + 8
    center = size // 2
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(image, color + (34,), (center, center), SHIELD_RADIUS)
    pygame.draw.circle(image, color + (70,), (center, center), SHIELD_RADIUS, 7)
    pygame.draw.circle(image, color + (225,), (center, center), SHIELD_RADIUS, 2)
    # A soft shine, so it reads as a sphere
    shine = pygame.Rect(center - 40, center - SHIELD_RADIUS + 9, 80, 40)
    pygame.draw.arc(image, (255, 255, 255, 150), shine, 0.7, 2.45, 3)
    return image


class SharkLook:
    def __init__(self):
        self.lean = 0
        self.last_x = None
        self.hit_left = 0
        self.ripples = []  # (angle from the shark's centre, ms left)
        self.shards = []
        self.frames = {}
        self.bubbles = {}

    def reset(self):
        self.lean = 0
        self.last_x = None
        self.hit_left = 0
        self.ripples = []
        self.shards = []
        self.frames = {}  # A restarted game has a new shark, with new frames

    def hit(self):
        self.hit_left = HIT_FLASH_MS

    def shield_hit(self, center, point=None):
        """point is where the blow landed. Without one, the blow takes the shield at the nose."""
        angle = -math.pi / 2
        if point:
            angle = math.atan2(point[1] - center[1], point[0] - center[0])
        self.ripples.append([angle, RIPPLE_MS])

    def shield_break(self, center, color=SHIELD_LOW):
        self.ripples = []
        for _ in range(SHARDS):
            angle = random.uniform(0, math.tau)
            start = (center[0] + math.cos(angle) * SHIELD_RADIUS, center[1] + math.sin(angle) * SHIELD_RADIUS)
            speed = random.uniform(0.08, 0.26)
            self.shards.append({'pos': pygame.math.Vector2(start),
                                'velocity': pygame.math.Vector2(math.cos(angle), math.sin(angle)) * speed,
                                'spin': random.uniform(0, math.tau), 'left': SHARD_MS, 'color': color})

    def _frame(self, image, kind):
        key = (id(image), kind, round(self.lean / LEAN_STEP) * LEAN_STEP, self.hit_left > 0)
        if key not in self.frames:
            color = WEAPONS[kind]['color'] if kind != BASE else BASE_COLOR
            frame = _dress(image, color)
            if self.hit_left > 0:
                frame.fill(HIT_RED, special_flags=pygame.BLEND_RGB_ADD)  # Only where the shark is
            self.frames[key] = pygame.transform.rotate(frame, key[2])
        return self.frames[key]

    def _lean_towards(self, x):
        moved = x - self.last_x if self.last_x is not None else 0
        self.last_x = x
        target = max(-MAX_LEAN, min(MAX_LEAN, -moved * LEAN_PER_PX))  # Nose towards the turn
        self.lean += (target - self.lean) * LEAN_EASING

    def draw_shark(self, screen, shark, kind=BASE, dt=16):
        self.hit_left = max(0, self.hit_left - dt)
        self._lean_towards(shark.rect.centerx)
        frame = self._frame(shark.image, kind)
        screen.blit(frame, frame.get_rect(center=shark.rect.center))

    def draw_shield(self, screen, center, strength, now, dt=16):
        self._draw_shards(screen, dt)
        if strength <= 0:
            return
        color = shield_color(strength)
        if strength >= FLICKER_BELOW or now // FLICKER_MS % 2 == 0:
            if color not in self.bubbles:
                self.bubbles[color] = _bubble(color)
            screen.blit(self.bubbles[color], self.bubbles[color].get_rect(center=center))
        for ripple in self.ripples:
            ripple[1] -= dt
            if ripple[1] > 0:
                done = 1 - ripple[1] / RIPPLE_MS
                x = center[0] + math.cos(ripple[0]) * SHIELD_RADIUS
                y = center[1] + math.sin(ripple[0]) * SHIELD_RADIUS
                ring = pygame.Surface((SHIELD_RADIUS * 2, SHIELD_RADIUS * 2), pygame.SRCALPHA)
                alpha = int(235 * (1 - done))
                pygame.draw.circle(ring, (255, 255, 255, alpha), (SHIELD_RADIUS, SHIELD_RADIUS),
                                   int(6 + done * (SHIELD_RADIUS - 8)), 3)
                screen.blit(ring, (x - SHIELD_RADIUS, y - SHIELD_RADIUS))
        self.ripples = [ripple for ripple in self.ripples if ripple[1] > 0]

    def _draw_shards(self, screen, dt):
        for shard in self.shards:
            shard['left'] -= dt
            shard['pos'] += shard['velocity'] * dt
            shard['spin'] += 0.02 * dt
            if shard['left'] > 0:
                points = [shard['pos'] + pygame.math.Vector2(math.cos(shard['spin'] + a), math.sin(shard['spin'] + a)) * r
                          for a, r in ((0, 9), (2.3, 5), (4.1, 6))]
                pygame.draw.polygon(screen, shard['color'], points)
                pygame.draw.polygon(screen, (255, 255, 255), points, 1)
        self.shards = [shard for shard in self.shards if shard['left'] > 0]
