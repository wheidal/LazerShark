"""
Obstacles and collision logic.
"""
import pygame
import random
import math


class CoralReef(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		w, h = 80, 44
		self.image = pygame.Surface((w, h), pygame.SRCALPHA)

		# ── Seabed base ──────────────────────────────────────────────────────
		pygame.draw.ellipse(self.image, (145, 118, 72), (0, h - 14, w, 14))
		pygame.draw.ellipse(self.image, (170, 140, 88), (2, h - 14, w - 4, 9))

		# ── Brain coral (left) ───────────────────────────────────────────────
		# Outer dome (shadow)
		pygame.draw.ellipse(self.image, (175, 108, 62), (2, 18, 28, 20))
		# Main dome
		pygame.draw.ellipse(self.image, (212, 138, 82), (3, 16, 26, 18))
		# Convolution bumps
		for bx, by in [(8, 22), (13, 17), (18, 22), (11, 27), (17, 27), (7, 30)]:
			pygame.draw.circle(self.image, (232, 158, 98), (bx, by), 4)
			pygame.draw.circle(self.image, (188, 112, 62), (bx, by), 4, 1)
		# Top specular
		pygame.draw.ellipse(self.image, (245, 180, 120), (7, 17, 11, 6))

		# ── Staghorn coral (centre) ──────────────────────────────────────────
		trunk  = (228, 208, 172)
		shadow = (182, 158, 122)
		tip    = (255, 248, 232)
		# Trunk
		pygame.draw.line(self.image, shadow, (41, h - 14), (40, 20), 4)
		pygame.draw.line(self.image, trunk,  (40, h - 14), (39, 20), 3)
		# Left main branch
		pygame.draw.line(self.image, shadow, (40, 24), (27, 8), 3)
		pygame.draw.line(self.image, trunk,  (39, 24), (26, 8), 2)
		pygame.draw.circle(self.image, tip, (25, 7), 3)
		# Left sub-branch
		pygame.draw.line(self.image, trunk, (34, 16), (22, 6), 2)
		pygame.draw.circle(self.image, tip, (21, 5), 2)
		# Right main branch
		pygame.draw.line(self.image, shadow, (40, 22), (54, 6), 3)
		pygame.draw.line(self.image, trunk,  (39, 22), (53, 6), 2)
		pygame.draw.circle(self.image, tip, (53, 5), 3)
		# Right sub-branch
		pygame.draw.line(self.image, trunk, (46, 15), (58, 4), 2)
		pygame.draw.circle(self.image, tip, (58, 3), 2)
		# Trunk tip
		pygame.draw.circle(self.image, tip, (39, 19), 3)

		# ── Boulder coral (right) ────────────────────────────────────────────
		pygame.draw.ellipse(self.image, (225, 118, 46), (52, 20, 26, 18))
		pygame.draw.ellipse(self.image, (252, 148, 68), (53, 18, 24, 16))
		pygame.draw.ellipse(self.image, (255, 188, 112), (56, 19, 14, 8))
		# Surface convolution arcs
		pygame.draw.arc(self.image, (200, 98, 36), (54, 22, 14, 8), 0, math.pi, 1)
		pygame.draw.arc(self.image, (200, 98, 36), (56, 28, 10, 6), 0, math.pi, 1)

		# ── Sea anemones along base ───────────────────────────────────────────
		for ax, ay in [(14, h - 9), (30, h - 8), (48, h - 10), (62, h - 9), (74, h - 8)]:
			for j in range(6):
				angle = j * 60
				tx = ax + int(4 * math.cos(math.radians(angle)))
				ty = ay + int(4 * math.sin(math.radians(angle)))
				pygame.draw.line(self.image, (255, 100, 148), (ax, ay), (tx, ty), 1)
			pygame.draw.circle(self.image, (255, 168, 192), (ax, ay), 2)

		# ── Scattered polyp dots ──────────────────────────────────────────────
		for _ in range(14):
			px = random.randint(2, w - 2)
			py = random.randint(h - 13, h - 3)
			c  = random.choice([(255, 178, 78), (255, 118, 58), (182, 242, 182)])
			pygame.draw.circle(self.image, c, (px, py), 1)

		self.rect = self.image.get_rect(midtop=(x, y))
		self.hits = 0
		self.name = "Coral Reef"


class Shipwreck(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		w, h = 90, 46
		self.image = pygame.Surface((w, h), pygame.SRCALPHA)

		# ── Sandy sediment base ───────────────────────────────────────────────
		pygame.draw.ellipse(self.image, (158, 132, 85), (4, h - 12, w - 8, 12))
		pygame.draw.ellipse(self.image, (180, 152, 102), (4, h - 12, w - 8, 7))

		# ── Hull (layered for depth) ──────────────────────────────────────────
		hull_shadow = [(10, 12), (80, 12), (86, 28), (75, h - 12), (15, h - 12), (4, 28)]
		hull_main   = [(11, 11), (79, 11), (85, 27), (74, h - 13), (16, h - 13), (5, 27)]
		hull_top    = [(11, 11), (79, 11), (83, 20), (7, 20)]
		pygame.draw.polygon(self.image, (65, 38, 13), hull_shadow)
		pygame.draw.polygon(self.image, (96, 58, 20), hull_main)
		pygame.draw.polygon(self.image, (130, 82, 32), hull_top)

		# ── Waterline band ────────────────────────────────────────────────────
		pygame.draw.line(self.image, (52, 74, 44), (10, 21), (80, 21), 2)

		# ── Portholes ─────────────────────────────────────────────────────────
		for px in [26, 45, 64]:
			pygame.draw.circle(self.image, (32, 18, 6),  (px, 30), 5)   # surround
			pygame.draw.circle(self.image, (16, 8,  2),  (px, 30), 3)   # dark interior
			pygame.draw.circle(self.image, (56, 36, 14), (px, 30), 5, 1) # rim
			pygame.draw.circle(self.image, (76, 98, 118), (px - 1, 28), 2) # glass glint

		# ── Superstructure (cabin) ────────────────────────────────────────────
		pygame.draw.rect(self.image, (78, 48, 16), (28, 5, 34, 9))
		pygame.draw.rect(self.image, (106, 66, 26), (29, 4, 32, 7))
		pygame.draw.rect(self.image, (130, 88, 40), (30, 4, 22, 3))
		for wx in [33, 42, 51]:
			pygame.draw.rect(self.image, (16, 8,  2),  (wx, 6, 4, 4))  # window dark
			pygame.draw.rect(self.image, (58, 80, 100), (wx, 6, 3, 3)) # window glint

		# ── Broken mast ───────────────────────────────────────────────────────
		pygame.draw.line(self.image, (70, 44, 15), (48, 4), (55, -2), 3)
		pygame.draw.line(self.image, (94, 60, 24), (47, 4), (54, -2), 2)
		# Fallen spar
		pygame.draw.line(self.image, (70, 44, 15), (32, 8), (50, 4), 2)

		# ── Rust streaks ─────────────────────────────────────────────────────
		for rx, ry in [(22, 12), (44, 12), (66, 12), (33, 21), (57, 21)]:
			pygame.draw.line(self.image, (162, 80, 22, 108),
							 (rx, ry), (rx + random.randint(-1, 1), ry + 9), 2)

		# ── Hull damage holes ─────────────────────────────────────────────────
		for hx, hy, hr in [(20, 30, 4), (56, 34, 3), (74, 27, 3)]:
			pygame.draw.circle(self.image, (26, 14, 4), (hx, hy), hr)
			pygame.draw.circle(self.image, (10, 4,  1), (hx, hy), hr - 1)
			pygame.draw.circle(self.image, (56, 34, 12), (hx, hy), hr, 1)

		# ── Structural cracks ─────────────────────────────────────────────────
		pygame.draw.line(self.image, (46, 26, 7), (34, 12), (38, 29), 1)
		pygame.draw.line(self.image, (46, 26, 7), (60, 12), (56, 30), 1)

		# ── Barnacles ────────────────────────────────────────────────────────
		for _ in range(14):
			bx = random.randint(10, 82)
			by = random.randint(24, h - 14)
			pygame.draw.circle(self.image, (176, 172, 154), (bx, by), 2)
			pygame.draw.circle(self.image, (146, 142, 126), (bx, by), 1)

		# ── Algae growth ──────────────────────────────────────────────────────
		for gx in [12, 22, 52, 70, 82]:
			gh = random.randint(5, 11)
			pygame.draw.line(self.image, (42, 88, 38),
							 (gx, h - 12), (gx + random.randint(-2, 2), h - 12 - gh), 2)

		# ── Hull rivets ───────────────────────────────────────────────────────
		for rx in range(18, 78, 12):
			pygame.draw.circle(self.image, (70, 42, 14), (rx, 14), 2)
			pygame.draw.circle(self.image, (106, 66, 26), (rx - 1, 13), 1)

		self.rect = self.image.get_rect(midtop=(x, y))
		self.name = "Shipwreck"
		self.hits = 0


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
