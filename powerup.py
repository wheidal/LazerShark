"""
Powerup logic and effects.
Laser energy, missile, torpedo and shield powerups.
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


class MissilePowerup(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		self.image = pygame.Surface((14, 30), pygame.SRCALPHA)
		# Nose cone
		pygame.draw.polygon(self.image, (175, 175, 200), [(3, 8), (11, 8), (7, 0)])
		pygame.draw.polygon(self.image, (225, 225, 248), [(4, 8), (10, 8), (7, 2)])
		# Body shadow side
		pygame.draw.rect(self.image, (130, 130, 160), (4, 8, 8, 14))
		# Body highlight side
		pygame.draw.rect(self.image, (195, 195, 218), (3, 8, 6, 14))
		# Fins
		pygame.draw.polygon(self.image, (100, 100, 135), [(1, 20), (3, 17), (3, 24)])
		pygame.draw.polygon(self.image, (100, 100, 135), [(11, 17), (13, 20), (11, 24)])
		# Exhaust flame (outer)
		pygame.draw.ellipse(self.image, (255, 155, 0), (3, 22, 8, 7))
		# Exhaust flame (inner)
		pygame.draw.ellipse(self.image, (255, 228, 95), (5, 23, 4, 4))
		# Panel line
		pygame.draw.line(self.image, (85, 85, 115), (3, 13), (11, 13), 1)
		# Sensor dot
		pygame.draw.rect(self.image, (55, 55, 95), (6, 11, 2, 1))
		self.rect = self.image.get_rect(center=(x, y))


class TorpedoPowerup(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		self.image = pygame.Surface((30, 14), pygame.SRCALPHA)
		# Cylindrical body (shadow)
		pygame.draw.ellipse(self.image, (0, 90, 120), (0, 2, 24, 10))
		# Cylindrical body (highlight)
		pygame.draw.ellipse(self.image, (0, 145, 175), (1, 3, 20, 6))
		# Pointed nose
		pygame.draw.polygon(self.image, (0, 75, 105), [(20, 3), (29, 7), (20, 11)])
		pygame.draw.polygon(self.image, (0, 115, 150), [(21, 4), (27, 7), (21, 10)])
		# Glowing sonar tip
		pygame.draw.circle(self.image, (0, 235, 225), (28, 7), 2)
		pygame.draw.circle(self.image, (175, 255, 255), (28, 7), 1)
		# Rear stabiliser fins
		pygame.draw.polygon(self.image, (0, 65, 95), [(4, 2), (1, 0), (2, 5)])
		pygame.draw.polygon(self.image, (0, 65, 95), [(4, 10), (1, 13), (2, 8)])
		# Propeller hub
		pygame.draw.circle(self.image, (95, 155, 175), (2, 7), 2)
		# Centerline panel
		pygame.draw.line(self.image, (0, 55, 85), (4, 7), (19, 7), 1)
		# Bubble trail
		pygame.draw.circle(self.image, (155, 215, 255, 90), (5, 4), 1)
		pygame.draw.circle(self.image, (155, 215, 255, 70), (3, 9), 1)
		self.rect = self.image.get_rect(center=(x, y))
