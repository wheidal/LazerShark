"""
The story scenes: the intro, and the shark's revenge. Everything is drawn in code. Any key moves on
to the next beat, so nobody is ever stuck watching.
"""
import math
import random

import pygame

from food import SmallFish
from shark_look import SharkLook
from story import _portrait

W, H = 800, 600
BLOOD = [(170, 10, 16), (210, 24, 24), (120, 6, 12)]
GUARD_COUNT = 8
GUARD_STEPS_MS = 520


def _font(size):
    return pygame.font.SysFont(None, size)


def _caption(screen, text, y=540, size=38, color=(255, 240, 200)):
    font = _font(size)
    image = font.render(text, True, color)
    rect = image.get_rect(center=(W // 2, y))
    backing = pygame.Surface((rect.width + 36, rect.height + 16), pygame.SRCALPHA)
    backing.fill((0, 0, 0, 175))
    screen.blit(backing, backing.get_rect(center=rect.center))
    screen.blit(image, rect)


def _big_text(screen, text, center, size, color):
    font = _font(size)
    edge = font.render(text, True, (20, 4, 6))
    face = font.render(text, True, color)
    rect = face.get_rect(center=center)
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
        screen.blit(edge, rect.move(dx, dy))
    screen.blit(face, rect)


def _dressed_shark(shark_image, scale=1.0):
    surface = pygame.Surface(shark_image.get_size(), pygame.SRCALPHA)
    look = SharkLook()

    class Holder:
        image = shark_image
        rect = shark_image.get_rect()

    look.draw_shark(surface, Holder)
    if scale != 1.0:
        surface = pygame.transform.scale(surface, (int(surface.get_width() * scale), int(surface.get_height() * scale)))
    return surface


def _lab_room(screen, t, alarm=True):
    screen.fill((16, 26, 34))
    for x in range(0, W, 80):
        pygame.draw.line(screen, (28, 42, 52), (x, 0), (x, H))
    for y in range(0, H, 80):
        pygame.draw.line(screen, (28, 42, 52), (0, y), (W, y))
    for x in (40, 200, 600, 760):
        pygame.draw.rect(screen, (40, 54, 66), (x - 22, 0, 44, 90), border_radius=6)
        pygame.draw.rect(screen, (90, 255, 170), (x - 12, 12, 24, 62), border_radius=5)
    pygame.draw.rect(screen, (70, 80, 92), (0, 90, W, 10))
    if alarm and int(t / 280) % 2:
        flash = pygame.Surface((W, H), pygame.SRCALPHA)
        flash.fill((255, 0, 0, 40))
        screen.blit(flash, (0, 0))


class Gibs:
    """Everything that flies apart."""

    def __init__(self, rng):
        self.rng = rng
        self.bits = []
        self.stains = []

    def burst(self, center, count=26, speed=0.42, extra=(), life=(500, 1300)):
        for _ in range(count):
            angle = self.rng.uniform(0, math.tau)
            pace = self.rng.uniform(0.06, speed)
            self.bits.append({'pos': list(center), 'vel': [math.cos(angle) * pace, math.sin(angle) * pace],
                              'size': self.rng.randint(2, 7), 'color': self.rng.choice(BLOOD), 'life': self.rng.randint(*life)})
        for image in extra:
            angle = self.rng.uniform(0, math.tau)
            self.bits.append({'pos': list(center), 'vel': [math.cos(angle) * 0.2, math.sin(angle) * 0.2 - 0.1],
                              'image': image, 'life': 3500, 'spin': self.rng.uniform(-0.3, 0.3), 'angle': 0})
        for _ in range(6):
            self.stains.append((center[0] + self.rng.randint(-46, 46), center[1] + self.rng.randint(-34, 40),
                                self.rng.randint(7, 19)))

    def update_and_draw(self, screen, dt):
        for stain in self.stains:
            pygame.draw.circle(screen, BLOOD[2], stain[:2], stain[2])
        for bit in self.bits:
            bit['life'] -= dt
            bit['pos'][0] += bit['vel'][0] * dt
            bit['pos'][1] += bit['vel'][1] * dt
            bit['vel'][1] += 0.00035 * dt  # Slowly sinking
            if 'image' in bit:
                bit['angle'] += bit['spin'] * dt
                image = pygame.transform.rotate(bit['image'], bit['angle'])
                screen.blit(image, image.get_rect(center=bit['pos']))
            elif bit['life'] > 0:
                pygame.draw.circle(screen, bit['color'], bit['pos'], bit['size'])
        self.bits = [bit for bit in self.bits if bit['life'] > 0]


def _guard_art():
    image = pygame.Surface((36, 44), pygame.SRCALPHA)
    pygame.draw.rect(image, (40, 60, 120), (8, 14, 20, 24), border_radius=4)
    pygame.draw.circle(image, (232, 196, 164), (18, 12), 9)
    pygame.draw.rect(image, (28, 36, 70), (9, 2, 18, 7), border_radius=3)
    pygame.draw.rect(image, (70, 74, 84), (24, 22, 12, 5))
    pygame.draw.rect(image, (40, 60, 120), (10, 36, 6, 8))
    pygame.draw.rect(image, (40, 60, 120), (20, 36, 6, 8))
    return image


def _limb():
    image = pygame.Surface((22, 10), pygame.SRCALPHA)
    pygame.draw.rect(image, (40, 60, 120), (0, 1, 15, 8), border_radius=3)
    pygame.draw.circle(image, (232, 196, 164), (17, 5), 4)
    pygame.draw.rect(image, BLOOD[1], (0, 1, 3, 8))
    return image


def _rask_tank(scale=2.6, cracked=True):
    from bosses import DrRask
    image = DrRask._tank_art(cracked)[0]
    return pygame.transform.scale(image, (int(image.get_width() * scale), int(image.get_height() * scale)))


def _rask_bits():
    glasses = pygame.Surface((36, 16), pygame.SRCALPHA)
    for x in (9, 27):
        pygame.draw.circle(glasses, (250, 250, 250), (x, 8), 7)
        pygame.draw.circle(glasses, (20, 20, 30), (x, 8), 7, 2)
    coat = pygame.Surface((30, 26), pygame.SRCALPHA)
    pygame.draw.polygon(coat, (240, 240, 240), [(2, 2), (28, 6), (22, 24), (6, 20)])
    pygame.draw.circle(coat, BLOOD[1], (19, 15), 6)
    shoe = pygame.Surface((26, 14), pygame.SRCALPHA)
    pygame.draw.ellipse(shoe, (34, 26, 22), (0, 2, 26, 12))
    return [glasses, coat, shoe, _limb()]


def _security_scene(shark, gibs, sounds):
    guards = [(90 + i * 88, 150 + (i % 2) * 74) for i in range(GUARD_COUNT)]
    image = _guard_art()
    state = {'killed': 0, 'beam': 0, 'target': None}

    def draw(screen, t, dt):
        _lab_room(screen, t)
        goal_index = min(GUARD_COUNT - 1, state['killed'])
        goal = guards[goal_index][0]
        shark_x = 400 + math.sin(t * 0.004) * 40 + (goal - 400) * 0.6
        if t > (state['killed'] + 1) * GUARD_STEPS_MS and state['killed'] < GUARD_COUNT:
            target = guards[state['killed']]
            state['killed'] += 1
            state['target'] = target
            state['beam'] = 110
            gibs.burst(target, extra=[_limb()])
            sounds['splat'].play()
            sounds['beam'].play()
        for i, spot in enumerate(guards[state['killed']:], start=state['killed']):
            screen.blit(image, image.get_rect(center=(spot[0] + math.sin(t * 0.01 + i) * 3, spot[1])))
        gibs.update_and_draw(screen, dt)
        center = (shark_x, 470)
        if state['beam'] > 0:
            state['beam'] -= dt
            pygame.draw.line(screen, (255, 90, 90), (shark_x, 420), state['target'], 7)
            pygame.draw.line(screen, (255, 255, 255), (shark_x, 420), state['target'], 3)
        screen.blit(shark, shark.get_rect(center=center))
        _caption(screen, f"LAB SECURITY: {GUARD_COUNT - state['killed']} REMAINING", 40, 34, (255, 120, 110))
    return draw, (GUARD_COUNT + 2) * GUARD_STEPS_MS


def _begging_scene(shark_big, sounds):
    tank = _rask_tank()
    state = {'spoken': False}

    def draw(screen, t, dt):
        _lab_room(screen, t)
        shake = math.sin(t * 0.05) * 3
        screen.blit(tank, tank.get_rect(center=(400 + shake, 200)))
        rise = 760 - min(1, t / 2800) * 300
        screen.blit(shark_big, shark_big.get_rect(center=(400, rise)))
        if not state['spoken'] and t > 300:
            state['spoken'] = True
            sounds['scream'].play()
        line = "Wait! WAIT! I MADE you!" if t < 1800 else "Good shark! GOOD SHARK!"
        _caption(screen, line, 40, 42)
    return draw, 3400


def _chomp_scene(gibs, sounds):
    tank = _rask_tank(2.6)
    state = {'bitten': False, 'burp': False, 'cloud': 0}

    def jaws(screen, gap):
        for top in (True, False):
            y = (300 - gap) if top else (300 + gap)
            points = [(0, 0 if top else H), (W, 0 if top else H), (W, y)]
            for i in range(11, 0, -1):  # Down the row of teeth
                x = i * W / 11
                points += [(x - W / 22, y + (46 if top else -46)), (x - W / 11, y)]
            pygame.draw.polygon(screen, (92, 104, 134), points)
            for i in range(11):
                x = i * W / 11
                pygame.draw.polygon(screen, (246, 242, 226), [(x, y), (x + W / 11, y), (x + W / 22, y + (46 if top else -46))])

    def draw(screen, t, dt):
        screen.fill((14, 40, 60))
        closes = 900
        if t < closes:
            screen.blit(tank, tank.get_rect(center=(400, 300)))
            gap = 300 - 290 * (t / closes) ** 2
            jaws(screen, gap)
            return
        if not state['bitten']:
            state['bitten'] = True
            sounds['chomp'].play()
            sounds['splat'].play()
            gibs.burst((400, 300), 220, 0.5, extra=_rask_bits(), life=(1500, 4200))
        state['cloud'] = min(1, state['cloud'] + dt / 1200)
        red = pygame.Surface((W, H), pygame.SRCALPHA)
        red.fill((150, 8, 14, int(190 * state['cloud'])))
        screen.blit(red, (0, 0))
        gibs.update_and_draw(screen, dt)
        if t < closes + 500:
            jaws(screen, 8 + (t - closes) * 0.5)
        if t > closes + 1400:
            _big_text(screen, "CHOMP.", (400, 170), 120, (255, 235, 200))
        if t > closes + 2900:
            if not state['burp']:
                state['burp'] = True
                sounds['burp'].play()
            _big_text(screen, "*burp*", (400, 420), 60, (255, 200, 170))
    return draw, 5400


def _escape_scene(shark, sounds, rng):
    state = {'blasts': 0}

    def draw(screen, t, dt):
        screen.fill((10, 24, 46))
        for i in range(9):  # The lab, going up
            x = 60 + i * 86
            height = 110 + (i * 37) % 70 - min(120, t * 0.03)
            pygame.draw.rect(screen, (40, 46, 56), (x, H - height, 70, height))
        if t // 300 > state['blasts'] and t < 3600:
            state['blasts'] += 1
            sounds['blast'].play()
        for i in range(state['blasts']):
            age = t - i * 300
            if 0 < age < 900:
                spot = (80 + (i * 173) % 640, 460 + (i * 71) % 110)
                radius = int(age * 0.14)
                pygame.draw.circle(screen, (255, 120, 30), spot, radius)
                pygame.draw.circle(screen, (255, 230, 130), spot, radius // 2)
        travel = min(1, t / 3800)
        small = pygame.transform.scale(shark, (int(shark.get_width() * (1 - travel * 0.65)),
                                               int(shark.get_height() * (1 - travel * 0.65))))
        screen.blit(small, small.get_rect(center=(400, 430 - travel * 300)))
        if t > 2000:
            _big_text(screen, "KILL! KILL!", (400, 300), 110, (255, 70, 50))
    return draw, 5000


def _credits_scene(score):
    lines = [("LAZER SHARK KILL! KILL!", 64, (255, 225, 90)), ("", 20, None),
             ("Subject 13  ...  free", 34, (225, 235, 240)),
             ("Dr. Rask  ...  eaten", 34, (225, 235, 240)),
             ("Lab security  ...  also eaten", 34, (225, 235, 240)),
             ("Kevin the eel  ...  avenged?", 34, (225, 235, 240)), ("", 20, None),
             (f"FINAL SCORE  {score}", 54, (255, 120, 110))]

    def draw(screen, t, dt):
        screen.fill((4, 12, 26))
        y = 110
        for text, size, color in lines:
            if text:
                image = _font(size).render(text, True, color)
                screen.blit(image, image.get_rect(center=(W // 2, y)))
            y += size + 16
    return draw, 6500


def _gag_scene(shark):
    fish = [SmallFish(0, 0).image for _ in range(5)]
    mounted = []
    for image in fish:
        image = pygame.transform.scale(image.copy(), (78, 42))
        pygame.draw.rect(image, (150, 160, 172), (26, 2, 20, 8))
        pygame.draw.rect(image, (255, 70, 60), (20, 4, 8, 4))
        mounted.append(image)

    def draw(screen, t, dt):
        _lab_room(screen, t, alarm=False)
        pygame.draw.rect(screen, (70, 80, 92), (80, 340, 640, 70), border_radius=6)
        for x in range(120, 700, 90):
            pygame.draw.rect(screen, (40, 50, 62), (x, 352, 70, 44))
            pygame.draw.rect(screen, (90, 255, 170), (x + 8, 360, 20 + (x + t // 90) % 40, 6))
        screen.blit(shark, shark.get_rect(center=(400, 470)))
        for i, image in enumerate(mounted):
            screen.blit(image, image.get_rect(center=(160 + i * 120, 200 + math.sin(t * 0.004 + i) * 10)))
        _caption(screen, "MEANWHILE, IN THE LAB...", 40)
        if t > 1200:
            _caption(screen, "Project: LAZER FISH. Subject 13 is hiring.", 110, 34, (120, 255, 170))
    return draw, 5500


def run_beats(screen, clock, beats, music):
    """Play each (draw, length) in turn. Returns as soon as the last one ends."""
    in_story = True
    for draw, length in beats:
        elapsed = 0
        while elapsed < length:
            dt = clock.tick(60)
            elapsed += dt
            draw(screen, elapsed, dt)
            pygame.display.flip()
            music.update(dt)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif event.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN):
                    elapsed = length
    pygame.event.clear()
    return in_story


def _intro_beats(shark):
    portrait = pygame.transform.scale(_portrait(), (150, 150))
    sparks = random.Random(4)

    def captured(screen, t, dt):
        screen.fill((14, 54, 88))
        screen.blit(shark, shark.get_rect(center=(400, 280)))
        for x in range(170, 640, 34):
            pygame.draw.line(screen, (190, 170, 120), (x, 130), (x + 40, 440), 2)
            pygame.draw.line(screen, (190, 170, 120), (x + 40, 130), (x, 440), 2)
        _caption(screen, "It was just a shark, minding its own business.")

    def operated(screen, t, dt):
        _lab_room(screen, 0, alarm=False)
        pygame.draw.rect(screen, (92, 100, 112), (240, 200, 320, 260), border_radius=10)
        screen.blit(shark, shark.get_rect(center=(400, 320)))
        screen.blit(portrait, (40, 170))
        for _ in range(7):
            spot = (400 + sparks.randint(-16, 16), 270 + sparks.randint(-16, 16))
            pygame.draw.circle(screen, (255, 240, 130), spot, sparks.randint(1, 4))
        _caption(screen, "Then Dr. Rask bolted a laser to its head.")

    def broke_out(screen, t, dt):
        _lab_room(screen, t)
        y = 300 - t * 0.04
        pygame.draw.line(screen, (255, 90, 90), (400, y - 40), (400, 0), 7)
        pygame.draw.line(screen, (255, 255, 255), (400, y - 40), (400, 0), 3)
        screen.blit(shark, shark.get_rect(center=(400, y + 60)))
        _big_text(screen, "BIG MISTAKE.", (400, 470), 90, (255, 90, 70))
    return [(captured, 3000), (operated, 3200), (broke_out, 2600)]


def play_intro(screen, clock, music, shark_image):
    run_beats(screen, clock, _intro_beats(_dressed_shark(shark_image, 1.8)), music)


def play_ending(screen, clock, music, shark_image, score, sounds):
    music.play('victory')
    rng = random.Random(13)
    gibs = Gibs(rng)
    shark = _dressed_shark(shark_image, 1.1)
    beats = [_security_scene(shark, gibs, sounds), _begging_scene(_dressed_shark(shark_image, 3.4), sounds),
             _chomp_scene(Gibs(rng), sounds), _escape_scene(_dressed_shark(shark_image, 1.6), sounds, rng),
             _credits_scene(score), _gag_scene(_dressed_shark(shark_image, 1.3))]
    run_beats(screen, clock, beats, music)
