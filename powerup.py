"""
Powerup logic and effects.
Laser energy and shield powerups.
"""
import pygame
import random
import math


class ShieldPowerup(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		self.image = pygame.Surface((26, 26), pygame.SRCALPHA)
		cx, cy = 13, 13
		r = 11
		pts = [(int(cx + r * math.cos(math.radians(i * 60 - 90))),
				int(cy + r * math.sin(math.radians(i * 60 - 90)))) for i in range(6)]
		glow = [(int(cx + (r + 2) * math.cos(math.radians(i * 60 - 90))),
				 int(cy + (r + 2) * math.sin(math.radians(i * 60 - 90)))) for i in range(6)]
		pygame.draw.polygon(self.image, (0, 255, 140, 50), glow)
		pygame.draw.polygon(self.image, (0, 170, 95), pts)
		# Lighter upper half for 3D feel
		upper = [pts[5], pts[0], pts[1], (cx, cy)]
		pygame.draw.polygon(self.image, (0, 215, 135), upper)
		# Border
		pygame.draw.polygon(self.image, (140, 255, 195), pts, 2)
		# Specular highlight
		pygame.draw.circle(self.image, (210, 255, 235), (cx - 2, cy - 3), 3)
		self.rect = self.image.get_rect(center=(x, y))


class LaserPowerup(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		self.image = pygame.Surface((26, 26), pygame.SRCALPHA)
		cx, cy = 13, 13
		# Outer glow
		pygame.draw.circle(self.image, (255, 80, 0, 55), (cx, cy), 12)
		# Diamond crystal body
		diamond = [(cx, cy - 11), (cx + 7, cy), (cx, cy + 11), (cx - 7, cy)]
		pygame.draw.polygon(self.image, (200, 0, 0), diamond)
		# Right face (lighter)
		pygame.draw.polygon(self.image, (255, 65, 45), [(cx, cy - 11), (cx + 7, cy), (cx, cy)])
		# Left face (warm highlight)
		pygame.draw.polygon(self.image, (255, 145, 75), [(cx - 7, cy), (cx, cy - 11), (cx, cy)])
		# Inner bright core
		core = [(cx, cy - 5), (cx + 3, cy), (cx, cy + 5), (cx - 3, cy)]
		pygame.draw.polygon(self.image, (255, 225, 175), core)
		# Specular dot
		pygame.draw.circle(self.image, (255, 255, 255), (cx - 1, cy - 4), 2)
		# Outline
		pygame.draw.polygon(self.image, (255, 110, 55), diamond, 1)
		self.rect = self.image.get_rect(center=(x, y))
