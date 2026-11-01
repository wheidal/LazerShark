"""
The arcade front end: gameplay playing itself behind the title, and a quick briefing before a game.
"""
import random

import pygame

from channel import ChannelDirector, SCROLL_PER_STEP
from enemies import RadioactivePiranha
from food import SmallFish, ZombieFish
from graphics_enhancements import ParticleEffects
from hazards import _whirlpool_art
from obstacle import EmpJellyfish, OBSTACLE_TYPES, RadiationBarrel
from player import Shark
from player_enhanced import SharkWithSprites
from shark_look import SharkLook
from powerup import LaserPowerup, MissilePowerup, ShieldPowerup, TorpedoPowerup
from projectile import Laser
from weapons import weapon_icon

SPAWN_STEPS = 80
FISH_CHANCE = 0.35
SIGHT = 380  # How far ahead the demo shark looks for something to shoot
FIRE_STEPS = 7
BANK_CLEARANCE = 60  # The demo shark's centre stays this far from the coast
BLINK_MS = 500
TITLE_COLOR = (255, 70, 50)
TITLE_SHADOW = (30, 6, 10)
PROMPT_COLOR = (255, 235, 120)
BRIEFING_MS = 7000  # Per page. Any key moves on sooner


def _outlined(font, text, color, outline=TITLE_SHADOW, width=3):
    face = font.render(text, True, color)
    edge = font.render(text, True, outline)
    image = pygame.Surface((face.get_width() + width * 2, face.get_height() + width * 2), pygame.SRCALPHA)
    for dx in (-width, 0, width):
        for dy in (-width, 0, width):
            image.blit(edge, (width + dx, width + dy))
    image.blit(face, (width, width))
    return image


class AttractMode:
    """A self-playing game. Nothing in it can hurt the shark, and it keeps no score."""

    def __init__(self, screen, enhancer):
        self.screen = screen
        self.enhancer = enhancer
        self.font = pygame.font.SysFont(None, 34)
        self.small = pygame.font.SysFont(None, 26)
        big = pygame.font.SysFont(None, 110)
        self.title_lines = [_outlined(big, "LAZER SHARK", TITLE_COLOR),
                            _outlined(big, "KILL! KILL!", (255, 225, 90))]
        self.reset()

    def reset(self):
        self.director = ChannelDirector()
        self.banks = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.foods = pygame.sprite.Group()
        self.shots = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        try:
            self.shark = SharkWithSprites(400, 480)
        except Exception:
            self.shark = Shark(400, 480)
        for chunk, y in self.director.prefill():
            self.banks.add(chunk.build(y))
        self.steps = 0
        self.look = SharkLook()

    def _channel_at_shark(self):
        """The open water alongside and just ahead of the shark."""
        top = self.shark.rect.top - 90
        left, right = 0, 800
        for bank in self.banks:
            if bank.rect.bottom >= top and bank.rect.top <= self.shark.rect.bottom:
                if bank.rect.left == 0:
                    left = max(left, bank.rect.right)
                else:
                    right = min(right, bank.rect.left)
        return left, right

    def _spawn(self):
        if random.random() < FISH_CHANCE:
            self.foods.add(SmallFish(self.director.spawn_x(26), -10))
            return
        kinds = self.director.obstacle_kinds()
        if kinds:
            kind = OBSTACLE_TYPES[random.choice(kinds)]
            x = self.director.spawn_x(kind.WIDTH, blocking=True, height=kind.HEIGHT)
            if x is not None:
                self.obstacles.add(kind.create(x))

    def _explode(self, sprite):
        ParticleEffects.create_explosion(self.particles, sprite.rect.center,
                                         [sprite.debris_color, (255, 210, 80), (255, 255, 200)], 18)
        sprite.kill()

    def _pilot(self):
        shark = self.shark
        left, right = self._channel_at_shark()
        ahead = [o for o in self.obstacles if 0 < shark.rect.top - o.rect.bottom < SIGHT]
        target = max(ahead, key=lambda o: o.rect.bottom, default=None)
        goal = target.rect.centerx if target else (left + right) // 2
        goal = max(left + BANK_CLEARANCE, min(right - BANK_CLEARANCE, goal))
        if target and self.steps % FIRE_STEPS == 0 and abs(shark.rect.centerx - target.rect.centerx) < 30:
            self.shots.add(Laser(shark.rect.centerx, shark.rect.top))
        return {'left': goal < shark.rect.centerx - 4, 'right': goal > shark.rect.centerx + 4,
                'up': False, 'down': False}

    def update(self, dt):
        self.steps += 1
        chunk = self.director.update(0)
        if chunk:
            self.banks.add(chunk.build())
        if self.steps % SPAWN_STEPS == 0:
            self._spawn()
        move = self._pilot()
        if hasattr(self.shark, 'update_with_input'):
            self.shark.update_with_input(move, dt)
        else:
            self.shark.update(dt, move)
        self.obstacles.update()
        self.shots.update()
        self.particles.update()
        for group in (self.banks, self.obstacles, self.foods):
            for sprite in group:
                sprite.rect.y += SCROLL_PER_STEP
                if sprite.rect.top > 600:
                    sprite.kill()
        pygame.sprite.groupcollide(self.shots, self.banks, True, False, pygame.sprite.collide_mask)
        for shot, hit in pygame.sprite.groupcollide(self.shots, self.obstacles, True, False,
                                                    pygame.sprite.collide_mask).items():
            for obstacle in hit:
                obstacle.hits += 1
                if obstacle.hits >= obstacle.toughness:
                    self._explode(obstacle)
        for obstacle in pygame.sprite.spritecollide(self.shark, self.obstacles, False, pygame.sprite.collide_mask):
            self._explode(obstacle)
        pygame.sprite.spritecollide(self.shark, self.foods, True)

    def draw_world(self):
        self.enhancer.render_background()
        for group in (self.banks, self.foods, self.obstacles, self.shots):
            group.draw(self.screen)
        self.look.draw_shark(self.screen, self.shark)
        self.particles.draw(self.screen)
        self.enhancer.render_effects()

    def draw_title(self, now):
        self.draw_world()
        screen = self.screen
        y = 95
        for line in self.title_lines:
            screen.blit(line, line.get_rect(midtop=(400, y)))
            y += line.get_height() - 6
        if now // BLINK_MS % 2 == 0:
            prompt = _outlined(self.font, "PRESS ANY KEY TO START", PROMPT_COLOR, (0, 0, 0), 2)
            screen.blit(prompt, prompt.get_rect(center=(400, 400)))
        hint = _outlined(self.small, "S: SETTINGS   1-5: JUMP TO A BOSS   F11: FULL SCREEN   ESC: QUIT", (225, 235, 240), (0, 0, 0), 2)
        screen.blit(hint, hint.get_rect(center=(400, 565)))


def _power_up_rows():
    fish = SmallFish(0, 0).image
    return [
        (fish, "Fish", "+20 energy. You burn energy just by swimming, so keep eating"),
        (LaserPowerup(0, 0).image, "Laser cell", "+30 laser power. The laser also recharges slowly"),
        (MissilePowerup(0, 0).image, "Missiles", "+2 missiles (hold 3). Blow up anything in one hit"),
        (TorpedoPowerup(0, 0).image, "Torpedo", "+1 torpedo (hold 3). Homes in on the nearest target"),
        (ShieldPowerup(0, 0).image, "Shield", "Takes damage in place of your energy until it breaks"),
    ]


def _weapon_rows():
    return [
        (weapon_icon('fan'), "Fan laser", "A wide spread of shots. Great against swarms"),
        (weapon_icon('chum'), "Chum Cannon", "Sprays red plasma balls across a huge 116-degree arc"),
        (weapon_icon('rapid'), "Rapid laser", "Fires much faster, and empties your laser much faster"),
        (weapon_icon('beam'), "Piercing beam", "A slow, heavy shot that passes through everything"),
    ]


def _hazard_rows():
    whirlpool = pygame.transform.smoothscale(_whirlpool_art()[0], (40, 40))
    whirlpool.fill((80, 90, 100), special_flags=pygame.BLEND_RGB_ADD)  # Stands out on the dark panel
    shark_rect = pygame.Rect(0, 0, 1, 1)
    return [
        (RadiationBarrel(0, 0).image, "Radiation barrel", "Shoot it before it leaks. Clouds go right through your shield"),
        (RadioactivePiranha(0, 0, shark_rect).image, "Radioactive piranha", "They chase you, and leave radiation behind when killed"),
        (ZombieFish(0, 0).image, "Zombie fish", "Grey with red crosses for eyes. Don't eat it: it bites!"),
        (EmpJellyfish(0, 0).image, "EMP jellyfish", "Its sting knocks out your laser for 2 seconds"),
        (whirlpool, "Whirlpool", "Drags you in, and its core hurts. Swim hard to escape"),
    ]


class Briefing:
    def __init__(self, screen, keymap):
        self.screen = screen
        self.keymap = keymap
        self.name_font = pygame.font.SysFont(None, 30)
        self.text_font = pygame.font.SysFont(None, 24)
        title_font = pygame.font.SysFont(None, 56)
        self.pages = [
            (_outlined(title_font, "POWER-UPS", PROMPT_COLOR, (0, 0, 0), 2), _power_up_rows(),
             ["Watch for the tuna's flashing charge and the manta's red aiming line!"]),
            (_outlined(title_font, "WEAPONS", PROMPT_COLOR, (0, 0, 0), 2), _weapon_rows(),
             ["Grab the same letter to power up, to level 3. A new letter swaps weapon.",
              "Taking a hit costs a level. Destroying 5 obstacles earns one."]),
            (_outlined(title_font, "HAZARDS", PROMPT_COLOR, (0, 0, 0), 2), _hazard_rows(), []),
        ]
        self.page = 0
        self.elapsed = 0

    @property
    def finished(self):
        return self.page >= len(self.pages)

    def next_page(self):
        self.page += 1
        self.elapsed = 0

    def _key(self, action):
        return pygame.key.name(self.keymap[action]).upper()

    def draw(self, dt):
        self.elapsed += dt
        if self.elapsed >= BRIEFING_MS:
            self.next_page()
        if self.finished:
            return
        title, rows, notes = self.pages[self.page]
        screen = self.screen
        panel = pygame.Surface((740, 510), pygame.SRCALPHA)
        panel.fill((6, 18, 36, 225))
        screen.blit(panel, (30, 45))
        screen.blit(title, title.get_rect(midtop=(400, 58)))
        y = 118
        for icon, name, text in rows:
            screen.blit(icon, icon.get_rect(center=(90, y + 20)))
            screen.blit(self.name_font.render(name, True, (255, 255, 255)), (135, y))
            screen.blit(self.text_font.render(text, True, (190, 215, 230)), (135, y + 24))
            y += 58
        controls = (f"{self._key('fire')}: laser     {self._key('missile')}: missile     "
                    f"{self._key('torpedo')}: torpedo     {self._key('pause')}: pause")
        for line in notes + [controls]:
            image = self.text_font.render(line, True, PROMPT_COLOR)
            screen.blit(image, image.get_rect(center=(400, y + 10)))
            y += 28
        words = "Press any key to dive in" if self.page == len(self.pages) - 1 else "Press any key for more"
        prompt = self.text_font.render(words, True, (255, 255, 255))
        screen.blit(prompt, prompt.get_rect(center=(400, 518)))
        share = max(0, 1 - self.elapsed / BRIEFING_MS)  # Time left on this page
        pygame.draw.rect(screen, PROMPT_COLOR, (200, 536, int(400 * share), 6), border_radius=3)
