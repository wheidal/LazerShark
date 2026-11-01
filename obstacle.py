"""
Obstacles and collision logic.
"""
import pygame
import random
import math


SHADOW_OFFSET = (4, 5)
OUTLINE = (14, 22, 34)
_art_cache = {}


def _finish(art, outline=True):
	"""Outline a drawing so it reads as a hazard, and lay a soft shadow on the seabed beneath it."""
	mask = pygame.mask.from_surface(art)
	w, h = art.get_size()
	done = pygame.Surface((w + SHADOW_OFFSET[0], h + SHADOW_OFFSET[1]), pygame.SRCALPHA)
	# Too faint to count in the hit shape, which is taken from solid pixels only
	shadow = mask.to_surface(setcolor=(4, 14, 30, 90), unsetcolor=(0, 0, 0, 0))
	done.blit(shadow, SHADOW_OFFSET)
	done.blit(art, (0, 0))
	if outline:
		for part in mask.connected_components():
			points = part.outline()
			if len(points) > 2:
				pygame.draw.lines(done, OUTLINE, True, points, 2)
	return done


def _cached(key, make):
	"""Art is drawn once and shared: obstacles appear too often to draw each one fresh."""
	if key not in _art_cache:
		_art_cache[key] = make()
	return _art_cache[key]


def _coral_head(variant):
	rng = random.Random(variant)
	art = pygame.Surface((78, 62), pygame.SRCALPHA)
	base = [(232, 120, 96), (238, 164, 84), (206, 110, 164)][variant]
	lobes = [(rng.randint(22, 56), rng.randint(19, 43), rng.randint(11, 18)) for _ in range(6 + variant)]
	for x, y, radius in lobes:
		pygame.draw.circle(art, tuple(int(c * 0.62) for c in base), (x, y), radius)
	for x, y, radius in lobes:
		pygame.draw.circle(art, base, (x - 1, y - 1), radius - 3)
		pygame.draw.circle(art, tuple(min(255, c + 40) for c in base), (x - 3, y - 3), radius // 2)
		# Polyps dot the top of each lobe
		for _ in range(radius):
			angle, reach = rng.uniform(0, math.tau), rng.uniform(0, radius - 4)
			pygame.draw.circle(art, (255, 238, 205),
				(x + math.cos(angle) * reach, y + math.sin(angle) * reach), 1)
	return _finish(art)


class CoralReef(pygame.sprite.Sprite):
	"""A coral head growing up from the seabed, seen from above."""
	WIDTH, HEIGHT = 82, 67
	kind = 'coral'
	name = "Coral Reef"
	toughness = 3
	damage = 33
	reward = 3
	counts_for_rewards = True
	blast_radius = 0
	blast_damage = 0
	drops_pickup = False
	bursts_on_coast = False
	debris_color = (238, 150, 110)

	def __init__(self, x, y):
		super().__init__()
		variant = random.randrange(3)
		self.image = _cached(('coral', variant), lambda: _coral_head(variant))
		self.mask = pygame.mask.from_surface(self.image, 127)
		self.rect = self.image.get_rect(midtop=(x, y))
		self.hits = 0

	@classmethod
	def create(cls, x):
		"""The sprites for one spawn, placed just above the top of the screen."""
		return [cls(x, -cls.HEIGHT)]


def _wreck(angle):
	rng = random.Random(angle)
	art = pygame.Surface((64, 146), pygame.SRCALPHA)
	hull = [(32, 0), (50, 22), (60, 56), (60, 118), (50, 142), (14, 142), (4, 118), (4, 56), (14, 22)]
	deck = [(32, 10), (45, 28), (52, 58), (52, 114), (45, 134), (19, 134), (12, 114), (12, 58), (19, 28)]
	pygame.draw.polygon(art, (84, 54, 42), hull)
	pygame.draw.polygon(art, (146, 104, 70), deck)
	for y in range(30, 132, 8):  # Deck planks
		pygame.draw.line(art, (112, 78, 54), (14, y), (50, y))
	# Superstructure, with the deck stove in behind it
	pygame.draw.rect(art, (108, 112, 104), (21, 48, 22, 28), border_radius=3)
	pygame.draw.rect(art, (64, 70, 72), (25, 53, 14, 9))
	pygame.draw.polygon(art, (22, 26, 34), [(22, 92), (40, 86), (46, 104), (32, 118), (18, 108)])
	# Rust and weed have taken over the old ship
	for _ in range(22):
		pos = (rng.randint(8, 56), rng.randint(20, 136))
		if art.get_at(pos).a:
			color = rng.choice([(164, 86, 44), (74, 122, 78), (96, 138, 86)])
			pygame.draw.circle(art, color, pos, rng.randint(1, 3))
	art = pygame.transform.rotate(art, angle)
	return _finish(art)


class Shipwreck(pygame.sprite.Sprite):
	"""A long hull lying on the seabed. Tough, and takes up more of the channel than coral."""
	WIDTH, HEIGHT = 96, 164
	kind = 'wreck'
	name = "Shipwreck"
	toughness = 5
	damage = 33
	reward = 5
	counts_for_rewards = True
	blast_radius = 0
	blast_damage = 0
	drops_pickup = False
	bursts_on_coast = False
	debris_color = (170, 120, 80)

	def __init__(self, x, y):
		super().__init__()
		angle = random.choice([-12, -6, 6, 12])
		self.image = _cached(('wreck', angle), lambda: _wreck(angle))
		self.mask = pygame.mask.from_surface(self.image, 127)
		self.rect = self.image.get_rect(midtop=(x, y))
		self.hits = 0

	@classmethod
	def create(cls, x):
		return [cls(x, -cls.HEIGHT)]


def _mine(lit):
	art = pygame.Surface((46, 46), pygame.SRCALPHA)
	center = (23, 23)
	for i in range(8):
		angle = i * math.tau / 8
		tip = (23 + math.cos(angle) * 22, 23 + math.sin(angle) * 22)
		pygame.draw.line(art, (92, 98, 104), center, tip, 4)
		pygame.draw.circle(art, (196, 200, 196), tip, 2)
	pygame.draw.circle(art, (46, 52, 60), center, 16)
	pygame.draw.circle(art, (74, 82, 90), (21, 21), 12)
	pygame.draw.circle(art, (112, 120, 126), (18, 18), 5)
	pygame.draw.circle(art, (255, 70, 50) if lit else (120, 30, 30), center, 5)
	if lit:
		pygame.draw.circle(art, (255, 200, 170), center, 2)
	return _finish(art)


class SeaMine(pygame.sprite.Sprite):
	"""Goes off when shot or touched, taking nearby obstacles with it."""
	WIDTH, HEIGHT = 50, 51
	kind = 'mine'
	name = "Sea Mine"
	toughness = 1
	damage = 40
	reward = 3
	counts_for_rewards = True
	blast_radius = 130
	blast_damage = 20  # To a shark caught too close when a mine is shot
	drops_pickup = False
	bursts_on_coast = False
	debris_color = (255, 170, 60)
	BLINK_STEPS = 24

	def __init__(self, x, y):
		super().__init__()
		self.frames = [_cached(('mine', lit), lambda: _mine(lit)) for lit in (False, True)]
		self.image = self.frames[0]
		self.mask = pygame.mask.from_surface(self.image, 127)
		self.rect = self.image.get_rect(midtop=(x, y))
		self.hits = 0
		self.age = random.randrange(self.BLINK_STEPS)

	def update(self):
		self.age += 1
		self.image = self.frames[(self.age // self.BLINK_STEPS) % 2]

	@classmethod
	def create(cls, x):
		return [cls(x, -cls.HEIGHT)]


def _jelly(pulse):
	art = pygame.Surface((30, 40), pygame.SRCALPHA)
	bell_w = 26 if pulse else 22
	left = 15 - bell_w // 2
	for i in range(5):  # Trailing tentacles, on the side away from the bell
		x = left + 3 + i * (bell_w - 6) // 4
		points = [(x + math.sin(y * 0.5 + i) * 2, y) for y in range(16, 39, 3)]
		pygame.draw.lines(art, (232, 178, 232, 200), False, points, 2)
	pygame.draw.ellipse(art, (196, 112, 214, 235), (left, 2, bell_w, 20))
	pygame.draw.ellipse(art, (246, 196, 246, 240), (left + 4, 5, bell_w - 8, 9))
	pygame.draw.ellipse(art, OUTLINE, (left, 2, bell_w, 20), 1)
	return _finish(art, outline=False)


class Jellyfish(pygame.sprite.Sprite):
	"""Drifts from side to side. One sting is mild, but they come in swarms."""
	WIDTH, HEIGHT = 150, 130
	kind = 'jellyfish'
	name = "Jellyfish"
	toughness = 1
	damage = 10
	reward = 1
	counts_for_rewards = False  # Swarms are easy kills, so they mustn't earn shields and upgrades
	blast_radius = 0
	blast_damage = 0
	drops_pickup = False
	bursts_on_coast = False
	debris_color = (230, 170, 235)
	_art = staticmethod(_jelly)
	SWAY = 22
	SWAY_SPEED = 0.03
	PULSE_STEPS = 20

	def __init__(self, x, y):
		super().__init__()
		self.frames = [_cached((self.kind, pulse), lambda: self._art(pulse)) for pulse in (False, True)]
		self.image = self.frames[0]
		self.mask = pygame.mask.from_surface(self.image, 127)
		self.rect = self.image.get_rect(midtop=(x, y))
		self.home_x = x
		self.hits = 0
		self.age = random.randrange(600)

	def update(self):
		self.age += 1
		self.image = self.frames[(self.age // self.PULSE_STEPS) % 2]
		self.rect.centerx = self.home_x + int(math.sin(self.age * self.SWAY_SPEED) * self.SWAY)

	@classmethod
	def create(cls, x):
		"""A swarm. WIDTH and HEIGHT cover all of its members however far they sway."""
		room = cls.WIDTH // 2 - cls.SWAY - 18
		return [cls(x + random.randint(-room, room), -random.randint(45, cls.HEIGHT))
				for _ in range(random.randint(3, 5))]


def _emp_jelly(pulse):
	art = pygame.Surface((36, 46), pygame.SRCALPHA)
	bell_w = 32 if pulse else 27
	left = 18 - bell_w // 2
	for i in range(5):
		x = left + 3 + i * (bell_w - 6) // 4
		points = [(x + (3 if y // 4 % 2 else -3), y) for y in range(18, 45, 4)]  # Jagged, like sparks
		pygame.draw.lines(art, (255, 245, 110), False, points, 2)
	pygame.draw.ellipse(art, (40, 90, 170, 240), (left, 2, bell_w, 22))
	pygame.draw.ellipse(art, (120, 235, 255, 245), (left + 4, 5, bell_w - 8, 11))
	pygame.draw.line(art, (255, 255, 180), (18, 4), (14, 12), 2)
	pygame.draw.line(art, (255, 255, 180), (14, 12), (21, 12), 2)
	pygame.draw.line(art, (255, 255, 180), (21, 12), (17, 21), 2)
	pygame.draw.ellipse(art, OUTLINE, (left, 2, bell_w, 22), 1)
	return _finish(art, outline=False)


class EmpJellyfish(Jellyfish):
	"""Its sting barely hurts, but it knocks out the laser for a moment, even through a shield."""
	kind = 'emp_jelly'
	name = "EMP Jellyfish"
	toughness = 2
	damage = 6
	reward = 2
	debris_color = (140, 235, 255)
	jams_laser_ms = 2000
	_art = staticmethod(_emp_jelly)

	@classmethod
	def create(cls, x):
		return [cls(x + random.randint(-30, 30), -random.randint(60, cls.HEIGHT)) for _ in range(random.randint(1, 2))]


def _barrel(lit):
	art = pygame.Surface((42, 42), pygame.SRCALPHA)
	pygame.draw.circle(art, (120, 100, 30), (21, 21), 20)
	pygame.draw.circle(art, (150, 240, 70) if lit else (232, 196, 50), (21, 21), 17)
	pygame.draw.circle(art, (70, 60, 24), (21, 21), 17, 2)
	for i in range(3):  # The radiation trefoil
		middle = i * math.tau / 3 - math.pi / 2
		points = [(21, 21)]
		for step in range(5):
			angle = middle - 0.5 + step * 0.25
			points.append((21 + math.cos(angle) * 14, 21 + math.sin(angle) * 14))
		pygame.draw.polygon(art, (24, 22, 20), points)
	pygame.draw.circle(art, (232, 196, 50), (21, 21), 4)
	pygame.draw.circle(art, (24, 22, 20), (21, 21), 2)
	return _finish(art)


class RadiationBarrel(pygame.sprite.Sprite):
	"""Blinks green, then cracks and leaks a cloud. Shoot it first and there's no leak."""
	WIDTH, HEIGHT = 48, 48
	kind = 'barrel'
	name = "Radiation Barrel"
	toughness = 1
	damage = 12
	reward = 2
	counts_for_rewards = False
	blast_radius = 0
	blast_damage = 0
	drops_pickup = False
	bursts_on_coast = False
	debris_color = (160, 255, 90)
	LEAK_STEPS = 125
	BLINK_FROM = 60

	def __init__(self, x, y):
		super().__init__()
		self.frames = [_cached(('barrel', lit), lambda: _barrel(lit)) for lit in (False, True)]
		self.image = self.frames[0]
		self.mask = pygame.mask.from_surface(self.image, 127)
		self.rect = self.image.get_rect(midtop=(x, y))
		self.hits = 0
		self.age = 0
		self.leaking = False

	def update(self):
		self.age += 1
		if self.age > self.BLINK_FROM:
			self.image = self.frames[self.age // 8 % 2]
		self.leaking = self.age >= self.LEAK_STEPS

	@classmethod
	def create(cls, x):
		return [cls(x, -cls.HEIGHT)]


OBSTACLE_TYPES = {cls.kind: cls for cls in (CoralReef, Shipwreck, SeaMine, Jellyfish, EmpJellyfish, RadiationBarrel)}


class ReefSegment(pygame.sprite.Sprite):
	"""One contiguous section of a reef wall — independently destructible."""

	_H = 44

	def __init__(self, x: int, w: int):
		super().__init__()
		self.image = pygame.Surface((w, self._H), pygame.SRCALPHA)
		self._draw(w)
		self.rect = self.image.get_rect(topleft=(x, -self._H))
		self.name = "Reef Wall"
		self.hits = 0

	def _draw(self, w: int):
		h = self._H

		# Sandy-rock foundation
		pygame.draw.rect(self.image, (108, 68, 20), (0, h // 2 + 2, w, h // 2))
		pygame.draw.rect(self.image, (146, 94, 36), (0, h // 2 - 2, w, 10))

		# Coral formations spaced ~14 px
		palette = [(255, 120, 55), (255, 178, 75), (218, 158, 96), (200, 95, 38)]
		for bx in range(6, w - 6, 14):
			bh = random.randint(10, 18)
			bc = random.choice(palette)
			cy = h // 2 - bh // 2
			pygame.draw.circle(self.image, bc, (bx, cy), bh // 2 + 2)
			light = tuple(min(255, c + 50) for c in bc)
			pygame.draw.circle(self.image, light, (bx - 1, cy - 1), max(1, bh // 4))
			pygame.draw.line(self.image, (136, 86, 26),
							 (bx, cy + bh // 2 + 1), (bx, h // 2 + 1), 2)

		# Rock texture spots
		for _ in range(max(1, w // 10)):
			rx = random.randint(1, max(1, w - 2))
			ry = random.randint(h // 2 + 8, h - 2)
			rc = random.choice([(86, 52, 14), (116, 72, 26), (76, 46, 12)])
			pygame.draw.circle(self.image, rc, (rx, ry), 2)

		# Anemone tentacles every ~24 px
		for ax in range(12, w - 12, 24):
			for j in range(5):
				angle = j * 72
				tx = ax + int(3 * math.cos(math.radians(angle)))
				ty = h // 2 - 5 + int(3 * math.sin(math.radians(angle)))
				pygame.draw.line(self.image, (255, 100, 148),
								 (ax, h // 2 - 5), (tx, ty), 1)


def create_reef_wall(coverage_ratio: float):
	"""
	Returns a list of ReefSegment sprites forming a full-width reef wall.
	Each segment is independently destructible — shooting one does not
	affect the others.
	"""
	W       = 800
	MIN_GAP = 90  # minimum navigable corridor width (px)

	total_gap = max(MIN_GAP, int(W * (1.0 - coverage_ratio)))

	if coverage_ratio > 0.50 and total_gap >= 2 * MIN_GAP:
		# Two separate corridors once the wall gets dense
		g1  = max(MIN_GAP, int(total_gap * random.uniform(0.4, 0.6)))
		g2  = total_gap - g1
		g1x = random.randint(25, max(25, W // 2 - g1 - 15))
		g2x = random.randint(W // 2 + 15, max(W // 2 + 15, W - g2 - 25))
		gaps = [(g1x, g1), (g2x, g2)]
	else:
		gx   = random.randint(25, max(25, W - total_gap - 25))
		gaps = [(gx, total_gap)]

	# Boolean mask: True = reef, False = navigable gap
	mask = [True] * W
	for gx, gw in gaps:
		for i in range(max(0, gx), min(W, gx + gw)):
			mask[i] = False

	# Find contiguous reef segments
	segments, start = [], None
	for i, filled in enumerate(mask):
		if filled and start is None:
			start = i
		elif not filled and start is not None:
			segments.append((start, i - start))
			start = None
	if start is not None:
		segments.append((start, W - start))

	return [ReefSegment(sx, sw) for sx, sw in segments if sw >= 4]
