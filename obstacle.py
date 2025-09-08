"""
Obstacles and collision logic.
Simple obstacles: coral reefs and shipwrecks.
"""
import pygame

class CoralReef(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		self.image = pygame.Surface((72, 36), pygame.SRCALPHA)
		
		# Enhanced coral reef with organic shapes and colors
		# Base reef structure (darker foundation)
		pygame.draw.ellipse(self.image, (180, 80, 20), (0, 18, 72, 18))
		pygame.draw.ellipse(self.image, (200, 100, 40), (4, 16, 64, 16))
		
		# Multiple coral formations with varied colors
		coral_colors = [
			(255, 120, 60),   # Orange coral
			(255, 180, 80),   # Yellow coral  
			(220, 160, 100),  # Brown coral
			(255, 200, 120),  # Light coral
		]
		
		# Large coral formations
		pygame.draw.circle(self.image, coral_colors[0], (18, 24), 12)
		pygame.draw.circle(self.image, coral_colors[1], (18, 22), 8)  # Highlight
		
		pygame.draw.circle(self.image, coral_colors[1], (54, 24), 9)
		pygame.draw.circle(self.image, coral_colors[2], (54, 22), 6)  # Highlight
		
		# Smaller coral polyps
		pygame.draw.circle(self.image, coral_colors[2], (36, 20), 6)
		pygame.draw.circle(self.image, coral_colors[3], (36, 18), 3)
		
		pygame.draw.circle(self.image, coral_colors[0], (8, 28), 4)
		pygame.draw.circle(self.image, coral_colors[3], (64, 26), 5)
		
		# Coral branches (organic tendrils)
		branch_color = (200, 140, 80)
		import random
		for i in range(6):
			start_x = 10 + i * 10
			start_y = 20 + random.randint(-3, 3)
			end_x = start_x + random.randint(-5, 5)
			end_y = start_y - random.randint(3, 8)
			pygame.draw.line(self.image, branch_color, (start_x, start_y), (end_x, end_y), 2)
			
			# Branch tips
			pygame.draw.circle(self.image, coral_colors[random.randint(0, 3)], (end_x, end_y), 2)
		
		# Sea anemone details
		anemone_color = (255, 100, 150)
		for i in range(3):
			center_x = 20 + i * 16
			center_y = 24
			for j in range(6):
				angle = j * 60  # degrees
				import math
				tentacle_x = center_x + int(4 * math.cos(math.radians(angle)))
				tentacle_y = center_y + int(4 * math.sin(math.radians(angle)))
				pygame.draw.line(self.image, anemone_color, (center_x, center_y), (tentacle_x, tentacle_y), 1)
		
		# Texture details (small spots and variations)
		texture_color = (160, 60, 10)
		for i in range(12):
			spot_x = random.randint(5, 67)
			spot_y = random.randint(18, 32)
			pygame.draw.circle(self.image, texture_color, (spot_x, spot_y), 1)
		
		self.rect = self.image.get_rect(midtop=(x, y))
		self.hits = 0
		self.name = "Coral Reef"

class Shipwreck(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		self.image = pygame.Surface((84, 42), pygame.SRCALPHA)
		
		# Enhanced shipwreck with detailed rusted metal and damage
		# Main hull (weathered and rusted)
		hull_colors = [
			(100, 60, 30),  # Dark rust
			(120, 80, 40),  # Medium rust
			(140, 100, 50), # Light rust
			(80, 50, 25),   # Very dark rust
		]
		
		# Main ship body with shading
		pygame.draw.rect(self.image, hull_colors[0], (14, 14, 56, 16))  # Main hull shadow
		pygame.draw.rect(self.image, hull_colors[1], (12, 12, 60, 18))  # Main hull
		pygame.draw.rect(self.image, hull_colors[2], (12, 12, 58, 8))   # Hull top highlight
		
		# Broken deck
		pygame.draw.polygon(self.image, hull_colors[3], [(12, 30), (72, 30), (42, 42)])
		pygame.draw.polygon(self.image, hull_colors[0], [(14, 30), (70, 30), (42, 40)])  # Inner shadow
		
		# Hull damage (holes and cracks)
		damage_color = (40, 25, 15)
		pygame.draw.ellipse(self.image, damage_color, (20, 16, 8, 6))  # Hole 1
		pygame.draw.ellipse(self.image, damage_color, (45, 18, 6, 5))  # Hole 2
		pygame.draw.ellipse(self.image, damage_color, (32, 22, 5, 4))  # Hole 3
		
		# Cracks
		crack_color = (60, 35, 20)
		pygame.draw.line(self.image, crack_color, (25, 14), (28, 28), 1)
		pygame.draw.line(self.image, crack_color, (50, 12), (52, 25), 1)
		pygame.draw.line(self.image, crack_color, (38, 15), (40, 30), 1)
		
		# Mast remnants (broken)
		mast_color = (90, 70, 40)
		pygame.draw.rect(self.image, mast_color, (38, 4, 4, 12))  # Main mast
		pygame.draw.rect(self.image, (70, 50, 30), (39, 4, 2, 12))  # Mast shadow
		
		# Broken rigging
		pygame.draw.line(self.image, (60, 40, 20), (40, 6), (20, 14), 1)
		pygame.draw.line(self.image, (60, 40, 20), (40, 8), (55, 16), 1)
		
		# Barnacles and sea growth
		barnacle_color = (180, 180, 160)
		growth_color = (40, 80, 40)
		
		# Barnacles
		for i in range(8):
			import random
			barn_x = random.randint(15, 65)
			barn_y = random.randint(14, 28)
			pygame.draw.circle(self.image, barnacle_color, (barn_x, barn_y), 2)
			pygame.draw.circle(self.image, (160, 160, 140), (barn_x, barn_y), 1)
		
		# Seaweed/algae growth
		for i in range(5):
			weed_x = random.randint(12, 70)
			weed_y = random.randint(25, 35)
			pygame.draw.line(self.image, growth_color, (weed_x, weed_y), (weed_x, weed_y + 4), 1)
		
		# Rust streaks
		rust_streak = (160, 80, 30, 100)
		pygame.draw.line(self.image, rust_streak, (25, 12), (25, 30), 2)
		pygame.draw.line(self.image, rust_streak, (48, 14), (48, 28), 2)
		pygame.draw.line(self.image, rust_streak, (60, 12), (60, 26), 2)
		
		# Metal rivets detail
		rivet_color = (80, 60, 40)
		for i in range(6):
			rivet_x = 16 + i * 9
			pygame.draw.circle(self.image, rivet_color, (rivet_x, 20), 1)
		
		self.rect = self.image.get_rect(midtop=(x, y))
		self.name = "Shipwreck"
		self.hits = 0
