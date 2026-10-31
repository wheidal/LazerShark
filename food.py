"""
Food (fish) logic.
Small fish with 4-frame tail-wag swimming animation.
"""
import pygame
import random
import math


class SmallFish(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()

		fish_palettes = [
			[(0, 180, 100),  (0, 220, 120),  (0, 150, 80)],
			[(200, 150, 0),  (240, 180, 0),  (170, 120, 0)],
			[(150, 0, 150),  (200, 50, 200), (120, 0, 120)],
			[(0, 150, 200),  (0, 180, 240),  (0, 120, 160)],
		]
		self._colors = random.choice(fish_palettes)

		self.frames = [self._make_frame(i) for i in range(4)]
		self.frame_index = 0
		self.frame_timer = 0
		self.image = self.frames[0]
		self.rect = self.image.get_rect(midtop=(x, y))

	def _make_frame(self, phase):
		base, highlight, shadow = self._colors
		surf = pygame.Surface((26, 14), pygame.SRCALPHA)

		# Tail sways ±3 px: 0, +3, 0, -3 across the four phases
		sway = int(3 * math.sin(phase * math.pi / 2))

		# Body (shadow layer, then main, then highlight)
		pygame.draw.ellipse(surf, shadow,    (1, 2, 16, 10))
		pygame.draw.ellipse(surf, base,      (0, 1, 16, 10))
		pygame.draw.ellipse(surf, highlight, (2, 3, 11,  6))

		# Scale pattern
		scale_c = tuple(max(0, c - 30) for c in base)
		for i in range(3):
			pygame.draw.arc(surf, scale_c, (4 + i * 4, 3, 4, 4), 0, math.pi, 1)

		# Eye
		pygame.draw.circle(surf, (255, 255, 255), (4, 6), 2)
		pygame.draw.circle(surf, (0,   0,   0),   (4, 6), 1)
		pygame.draw.circle(surf, (200, 200, 255),  (4, 5), 1)

		# Animated tail fin
		tail_c = tuple(min(255, c + 20) for c in base)
		spread = abs(sway) // 2
		tail = [
			(14, 6),
			(20 + sway, 2 - spread),
			(22 + sway, 5),
			(22 + sway, 7),
			(20 + sway, 10 + spread),
		]
		pygame.draw.polygon(surf, tail_c, tail)
		# Shadow on tail
		pygame.draw.polygon(surf, shadow, [tail[1], tail[2], tail[3]])

		# Dorsal fin
		fin_c = tuple(min(255, c + 30) for c in base)
		pygame.draw.polygon(surf, fin_c, [(6, 1), (8, 1), (10, 4), (7, 4)])
		# Pectoral fin
		pygame.draw.polygon(surf, fin_c, [(6, 11), (8, 11), (9,  8), (7, 8)])

		# Gill line
		gill_c = tuple(max(0, c - 20) for c in base)
		pygame.draw.line(surf, gill_c, (7, 5), (7, 8), 1)

		return surf

	def update(self, *args, **kwargs):
		# Advance one animation frame every 8 game ticks (~7.5 fps at 60 fps)
		self.frame_timer += 1
		if self.frame_timer >= 8:
			self.frame_timer = 0
			self.frame_index = (self.frame_index + 1) % 4
			self.image = self.frames[self.frame_index]
