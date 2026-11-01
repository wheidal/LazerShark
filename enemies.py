"""
Enemies: obstacles that hunt the shark. They live in the obstacles group, so shots, blasts and
scoring treat them alike, but they steer themselves instead of scrolling with the coast.
"""
import math
import random

import pygame

from boss import Hazard
from obstacle import SeaMine, _finish

# How often enemies arrive and how many may be about, by difficulty
ENEMY_SPAWN_MS = {'easy': 4500, 'normal': 3200, 'hard': 2200}
ENEMY_LIMIT = {'easy': 2, 'normal': 3, 'hard': 5}
SCREEN = pygame.Rect(0, 0, 800, 600)
OFF_SCREEN = SCREEN.inflate(240, 240)
OFF_BOTTOM = 620
STEER_LOOKAHEAD = 80
STEER_MARGIN = 10
STEER_SPEED = 5
_art = {}


def _cached(key, make):
    if key not in _art:
        _art[key] = make()
    return _art[key]


class Enemy(pygame.sprite.Sprite):
    WIDTH, HEIGHT = 60, 60
    kind = 'enemy'
    name = "Enemy"
    min_score = 0
    toughness = 1
    damage = 15
    reward = 1
    counts_for_rewards = False
    blast_radius = 0
    blast_damage = 0
    debris_color = (200, 200, 200)
    drops_pickup = False
    bursts_on_coast = False
    steers = False

    def __init__(self, x, y, shark_rect, image):
        super().__init__()
        self.shark_rect = shark_rect
        self.set_image(image)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(x, y)
        self.hits = 0
        self.age = 0
        self.new_shots = []  # Beams for the game to take charge of
        self.new_obstacles = []  # Things released into the water

    def set_image(self, image):
        self.image = image
        self.mask = pygame.mask.from_surface(image, 127)

    def move_to_pos(self):
        # Replaces the scrolling the game applies to obstacles
        self.rect = self.image.get_rect(center=self.pos)
        if not OFF_SCREEN.collidepoint(self.pos) or self.pos.y > OFF_BOTTOM + 60:
            self.kill()

    def draw_warning(self, screen):
        pass

    def steer_clear_of(self, banks):
        """Slower swimmers would otherwise end up over the reef as the coast scrolls past."""
        if not self.steers:
            return
        for bank in banks:
            if bank.rect.top <= self.rect.bottom + STEER_LOOKAHEAD and bank.rect.bottom >= self.rect.top:
                if bank.rect.left == 0 and self.rect.left < bank.rect.right + STEER_MARGIN:
                    self.pos.x += STEER_SPEED
                    return
                if bank.rect.left > 0 and self.rect.right > bank.rect.left - STEER_MARGIN:
                    self.pos.x -= STEER_SPEED
                    return

    @classmethod
    def create(cls, x, shark_rect):
        return [cls(x, -cls.HEIGHT, shark_rect)]


def _tuna_art(lit):
    art = pygame.Surface((30, 64), pygame.SRCALPHA)
    body = (255, 110, 80) if lit else (72, 96, 150)
    belly = (255, 210, 180) if lit else (190, 205, 225)
    pygame.draw.polygon(art, (40, 56, 96), [(15, 50), (3, 63), (27, 63)])  # Tail
    pygame.draw.polygon(art, (40, 56, 96), [(15, 22), (1, 36), (29, 36)])  # Fins
    pygame.draw.ellipse(art, body, (5, 0, 20, 54))
    pygame.draw.ellipse(art, belly, (10, 8, 10, 36))
    for y in (46, 50, 54):
        pygame.draw.line(art, (250, 220, 70), (10, y), (20, y), 1)
    pygame.draw.circle(art, (250, 240, 120), (10, 10), 3)
    pygame.draw.circle(art, (250, 240, 120), (20, 10), 3)
    return _finish(pygame.transform.flip(art, False, True))  # Nose first, down the screen


class KamikazeTuna(Enemy):
    """Hangs at the top, picks its moment, then charges in a straight line and blows up."""
    WIDTH, HEIGHT = 40, 70
    kind = 'tuna'
    name = "Kamikaze Tuna"
    damage = 20
    reward = 2
    blast_radius = 95
    blast_damage = 10
    debris_color = (255, 170, 80)
    bursts_on_coast = True
    HOVER_Y = 70
    ENTER_SPEED = 3
    TRACK_STEPS = 40
    LOCK_STEPS = 22  # Aim is fixed from here, so a sidestep will beat it
    CHARGE_SPEED = 11

    def __init__(self, x, y, shark_rect):
        self.frames = [_cached(('tuna', lit), lambda: _tuna_art(lit)) for lit in (False, True)]
        super().__init__(x, y, shark_rect, self.frames[0])
        self.state = 'enter'
        self.timer = 0
        self.heading = pygame.math.Vector2(0, 1)

    def _turned(self, lit):
        angle = round(self.heading.angle_to(pygame.math.Vector2(0, 1)) / 10) * 10
        return _cached(('tuna', lit, angle), lambda: pygame.transform.rotate(self.frames[lit], angle))

    def _aim(self):
        to_shark = pygame.math.Vector2(self.shark_rect.center) - self.pos
        if to_shark.length():
            self.heading = to_shark.normalize()

    def update(self):
        if self.state == 'enter':
            self.pos.y += self.ENTER_SPEED
            if self.pos.y >= self.HOVER_Y:
                self.state = 'track'
                self.timer = self.TRACK_STEPS
        elif self.state == 'track':
            self.timer -= 1
            self._aim()
            self.set_image(self._turned(False))
            if self.timer <= 0:
                self.state = 'lock'
                self.timer = self.LOCK_STEPS
        elif self.state == 'lock':
            self.timer -= 1
            self.set_image(self._turned(self.timer // 3 % 2))
            if self.timer <= 0:
                self.state = 'charge'
                self.set_image(self._turned(True))
        else:
            self.pos += self.heading * self.CHARGE_SPEED
        self.move_to_pos()

    def draw_warning(self, screen):
        if self.state == 'lock':
            for i in range(1, 8):
                dot = self.pos + self.heading * i * 42
                pygame.draw.circle(screen, (255, 120, 80), dot, 3)


class MantaBeam(Hazard):
    """A column of laser straight down. It only hurts once."""
    single_use = True
    STEPS = 20
    WIDTH = 16
    damage = 15

    def __init__(self, x, top):
        super().__init__()
        height = max(1, 620 - int(top))
        self.image = pygame.Surface((self.WIDTH, height), pygame.SRCALPHA)
        self.image.fill((255, 60, 130, 210))
        self.image.fill((255, 235, 245), (self.WIDTH // 3, 0, self.WIDTH // 3, height))
        self.rect = self.image.get_rect(midtop=(x, top))
        self.mask = pygame.mask.from_surface(self.image)
        self.timer = self.STEPS

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.kill()


def _manta_art():
    art = pygame.Surface((110, 62), pygame.SRCALPHA)
    wings = [(55, 4), (84, 12), (108, 34), (78, 38), (62, 54), (55, 60), (48, 54), (32, 38), (2, 34), (26, 12)]
    pygame.draw.polygon(art, (44, 48, 84), wings)
    pygame.draw.polygon(art, (82, 74, 138), [(55, 10), (80, 18), (96, 32), (72, 34), (55, 50), (38, 34), (14, 32), (30, 18)])
    for x in (46, 64):
        pygame.draw.circle(art, (255, 90, 150), (x, 22), 3)
    pygame.draw.rect(art, (150, 160, 180), (49, 28, 12, 18), border_radius=3)  # The laser it's strapped to
    pygame.draw.circle(art, (255, 70, 130), (55, 44), 5)
    return _finish(art)


class LaserManta(Enemy):
    """Glides to and fro up high, stops to aim, and fires straight down. Vulnerable as it stops."""
    WIDTH, HEIGHT = 116, 70
    kind = 'manta'
    name = "Laser Manta"
    min_score = 20
    toughness = 4
    damage = 20
    reward = 6
    counts_for_rewards = True
    debris_color = (150, 120, 220)
    steers = True
    HOVER_Y = 95
    GLIDE_STEPS = (80, 130)
    AIM_STEPS = 42
    SHOTS = 3
    GLIDE_SPEED = 2.5
    LEAVE_SPEED = 2.5
    EDGE = 70

    def __init__(self, x, y, shark_rect):
        super().__init__(x, y, shark_rect, _cached('manta', _manta_art))
        self.state = 'enter'
        self.timer = 0
        self.shots_left = self.SHOTS
        self.direction = random.choice([-1, 1])

    def update(self):
        self.age += 1
        self.timer -= 1
        if self.state == 'enter':
            self.pos.y += 2.5
            if self.pos.y >= self.HOVER_Y:
                self.state = 'glide'
                self.timer = random.randint(*self.GLIDE_STEPS)
        elif self.state == 'glide':
            # Drifts over the shark's side of the channel, then lines up
            self.direction = 1 if self.shark_rect.centerx > self.pos.x else self.direction
            self.direction = -1 if self.shark_rect.centerx < self.pos.x else self.direction
            self.pos.x += self.direction * self.GLIDE_SPEED
            self.pos.x = max(self.EDGE, min(SCREEN.right - self.EDGE, self.pos.x))
            if self.timer <= 0:
                self.state = 'aim'
                self.timer = self.AIM_STEPS
        elif self.state == 'aim':
            if self.timer <= 0:
                self.new_shots.append(MantaBeam(self.pos.x, self.pos.y + 30))
                self.shots_left -= 1
                self.state = 'glide' if self.shots_left else 'leave'
                self.timer = random.randint(*self.GLIDE_STEPS)
        else:
            self.pos.y += self.LEAVE_SPEED
        self.pos.y += math.sin(self.age * 0.05) * 0.3
        self.move_to_pos()

    def draw_warning(self, screen):
        if self.state == 'aim' and self.age // 5 % 2:
            for y in range(int(self.pos.y) + 40, 600, 34):
                pygame.draw.line(screen, (255, 70, 130), (self.pos.x, y), (self.pos.x, y + 16), 2)


def _barracuda_art():
    art = pygame.Surface((20, 62), pygame.SRCALPHA)
    pygame.draw.polygon(art, (120, 136, 150), [(10, 62), (1, 48), (19, 48)])
    pygame.draw.polygon(art, (186, 200, 210), [(10, 0), (17, 22), (15, 50), (5, 50), (3, 22)])
    pygame.draw.line(art, (90, 104, 120), (10, 8), (10, 48), 2)
    pygame.draw.polygon(art, (250, 80, 70), [(4, 26), (0, 36), (6, 34)])
    pygame.draw.polygon(art, (250, 80, 70), [(16, 26), (20, 36), (14, 34)])
    pygame.draw.circle(art, (255, 60, 50), (7, 10), 2)
    pygame.draw.circle(art, (255, 60, 50), (13, 10), 2)
    return _finish(pygame.transform.flip(art, False, True))


class Barracuda(Enemy):
    """Weak alone, but they come in a weaving V. Wide weapons shred them."""
    WIDTH, HEIGHT = 190, 150
    kind = 'barracuda'
    name = "Cyber Barracuda"
    min_score = 45
    damage = 12
    reward = 1
    debris_color = (190, 205, 215)
    SWIM_SPEED = 4.2
    WEAVE = 32
    WEAVE_SPEED = 0.05

    def __init__(self, x, y, shark_rect, phase=0):
        super().__init__(x, y, shark_rect, _cached('barracuda', _barracuda_art))
        self.home_x = x
        self.age = phase

    def update(self):
        self.age += 1
        self.pos.y += self.SWIM_SPEED
        self.pos.x = self.home_x + math.sin(self.age * self.WEAVE_SPEED) * self.WEAVE
        self.move_to_pos()

    @classmethod
    def create(cls, x, shark_rect):
        count = random.choice([3, 5])
        phase = random.randrange(200)
        pack = []
        for i in range(count):
            rank = (i + 1) // 2
            side = -1 if i % 2 else 1
            pack.append(cls(x + side * rank * 32, -40 - rank * 40, shark_rect, phase))
        return pack


def _torpedo_art():
    art = pygame.Surface((16, 40), pygame.SRCALPHA)
    pygame.draw.rect(art, (120, 40, 40), (3, 0, 10, 34), border_radius=5)
    pygame.draw.rect(art, (70, 76, 86), (3, 26, 10, 8))
    pygame.draw.polygon(art, (70, 76, 86), [(8, 26), (0, 38), (16, 38)])
    return _finish(pygame.transform.flip(art, False, True))


class EnemyTorpedo(Enemy):
    """Slow enough to dodge, and can be shot down."""
    kind = 'enemy_torpedo'
    name = "Enemy Torpedo"
    damage = 18
    debris_color = (255, 140, 70)
    SPEED = 4.5

    def __init__(self, x, y, shark_rect):
        super().__init__(x, y, shark_rect, _cached('torpedo', _torpedo_art))
        to_shark = pygame.math.Vector2(shark_rect.center) - self.pos
        self.velocity = to_shark.normalize() * self.SPEED if to_shark.length() else pygame.math.Vector2(0, self.SPEED)

    def update(self):
        self.pos += self.velocity
        self.move_to_pos()


def _sub_art():
    art = pygame.Surface((64, 120), pygame.SRCALPHA)
    pygame.draw.ellipse(art, (40, 24, 30), (6, 0, 52, 120))
    pygame.draw.ellipse(art, (88, 42, 50), (11, 5, 42, 110))
    pygame.draw.rect(art, (130, 70, 70), (20, 40, 24, 40), border_radius=6)
    pygame.draw.circle(art, (250, 220, 90), (32, 52), 6)
    for y in (24, 96):
        pygame.draw.line(art, (50, 28, 34), (16, y), (48, y), 2)
    pygame.draw.polygon(art, (50, 28, 34), [(32, 2), (0, 20), (10, 26)])
    pygame.draw.polygon(art, (50, 28, 34), [(32, 2), (64, 20), (54, 26)])
    return _finish(art)


class EvilSub(Enemy):
    """Slowly works its way down, firing torpedoes and laying mines. Pays out when destroyed."""
    WIDTH, HEIGHT = 80, 130
    kind = 'evil_sub'
    name = "Evil Sub"
    min_score = 85
    toughness = 14
    damage = 33
    reward = 12
    counts_for_rewards = True
    debris_color = (170, 90, 80)
    drops_pickup = True
    steers = True
    SPEED = 1.3
    FIRE_STEPS = 100

    def __init__(self, x, y, shark_rect):
        super().__init__(x, y, shark_rect, _cached('sub', _sub_art))
        self.shots_fired = 0

    def update(self):
        self.age += 1
        self.pos.y += self.SPEED
        if self.age % self.FIRE_STEPS == 0 and self.pos.y > 0:
            self.shots_fired += 1
            if self.shots_fired % 3 == 0:
                self.new_obstacles.append(SeaMine(int(self.pos.x), int(self.pos.y) + 40))
            else:
                self.new_obstacles.append(EnemyTorpedo(self.pos.x, self.pos.y + 50, self.shark_rect))
        self.move_to_pos()


ENEMY_TYPES = {cls.kind: cls for cls in (KamikazeTuna, LaserManta, Barracuda, EvilSub)}


def choose_enemy(kinds, score):
    """A kind of enemy allowed at this score, or None."""
    allowed = [kind for kind in kinds if ENEMY_TYPES[kind].min_score <= score]
    return ENEMY_TYPES[random.choice(allowed)] if allowed else None
