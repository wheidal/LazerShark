"""
Food (fish) logic.
Simple food: small fish.
"""
import pygame

class SmallFish(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		self.image = pygame.Surface((24, 14), pygame.SRCALPHA)
		
		# Enhanced small fish with better details and shading
		import random
		
		# Randomize fish color for variety
		fish_colors = [
			[(0, 180, 100), (0, 220, 120), (0, 160, 80)],    # Green fish
			[(200, 150, 0), (240, 180, 0), (180, 130, 0)],   # Gold fish
			[(150, 0, 150), (200, 50, 200), (120, 0, 120)],  # Purple fish
			[(0, 150, 200), (0, 180, 240), (0, 120, 160)],   # Blue fish
		]
		colors = random.choice(fish_colors)
		base_color, highlight_color, shadow_color = colors
		
		# Fish body with gradient effect
		pygame.draw.ellipse(self.image, shadow_color, (1, 2, 16, 10))    # Shadow
		pygame.draw.ellipse(self.image, base_color, (0, 0, 16, 10))      # Main body
		pygame.draw.ellipse(self.image, highlight_color, (2, 2, 12, 6))  # Highlight
		
		# Scale pattern
		scale_color = tuple(max(0, c - 30) for c in base_color)
		for i in range(3):
			x_pos = 4 + i * 4
			pygame.draw.arc(self.image, scale_color, (x_pos, 3, 4, 4), 0, 3.14, 1)
		
		# Eye with detail
		pygame.draw.circle(self.image, (255, 255, 255), (4, 5), 2)  # Eye white
		pygame.draw.circle(self.image, (0, 0, 0), (4, 5), 1)        # Pupil
		pygame.draw.circle(self.image, (200, 200, 255), (4, 4), 1)  # Eye reflection
		
		# Tail fin with better shape
		tail_color = tuple(min(255, c + 20) for c in base_color)
		tail_points = [
			(14, 5),
			(20, 2),
			(22, 4),
			(22, 6),
			(20, 8),
			(14, 5)
		]
		pygame.draw.polygon(self.image, tail_color, tail_points)
		pygame.draw.polygon(self.image, shadow_color, tail_points[1:4])  # Tail shadow
		
		# Fins
		fin_color = tuple(min(255, c + 30) for c in base_color)
		# Top fin
		pygame.draw.polygon(self.image, fin_color, [(6, 0), (8, 0), (10, 3), (7, 3)])
		# Bottom fin
		pygame.draw.polygon(self.image, fin_color, [(6, 10), (8, 10), (9, 7), (7, 7)])
		
		# Gill detail
		gill_color = tuple(max(0, c - 20) for c in base_color)
		pygame.draw.line(self.image, gill_color, (6, 4), (6, 6), 1)
		
		self.rect = self.image.get_rect(midtop=(x, y))
		self.animation_offset = random.random() * 6.28  # Random starting phase for swimming animation
