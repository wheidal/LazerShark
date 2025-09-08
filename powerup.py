
import pygame

class ShieldPowerup(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		self.image = pygame.Surface((18, 18), pygame.SRCALPHA)
		font = pygame.font.SysFont(None, 24)
		text = font.render('S', True, (0, 255, 128))
		self.image.blit(text, (4, 0))
		self.rect = self.image.get_rect(center=(x, y))

"""
Powerup logic and effects.
Laser energy, missile, torpedo powerups, and friendly submarine supply drop.
"""

class LaserPowerup(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
		pygame.draw.circle(self.image, (255, 0, 0), (8, 8), 7)
		self.rect = self.image.get_rect(center=(x, y))

class MissilePowerup(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
		pygame.draw.rect(self.image, (255, 128, 0), (2, 2, 12, 12))
		self.rect = self.image.get_rect(center=(x, y))

class TorpedoPowerup(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
		pygame.draw.ellipse(self.image, (0, 255, 255), (2, 4, 12, 8))
		self.rect = self.image.get_rect(center=(x, y))

class FriendlySubmarine(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		self.image = pygame.Surface((60, 27), pygame.SRCALPHA)
		pygame.draw.ellipse(self.image, (100, 100, 200), (0, 0, 60, 27))
		pygame.draw.rect(self.image, (200, 200, 255), (15, 9, 30, 9))
		self.rect = self.image.get_rect(center=(x, y))
		self.drop_timer = 0
	def update(self, *args, **kwargs):
		self.rect.y += 2
		self.drop_timer += 1
		# Drop supply every 120 frames (~2 seconds at 60fps)
		if self.drop_timer == 120:
			self.drop_timer = 0
			# Randomly choose a supply to drop
			supply_type = None
			import random
			r = random.randint(0, 2)
			if r == 0:
				supply_type = LaserPowerup(self.rect.centerx, self.rect.bottom)
			elif r == 1:
				supply_type = MissilePowerup(self.rect.centerx, self.rect.bottom)
			else:
				supply_type = TorpedoPowerup(self.rect.centerx, self.rect.bottom)
			return supply_type
		return None
