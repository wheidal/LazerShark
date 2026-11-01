"""
The giant moray eel: lives in the arena's banks and lunges across the water.
The shark can only fire upwards, so the way to beat it is to dodge below a lunge and shoot.
"""
import math
import random

import pygame

BOSS_SCORE = 120  # The arena opens once a run reaches this score
# Each fight rolls its own values from these ranges, so no two play quite alike
DIFFICULTIES = {
    'easy': {'health': (60, 80), 'bite': (15, 20), 'warn_steps': (60, 75)},
    'normal': {'health': (90, 120), 'bite': (20, 30), 'warn_steps': (45, 60)},
    'hard': {'health': (130, 170), 'bite': (30, 40), 'warn_steps': (34, 45)},
}
DEFAULT_DIFFICULTY = 'normal'
LASER_RECHARGE = {'easy': 18, 'normal': 12, 'hard': 7}  # Energy per second, for the whole run
ANGRY_WARN_SHARE = 0.7  # Warnings shorten by this much once the eel is hurt
CONTACT_INVULN_MS = 1000
VICTORY_SCORE = 100
LASER_DAMAGE = 1
HEAD_LASER_DAMAGE = 2
HEAVY_DAMAGE = 6  # Missiles and torpedoes
ANGRY_AT = 0.5  # Share of health below which the eel attacks faster

LUNGE_Y_RANGE = (110, 430)  # Always leaves room to get below it
HIDE_STEPS = (45, 80)
EXPOSED_STEPS = 80
ANGRY_EXPOSED_STEPS = 55
LUNGE_SPEED = 14
RETRACT_SPEED = 6
REACH = 0.72  # Share of the arena's width a lunge covers
SEGMENTS = 24
SEGMENT_SPACING = 19
WAVE = 9  # How far the body ripples, in px
FLASH_STEPS = 4

BODY = (84, 112, 58)
BODY_DARK = (48, 70, 38)
SPOT = (196, 186, 92)
_art = {}


def _white(image):
    flash = image.copy()
    flash.fill((120, 120, 120, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return flash


def _segment_art(radius):
    if radius not in _art:
        rng = random.Random(radius)
        size = radius * 2 + 2
        image = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (radius + 1, radius + 1)
        pygame.draw.circle(image, (14, 22, 18), center, radius + 1)
        pygame.draw.circle(image, BODY_DARK, center, radius)
        pygame.draw.circle(image, BODY, (radius, radius - 1), radius - 3)
        for _ in range(4):
            angle, reach = rng.uniform(0, math.tau), rng.uniform(0, radius - 5)
            spot = (radius + math.cos(angle) * reach, radius + math.sin(angle) * reach)
            pygame.draw.circle(image, SPOT, spot, rng.randint(1, 3))
        _art[radius] = (image, _white(image))
    return _art[radius]


def _head_art(direction, mouth_open):
    key = ('head', direction, mouth_open)
    if key not in _art:
        image = pygame.Surface((72, 54), pygame.SRCALPHA)
        gape = 14 if mouth_open else 4
        pygame.draw.polygon(image, (14, 22, 18), [(0, 8), (46, 3), (71, 27 - gape), (40, 27),
                                                  (71, 27 + gape), (46, 51), (0, 46)])
        pygame.draw.polygon(image, BODY, [(2, 10), (45, 6), (66, 24 - gape), (38, 26),
                                          (66, 30 + gape), (45, 48), (2, 44)])
        pygame.draw.polygon(image, (150, 40, 50), [(38, 27), (66, 26 - gape), (66, 28 + gape)])
        for i in range(4):  # Teeth, top and bottom
            x = 44 + i * 6
            top = 22 - gape * (i + 1) // 4
            bottom = 32 + gape * (i + 1) // 4
            pygame.draw.polygon(image, (246, 240, 220), [(x, top), (x + 4, top), (x + 2, top + 7)])
            pygame.draw.polygon(image, (246, 240, 220), [(x, bottom), (x + 4, bottom), (x + 2, bottom - 7)])
        for spot in ((12, 18), (20, 36), (28, 14), (8, 34)):
            pygame.draw.circle(image, SPOT, spot, 3)
        for y in (14, 40):  # Seen from above, so both eyes show
            pygame.draw.circle(image, (240, 220, 60), (36, y), 5)
            pygame.draw.circle(image, (10, 10, 10), (37, y), 2)
        if direction < 0:
            image = pygame.transform.flip(image, True, False)
        _art[key] = (image, _white(image))
    return _art[key]


class EelPart(pygame.sprite.Sprite):
    def __init__(self, frames, is_head=False):
        super().__init__()
        self.frames = frames
        self.image = frames[0]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.is_head = is_head

    def show(self, frames, center, flash):
        if frames is not self.frames:  # The outline is the same whichever frame is showing
            self.frames = frames
            self.mask = pygame.mask.from_surface(frames[0])
        self.image = self.frames[1 if flash else 0]
        self.rect = self.image.get_rect(center=center)


class MorayEel:
    def __init__(self, left_edge, right_edge, difficulty=DEFAULT_DIFFICULTY):
        ranges = DIFFICULTIES.get(difficulty, DIFFICULTIES[DEFAULT_DIFFICULTY])
        health = random.randint(*ranges['health'])
        self.bite_damage = random.randint(*ranges['bite'])
        self.warn_steps = random.randint(*ranges['warn_steps'])
        self.left_edge = left_edge
        self.right_edge = right_edge
        self.health = self.max_health = health
        self.parts = pygame.sprite.Group()
        self.head = EelPart(_head_art(1, False), is_head=True)
        self.body = [EelPart(_segment_art(max(11, 24 - i // 2))) for i in range(SEGMENTS)]
        self.state = 'hidden'
        self.timer = random.randint(*HIDE_STEPS)
        self.side = random.choice([-1, 1])
        self.y = 300
        self.head_x = 0
        self.age = 0
        self.flash = 0
        self.rubble_due = 0  # Each full lunge shakes loose hazards, so the bottom of the screen isn't safe

    @property
    def dead(self):
        return self.health <= 0

    @property
    def angry(self):
        return self.health < self.max_health * ANGRY_AT

    @property
    def _hole_x(self):
        return self.left_edge if self.side < 0 else self.right_edge

    @property
    def _target_x(self):
        reach = (self.right_edge - self.left_edge) * REACH
        return self._hole_x + reach if self.side < 0 else self._hole_x - reach

    def update(self, shark_rect):
        self.age += 1
        self.flash = max(0, self.flash - 1)
        self.timer -= 1
        if self.state == 'hidden' and self.timer <= 0:
            self.state = 'warning'
            self.timer = int(self.warn_steps * ANGRY_WARN_SHARE) if self.angry else self.warn_steps
            self.side = random.choice([-1, 1])
            self.y = max(LUNGE_Y_RANGE[0], min(LUNGE_Y_RANGE[1], shark_rect.centery))
            self.head_x = self._hole_x
        elif self.state == 'warning' and self.timer <= 0:
            self.state = 'lunge'
        elif self.state == 'lunge':
            self.head_x -= self.side * LUNGE_SPEED
            if (self.head_x - self._target_x) * -self.side >= 0:
                self.head_x = self._target_x
                self.state = 'exposed'
                self.rubble_due = 2 if self.angry else 1
                self.timer = ANGRY_EXPOSED_STEPS if self.angry else EXPOSED_STEPS
        elif self.state == 'exposed' and self.timer <= 0:
            self.state = 'retract'
        elif self.state == 'retract':
            self.head_x += self.side * RETRACT_SPEED
            if (self.head_x - self._hole_x) * self.side >= 0:
                self.state = 'hidden'
                self.timer = random.randint(*HIDE_STEPS)
        self._place_parts()

    def _place_parts(self):
        self.parts.empty()
        if self.state in ('hidden', 'warning'):
            return
        flash = self.flash > 0
        # Facing away from the hole it came out of
        frames = _head_art(-self.side, self.state in ('lunge', 'exposed'))
        self.head.show(frames, (self.head_x, self.y), flash)
        self.parts.add(self.head)
        for i, part in enumerate(self.body):
            x = self.head_x + self.side * (i + 1) * SEGMENT_SPACING
            if (x - self._hole_x) * self.side > 0:  # Still inside the bank
                break
            ripple = math.sin(self.age * 0.18 + i * 0.55) * WAVE * min(1, i / 4)
            part.show(part.frames, (x, self.y + ripple), flash)
            self.parts.add(part)

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        self.flash = FLASH_STEPS

    def targets(self):
        """What a torpedo can home in on."""
        return [self.head] if self.head.alive() else []

    def draw(self, screen):
        if self.state != 'hidden':
            # The lair in the bank, drawn beneath the eel
            pygame.draw.ellipse(screen, (6, 10, 16), (self._hole_x - 26, self.y - 34, 52, 68))
            pygame.draw.ellipse(screen, (60, 46, 50), (self._hole_x - 26, self.y - 34, 52, 68), 3)
        if self.state == 'warning':
            if self.age // 6 % 2:
                for x in range(int(min(self._hole_x, self._target_x)), int(max(self._hole_x, self._target_x)), 34):
                    pygame.draw.line(screen, (255, 60, 50), (x, self.y), (x + 18, self.y), 3)
            for offset in (-11, 11):
                pygame.draw.circle(screen, (250, 230, 70), (self._hole_x, self.y + offset), 4)
        for part in sorted(self.parts, key=lambda p: p.is_head):
            screen.blit(part.image, part.rect)
