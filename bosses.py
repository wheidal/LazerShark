"""
The bosses after the eel, one for each stretch of the journey, and the order they come in.
"""
import math
import random

import pygame

from boss import (BOSS_SCORE, Boss, BossPart, Hazard, HEAD_LASER_DAMAGE, HEAVY_DAMAGE, LASER_DAMAGE,
                  LUNGE_Y_RANGE, MorayEel, _white)
from player_enhanced import SharkWithSprites

SWITCH_Y = 215
_art = {}


def _cached(key, make):
    """Art comes as (normal, flash) pairs, drawn once and shared."""
    if key not in _art:
        image = make()
        _art[key] = (image, _white(image))
    return _art[key]


def _ball(radius, color, dark, spot=None):
    def make():
        image = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(image, (14, 16, 24), (radius + 1, radius + 1), radius + 1)
        pygame.draw.circle(image, dark, (radius + 1, radius + 1), radius)
        pygame.draw.circle(image, color, (radius, radius - 1), max(1, radius - 3))
        if spot:
            pygame.draw.circle(image, spot, (radius, radius), max(1, radius // 3))
        return image
    return _cached(('ball', radius, color), make)


class Orb(Hazard):
    """A slow shot aimed where the shark was."""

    def __init__(self, center, target, color, speed=3.5, radius=11):
        super().__init__()
        self.image = _ball(radius, color, tuple(c // 2 for c in color), (255, 255, 240))[0]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=center)
        self.pos = pygame.math.Vector2(center)
        heading = pygame.math.Vector2(target) - self.pos
        self.velocity = heading.normalize() * speed if heading.length() else pygame.math.Vector2(0, speed)

    def update(self):
        self.pos += self.velocity
        self.rect.center = self.pos
        if not pygame.Rect(-40, -40, 880, 680).colliderect(self.rect):
            self.kill()


class LavaVent(Hazard):
    """Glows on the seabed as a warning, then erupts."""
    single_use = False
    RADIUS = 62
    ERUPT_STEPS = 40

    def __init__(self, center, warn_steps):
        super().__init__()
        size = self.RADIUS * 2
        self.warn_steps = warn_steps
        self.timer = warn_steps
        self.active = False
        self.warn_images = []
        for strength in (70, 150):
            image = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(image, (255, 90, 20, strength), (self.RADIUS, self.RADIUS), self.RADIUS, 5)
            pygame.draw.circle(image, (255, 150, 40, strength // 2), (self.RADIUS, self.RADIUS), self.RADIUS // 3)
            self.warn_images.append(image)
        self.erupt = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.erupt, (200, 40, 10), (self.RADIUS, self.RADIUS), self.RADIUS)
        pygame.draw.circle(self.erupt, (255, 130, 20), (self.RADIUS, self.RADIUS), self.RADIUS - 12)
        pygame.draw.circle(self.erupt, (255, 235, 130), (self.RADIUS, self.RADIUS), self.RADIUS // 2)
        self.image = self.warn_images[0]
        self.rect = self.image.get_rect(center=center)
        self.mask = pygame.mask.from_surface(self.erupt)

    def update(self):
        self.timer -= 1
        if self.active:
            if self.timer <= 0:
                self.kill()
        elif self.timer <= 0:
            self.active = True
            self.image = self.erupt
            self.timer = self.ERUPT_STEPS
        else:
            self.image = self.warn_images[self.timer // 6 % 2]


class Beam(Hazard):
    """A wall of energy across the whole arena."""
    single_use = False
    HEIGHT = 34
    STEPS = 30

    def __init__(self, left, right, y):
        super().__init__()
        self.image = pygame.Surface((right - left, self.HEIGHT), pygame.SRCALPHA)
        self.image.fill((90, 220, 255, 230))
        self.image.fill((235, 255, 255), (0, self.HEIGHT // 3, right - left, self.HEIGHT // 3))
        self.rect = self.image.get_rect(midleft=(left, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.timer = self.STEPS

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.kill()


class GiantSquid(Boss):
    """Clings above the wreck. Its tentacles slam down and shield the head until they're destroyed."""
    name = "GIANT SQUID"
    arrival = "The wrecks are groaning..."
    health_scale = 1.3
    arena_reef = [(112, 118, 112), (88, 72, 62), (62, 58, 60), (40, 48, 62), (22, 32, 52)]
    TENTACLES = 4
    TENTACLE_SHARE = 0.15  # Each tentacle's share of the health bar
    SEGMENTS = 11
    HANG = 120
    SLAM_SPEED = 16
    RETRACT_SPEED = 8
    HOLD_STEPS = 45
    REST_STEPS = (35, 65)
    BODY_Y = 92

    def __init__(self, left_edge, right_edge, difficulty='normal'):
        super().__init__(left_edge, right_edge, difficulty)
        self.body_x = (left_edge + right_edge) // 2
        self.head = BossPart(self._mantle())
        self.tentacles = []
        for i in range(self.TENTACLES):
            parts = [BossPart(_ball(max(7, 15 - s // 2), (176, 66, 84), (112, 38, 60), (232, 170, 170)))
                     for s in range(self.SEGMENTS)]
            for part in parts:
                part.tentacle = i
            self.tentacles.append({'offset': (i - 1.5) * 42, 'hp': int(self.max_health * self.TENTACLE_SHARE),
                                   'parts': parts, 'x': self.body_x, 'y': 0})
        self.state = 'rest'
        self.timer = random.randint(*self.REST_STEPS)
        self.slamming = None
        self.target_x = self.body_x
        self.tip_y = 0

    @staticmethod
    def _mantle():
        def make():
            image = pygame.Surface((150, 112), pygame.SRCALPHA)
            pygame.draw.ellipse(image, (14, 16, 24), (0, 0, 150, 112))
            pygame.draw.ellipse(image, (150, 52, 76), (3, 3, 144, 106))
            pygame.draw.ellipse(image, (196, 86, 100), (20, 8, 110, 60))
            for x, y in ((30, 40), (56, 22), (92, 20), (118, 42), (70, 48)):
                pygame.draw.circle(image, (108, 34, 58), (x, y), 6)
            for x in (48, 102):  # Eyes, huge and watching
                pygame.draw.circle(image, (246, 230, 160), (x, 82), 15)
                pygame.draw.circle(image, (10, 10, 14), (x, 84), 8)
            return image
        return _cached('mantle', make)

    def _alive(self):
        return [t for t in self.tentacles if t['hp'] > 0]

    def step(self, shark_rect):
        reach = (self.right_edge - self.left_edge) // 2 - 110
        middle = (self.left_edge + self.right_edge) // 2
        self.body_x = middle + int(math.sin(self.age * 0.012) * reach)
        self.timer -= 1
        alive = self._alive()
        if self.state == 'rest' and self.timer <= 0:
            self._spit(shark_rect, alive)
            if alive:
                self.slamming = random.choice(alive)
                self.target_x = max(self.left_edge + 30, min(self.right_edge - 30, shark_rect.centerx))
                self.tip_y = self.BODY_Y + self.HANG
                self.state = 'warning'
                self.timer = self.warning
            else:
                self.timer = random.randint(*self.REST_STEPS)
        elif self.state == 'warning' and self.timer <= 0:
            self.state = 'slam'
        elif self.state == 'slam':
            self.tip_y += self.SLAM_SPEED
            if self.tip_y >= 570:
                self.tip_y = 570
                self.state = 'hold'
                self.timer = self.HOLD_STEPS
        elif self.state == 'hold' and self.timer <= 0:
            self.state = 'retract'
        elif self.state == 'retract':
            self.tip_y -= self.RETRACT_SPEED
            if self.tip_y <= self.BODY_Y + self.HANG:
                self.state = 'rest'
                self.slamming = None
                self.timer = random.randint(*self.REST_STEPS)
        if self.slamming and self.slamming['hp'] <= 0:  # Shot off mid-attack
            self.slamming = None
            self.state = 'rest'
            self.timer = random.randint(*self.REST_STEPS)
        self._place_parts(alive)

    def _spit(self, shark_rect, alive):
        shots = 1 if alive else 3
        for i in range(shots):
            aim = (shark_rect.centerx + (i - (shots - 1) / 2) * 90, shark_rect.centery)
            self.hazards.add(Orb((self.body_x, self.BODY_Y + 50), aim, (46, 40, 70)))

    def _place_parts(self, alive):
        self.parts.empty()
        flash = self.flash > 0
        for index, tentacle in enumerate(self.tentacles):
            if tentacle['hp'] <= 0:
                continue
            start = (self.body_x + tentacle['offset'], self.BODY_Y + 42)
            if tentacle is self.slamming and self.state in ('slam', 'hold', 'retract'):
                tip = (self.target_x, self.tip_y)
            else:
                tip = (start[0] + math.sin(self.age * 0.04 + index) * 24, start[1] + self.HANG)
            for s, part in enumerate(tentacle['parts']):
                t = (s + 1) / self.SEGMENTS
                ripple = math.sin(self.age * 0.1 + s * 0.7 + index) * 6
                part.show(part.frames, (start[0] + (tip[0] - start[0]) * t + ripple,
                                        start[1] + (tip[1] - start[1]) * t), flash)
                self.parts.add(part)
        self.head.show(self.head.frames, (self.body_x, self.BODY_Y), flash)
        self.parts.add(self.head)

    def on_shot(self, parts, heavy):
        tentacle_parts = [p for p in parts if hasattr(p, 'tentacle')]
        if tentacle_parts:
            tentacle = self.tentacles[tentacle_parts[0].tentacle]
            hit = min(tentacle['hp'], (HEAVY_DAMAGE if heavy else LASER_DAMAGE) * self.shot_power)
            tentacle['hp'] -= hit
            self.take_damage(hit)
        elif not self._alive():  # The head can't be hurt until its tentacles are gone
            self.hurt(HEAVY_DAMAGE if heavy else HEAD_LASER_DAMAGE)

    def targets(self):
        alive = self._alive()
        return [alive[0]['parts'][-1]] if alive else [self.head]

    def draw(self, screen):
        if self.state == 'warning' and self.age // 6 % 2:
            for y in range(self.BODY_Y + 60, 580, 34):
                pygame.draw.line(screen, (255, 60, 50), (self.target_x, y), (self.target_x, y + 18), 3)
        super().draw(screen)


class LavaCrab(Boss):
    """Armoured until it overheats. Vents erupt around you, then its shell opens to cool down."""
    name = "MAGMA CRAB"
    arrival = "The water is getting hot..."
    health_scale = 1.5
    arena_reef = [(230, 110, 40), (128, 52, 34), (72, 40, 40), (46, 34, 44), (24, 22, 36)]
    Y = 110
    WALK_SPEED = 2.5
    WALK_STEPS = 90
    OVERHEAT_STEPS = 170
    ARMOUR_HEAVY_DAMAGE = 2

    def __init__(self, left_edge, right_edge, difficulty='normal'):
        super().__init__(left_edge, right_edge, difficulty)
        self.x = (left_edge + right_edge) / 2
        self.direction = random.choice([-1, 1])
        self.shell = BossPart(self._shell_art(False))
        self.claws = [BossPart(self._claw_art(side)) for side in (-1, 1)]
        self.state = 'walk'
        self.timer = self.WALK_STEPS

    @staticmethod
    def _shell_art(open_shell):
        def make():
            image = pygame.Surface((176, 124), pygame.SRCALPHA)
            for side in (-1, 1):  # Legs
                for i in range(3):
                    y = 42 + i * 26
                    pygame.draw.line(image, (14, 14, 20), (88, y), (88 + side * 87, y + 12), 9)
                    pygame.draw.line(image, (96, 44, 34), (88, y), (88 + side * 85, y + 12), 5)
            pygame.draw.ellipse(image, (14, 14, 20), (24, 8, 128, 110))
            pygame.draw.ellipse(image, (72, 50, 52), (27, 11, 122, 104))
            if open_shell:
                pygame.draw.ellipse(image, (255, 120, 30), (52, 30, 72, 64))
                pygame.draw.ellipse(image, (255, 230, 130), (70, 44, 36, 34))
            else:
                for points in (((40, 40), (70, 60), (60, 92)), ((136, 40), (104, 64), (118, 94)),
                               ((88, 16), (82, 48), (98, 74), (88, 106))):
                    pygame.draw.lines(image, (255, 110, 30), False, points, 3)
            for x in (72, 104):
                pygame.draw.circle(image, (250, 230, 90), (x, 112), 6)
                pygame.draw.circle(image, (10, 10, 10), (x, 113), 3)
            return image
        return _cached(('shell', open_shell), make)

    @staticmethod
    def _claw_art(side):
        def make():
            image = pygame.Surface((64, 74), pygame.SRCALPHA)
            pygame.draw.polygon(image, (14, 14, 20), [(10, 0), (54, 0), (62, 40), (46, 74), (34, 40), (22, 74), (2, 40)])
            pygame.draw.polygon(image, (116, 62, 50), [(13, 3), (51, 3), (58, 40), (46, 66), (33, 34), (22, 66), (6, 40)])
            pygame.draw.line(image, (255, 110, 30), (20, 12), (44, 12), 3)
            return image
        return _cached(('claw', side), make)

    def step(self, shark_rect):
        self.timer -= 1
        limit = (self.right_edge - self.left_edge) // 2 - 130
        middle = (self.left_edge + self.right_edge) / 2
        if self.state == 'walk':
            self.x += self.direction * self.WALK_SPEED
            if abs(self.x - middle) >= limit:
                self.direction *= -1
                self.x += self.direction * self.WALK_SPEED * 2
            if self.timer <= 0:
                self._erupt(shark_rect)
                self.state = 'vents'
                self.timer = self.warning + LavaVent.ERUPT_STEPS
        elif self.state == 'vents' and self.timer <= 0:
            self.state = 'overheat'
            self.timer = self.OVERHEAT_STEPS
        elif self.state == 'overheat' and self.timer <= 0:
            self.state = 'walk'
            self.timer = self.WALK_STEPS
        self._place_parts()

    def _erupt(self, shark_rect):
        spots = [shark_rect.center]
        for _ in range(4 if self.angry else 2):
            spots.append((random.randint(self.left_edge + 70, self.right_edge - 70), random.randint(230, 540)))
        self.hazards.add(LavaVent(spot, self.warning) for spot in spots)

    def _place_parts(self):
        self.parts.empty()
        flash = self.flash > 0
        self.shell.show(self._shell_art(self.state == 'overheat'), (self.x, self.Y), flash)
        self.parts.add(self.shell)
        for side, claw in zip((-1, 1), self.claws):
            bob = math.sin(self.age * 0.08 + side) * 6
            claw.show(claw.frames, (self.x + side * 76, self.Y + 74 + bob), flash)
            self.parts.add(claw)

    def on_shot(self, parts, heavy):
        if self.state == 'overheat':
            if self.shell in parts:
                self.hurt(HEAVY_DAMAGE if heavy else HEAD_LASER_DAMAGE)
            else:
                self.hurt(HEAVY_DAMAGE if heavy else LASER_DAMAGE)
        elif heavy:  # Lasers just bounce off the armour
            self.hurt(self.ARMOUR_HEAVY_DAMAGE)

    def targets(self):
        return [self.shell]


class RivalShark(Boss):
    """Another cyborg shark, firing back. Shoot the lit switch to drop its shield."""
    name = "RIVAL SHARK"
    arrival = "ALERT: unknown laser signature"
    health_scale = 1.6
    arena_reef = [(120, 190, 210), (70, 90, 112), (52, 62, 88), (36, 44, 70), (20, 26, 48)]
    Y = 100
    SWIM_SPEED = 3
    ANGRY_SWIM_SPEED = 4
    SHIELD_DOWN_STEPS = 420
    ANGRY_SHIELD_DOWN_STEPS = 300
    BURST = 3
    BURST_GAP = 9
    REST_STEPS = (50, 90)
    SHOT_SPEED = 8

    def __init__(self, left_edge, right_edge, difficulty='normal'):
        super().__init__(left_edge, right_edge, difficulty)
        self.x = (left_edge + right_edge) / 2
        self.body = BossPart(self._body_art())
        self.switches = [BossPart(self._switch_art()) for _ in range(2)]
        self.switch_spots = [(left_edge + 34, SWITCH_Y), (right_edge - 34, SWITCH_Y)]
        self.lit = random.randrange(2)
        self.shield_down = 0
        self.state = 'rest'
        self.timer = random.randint(*self.REST_STEPS)
        self.burst_left = 0

    @staticmethod
    def _body_art():
        def make():
            try:
                image = pygame.transform.flip(SharkWithSprites(0, 0).image, False, True)
                image.fill((255, 130, 130, 255), special_flags=pygame.BLEND_RGBA_MULT)
                image.fill((70, 0, 0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                return image
            except Exception:
                return _ball(40, (160, 60, 70), (90, 30, 40))[0]
        return _cached('rival', make)

    @staticmethod
    def _switch_art():
        def make():
            image = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.rect(image, (14, 16, 24), (0, 0, 36, 36), border_radius=6)
            pygame.draw.rect(image, (70, 90, 104), (2, 2, 32, 32), border_radius=5)
            pygame.draw.circle(image, (120, 255, 150), (18, 18), 11)
            pygame.draw.circle(image, (235, 255, 240), (16, 16), 4)
            return image
        return _cached('switch', make)

    @property
    def shielded(self):
        return self.shield_down <= 0

    def step(self, shark_rect):
        self.timer -= 1
        if self.shield_down > 0:
            self.shield_down -= 1
            if self.shield_down == 0:
                self.lit = 1 - self.lit
        speed = self.ANGRY_SWIM_SPEED if self.angry else self.SWIM_SPEED
        self.x += max(-speed, min(speed, shark_rect.centerx - self.x))
        self.x = max(self.left_edge + 70, min(self.right_edge - 70, self.x))
        if self.state == 'rest' and self.timer <= 0:
            self.state = 'aim'
            self.timer = self.warning
        elif self.state == 'aim' and self.timer <= 0:
            self.state = 'burst'
            self.burst_left = self.BURST
            self.timer = 0
        elif self.state == 'burst' and self.timer <= 0:
            if self.burst_left > 0:
                self.burst_left -= 1
                self.timer = self.BURST_GAP
                shot = Orb((self.x, self.Y + 50), (self.x, 900), (255, 70, 60), self.SHOT_SPEED, 7)
                self.hazards.add(shot)
            else:
                self.state = 'rest'
                self.timer = random.randint(*self.REST_STEPS)
        self._place_parts()

    def _place_parts(self):
        self.parts.empty()
        self.body.show(self.body.frames, (self.x, self.Y + math.sin(self.age * 0.05) * 8), self.flash > 0)
        self.parts.add(self.body)
        if self.shielded:
            switch = self.switches[self.lit]
            switch.show(switch.frames, self.switch_spots[self.lit], False)
            self.parts.add(switch)

    def on_shot(self, parts, heavy):
        if self.shielded:
            if self.switches[self.lit] in parts:
                self.shield_down = self.ANGRY_SHIELD_DOWN_STEPS if self.angry else self.SHIELD_DOWN_STEPS
        elif self.body in parts:
            self.hurt(HEAVY_DAMAGE if heavy else HEAD_LASER_DAMAGE)

    def touching(self, shark, collided):
        # The switches are only machinery: swimming into one does no harm
        if collided(shark, self.body):
            return True
        return super().touching(shark, lambda a, b: False if b in self.switches else collided(a, b))

    def targets(self):
        return [self.switches[self.lit]] if self.shielded else [self.body]

    def draw(self, screen):
        if self.state == 'aim' and self.age // 4 % 2:
            pygame.draw.circle(screen, (255, 90, 70), (int(self.x), self.Y + 56), 12)
        super().draw(screen)
        for i, spot in enumerate(self.switch_spots):
            if not (self.shielded and i == self.lit):
                pygame.draw.rect(screen, (40, 50, 60), (spot[0] - 18, spot[1] - 18, 36, 36), border_radius=6)
        if self.shielded:
            center = self.body.rect.center
            pygame.draw.circle(screen, (110, 220, 255), center, 72, 3)
            pygame.draw.circle(screen, (200, 245, 255), center, 66, 1)


class Guardian(Boss):
    """The final boss. Atlantis's guardian uses every kind of attack, and opens its core after each."""
    name = "ATLANTEAN GUARDIAN"
    arrival = "The ruins are waking up..."
    health_scale = 2.2
    arena_reef = [(226, 206, 130), (130, 130, 110), (88, 100, 110), (52, 74, 100), (26, 44, 76)]
    Y = 110
    SWAY = 150
    OPEN_STEPS = 170
    ANGRY_OPEN_STEPS = 125
    ARMOUR_HEAVY_DAMAGE = 2
    ATTACKS = ('beam', 'volley', 'vents')
    VOLLEY = 5
    VOLLEY_SPREAD = 70

    def __init__(self, left_edge, right_edge, difficulty='normal'):
        super().__init__(left_edge, right_edge, difficulty)
        self.x = (left_edge + right_edge) / 2
        self.body = BossPart(self._body_art(False))
        self.attack_index = 0
        self.state = 'wind_up'
        self.timer = self.warning
        self.beam_y = 300  # The first attack is a beam, aimed through the middle

    @staticmethod
    def _body_art(open_core):
        def make():
            image = pygame.Surface((240, 150), pygame.SRCALPHA)
            for x in (0, 196):  # Shoulders
                pygame.draw.rect(image, (14, 16, 24), (x, 30, 44, 100), border_radius=8)
                pygame.draw.rect(image, (150, 136, 92), (x + 3, 33, 38, 94), border_radius=6)
                pygame.draw.line(image, (90, 220, 255), (x + 22, 44), (x + 22, 116), 3)
            pygame.draw.polygon(image, (14, 16, 24), [(46, 8), (194, 8), (210, 90), (160, 148), (80, 148), (30, 90)])
            pygame.draw.polygon(image, (182, 166, 110), [(50, 12), (190, 12), (205, 88), (157, 144), (83, 144), (35, 88)])
            pygame.draw.polygon(image, (214, 198, 140), [(66, 20), (174, 20), (180, 52), (60, 52)])
            for y in (64, 84, 104):
                pygame.draw.line(image, (120, 110, 76), (56, y), (184, y), 2)
            pygame.draw.circle(image, (20, 26, 36), (120, 92), 30)
            if open_core:
                pygame.draw.circle(image, (90, 220, 255), (120, 92), 27)
                pygame.draw.circle(image, (235, 255, 255), (120, 92), 13)
            else:
                pygame.draw.circle(image, (110, 104, 80), (120, 92), 27)
                pygame.draw.line(image, (70, 66, 50), (93, 92), (147, 92), 3)
                pygame.draw.line(image, (70, 66, 50), (120, 65), (120, 119), 3)
            for x in (92, 148):
                pygame.draw.circle(image, (90, 220, 255), (x, 36), 7)
            return image
        return _cached(('guardian', open_core), make)

    @property
    def attack(self):
        return self.ATTACKS[self.attack_index % len(self.ATTACKS)]

    def step(self, shark_rect):
        self.timer -= 1
        self.x = (self.left_edge + self.right_edge) / 2 + math.sin(self.age * 0.01) * self.SWAY
        if self.state == 'wind_up':
            if self.timer <= 0:
                self._fire(shark_rect)
                self.state = 'attacking'
                self.timer = 45
        elif self.state == 'attacking' and self.timer <= 0:
            self.state = 'open'
            self.timer = self.ANGRY_OPEN_STEPS if self.angry else self.OPEN_STEPS
        elif self.state == 'open' and self.timer <= 0:
            self.attack_index += 1
            self.state = 'wind_up'
            self.timer = self.warning
            self.beam_y = max(LUNGE_Y_RANGE[0] + 150, min(LUNGE_Y_RANGE[1], shark_rect.centery))
        self.parts.empty()
        self.body.show(self._body_art(self.state == 'open'), (self.x, self.Y), self.flash > 0)
        self.parts.add(self.body)

    def _fire(self, shark_rect):
        if self.attack == 'beam':
            self.hazards.add(Beam(self.left_edge, self.right_edge, self.beam_y))
        elif self.attack == 'volley':
            for i in range(self.VOLLEY):
                aim = (shark_rect.centerx + (i - self.VOLLEY // 2) * self.VOLLEY_SPREAD, shark_rect.centery)
                self.hazards.add(Orb((self.x, self.Y + 60), aim, (90, 220, 255), 4.5))
        else:
            spots = [shark_rect.center]
            for _ in range(4 if self.angry else 3):
                spots.append((random.randint(self.left_edge + 70, self.right_edge - 70), random.randint(260, 540)))
            self.hazards.add(LavaVent(spot, self.warning) for spot in spots)

    def on_shot(self, parts, heavy):
        if self.state == 'open':
            self.hurt(HEAVY_DAMAGE if heavy else HEAD_LASER_DAMAGE)
        elif heavy:
            self.hurt(self.ARMOUR_HEAVY_DAMAGE)

    def targets(self):
        return [self.body]

    def draw(self, screen):
        if self.state == 'wind_up' and self.attack == 'beam' and self.age // 6 % 2:
            for x in range(self.left_edge, self.right_edge, 34):
                pygame.draw.line(screen, (90, 220, 255), (x, self.beam_y), (x + 18, self.beam_y), 3)
        super().draw(screen)


# Each boss and the score that summons it
BOSS_ROSTER = [
    (MorayEel, BOSS_SCORE),
    (GiantSquid, 400),
    (LavaCrab, 800),
    (RivalShark, 1300),
    (Guardian, 1900),
]
