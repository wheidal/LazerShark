"""
Player (Shark) logic and animation.
Temporary shark sprite for prototyping (16x32 px, top-down, simple blue shape).
"""
import pygame
import os

class Shark(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		self.current_frame = 0
		self.images = [self._create_frame(i) for i in range(4)]  # 4-frame swim animation
		self.image = self.images[self.current_frame]
		self.rect = self.image.get_rect(midbottom=(x, y))
		self.frame_timer = 0
		self.frame_rate = 8  # frames per second
		self.speed = 5
		# Weapon attributes
		self.laser_energy = 100  # max 100
		self.missiles = 3
		self.torpedoes = 1
		self.fire_cooldown = 0

	def _create_frame(self, phase):
		import math
		surf = pygame.Surface((48, 72), pygame.SRCALPHA)
		
		# Enhanced shark with gradient shading and better details
		t = phase + self.current_frame
		tail_offset = int(10 * math.sin(t * math.pi / 2))
		fin_offset = int(3 * math.sin(t * math.pi / 3))
		
		# Main body with gradient shading (darker to lighter)
		body_colors = [
			(0, 80, 160),   # Dark blue (top/back)
			(0, 110, 200),  # Medium blue
			(20, 140, 240), # Lighter blue
			(40, 160, 255)  # Lightest blue (belly)
		]
		
		# Draw body with layered ellipses for gradient effect
		for i, color in enumerate(body_colors):
			y_offset = i * 2
			height = 48 - i * 3
			width = 36 - i * 2
			x_pos = 6 + i
			y_pos = 18 + y_offset
			if height > 0 and width > 0:
				pygame.draw.ellipse(surf, color, (x_pos, y_pos, width, height))
		
		# Belly highlight (lighter stripe)
		pygame.draw.ellipse(surf, (60, 180, 255), (12, 35, 24, 20))
		
		# Dorsal fin (animated)
		fin_points = [
			(24, 36 + fin_offset),
			(30 + fin_offset, 18),
			(18 - fin_offset, 18),
			(22, 28)
		]
		pygame.draw.polygon(surf, (0, 60, 120), fin_points)
		pygame.draw.polygon(surf, (0, 80, 140), fin_points[:-1])  # Highlight edge
		
		# Side fins (pectoral fins)
		left_fin = [(8, 42), (2, 48), (8, 52), (14, 48)]
		right_fin = [(40, 42), (46, 48), (40, 52), (34, 48)]
		pygame.draw.polygon(surf, (0, 90, 160), left_fin)
		pygame.draw.polygon(surf, (0, 90, 160), right_fin)
		
		# Gills (detailed lines)
		gill_color = (0, 60, 120)
		for i in range(3):
			x = 10 + i * 3
			pygame.draw.line(surf, gill_color, (x, 32), (x + 2, 36), 2)
			pygame.draw.line(surf, gill_color, (36 - x, 32), (38 - x, 36), 2)
		
		# Enhanced mouth with teeth
		mouth_rect = (15, 12, 18, 12)
		pygame.draw.arc(surf, (255, 255, 255), mouth_rect, math.pi, 0, 3)
		pygame.draw.arc(surf, (220, 0, 0), mouth_rect, math.pi, 0, 2)
		
		# Teeth details
		for i in range(4):
			tooth_x = 17 + i * 3
			pygame.draw.polygon(surf, (255, 255, 255), 
							  [(tooth_x, 15), (tooth_x + 1, 12), (tooth_x + 2, 15)])
		
		# Enhanced eyes with pupils and reflections
		eye_color = (0, 0, 0)
		pupil_color = (40, 40, 40)
		reflection_color = (200, 200, 255)
		
		# Left eye
		pygame.draw.circle(surf, eye_color, (18, 27), 4)
		pygame.draw.circle(surf, pupil_color, (18, 27), 2)
		pygame.draw.circle(surf, reflection_color, (19, 26), 1)
		
		# Right eye
		pygame.draw.circle(surf, eye_color, (30, 27), 4)
		pygame.draw.circle(surf, pupil_color, (30, 27), 2)
		pygame.draw.circle(surf, reflection_color, (31, 26), 1)
		
		# Cybernetic laser harness (enhanced with details)
		harness_color = (255, 0, 0)
		harness_highlight = (255, 100, 100)
		
		# Main harness line
		pygame.draw.line(surf, harness_color, (12, 48), (36, 48), 6)
		pygame.draw.line(surf, harness_highlight, (12, 46), (36, 46), 2)
		
		# Laser emitters
		pygame.draw.circle(surf, harness_color, (15, 48), 3)
		pygame.draw.circle(surf, harness_color, (33, 48), 3)
		pygame.draw.circle(surf, harness_highlight, (15, 48), 1)
		pygame.draw.circle(surf, harness_highlight, (33, 48), 1)
		
		# Tech details on harness
		pygame.draw.rect(surf, (150, 150, 150), (22, 46, 4, 4))
		pygame.draw.rect(surf, (200, 200, 200), (23, 47, 2, 2))
		
		# Animated tail with better shape and shading
		tail_points = [
			(24, 66),
			(24 + tail_offset, 72),
			(24, 72),
			(20, 68)
		]
		pygame.draw.polygon(surf, (0, 100, 180), tail_points)
		
		# Tail fin details
		tail_detail_points = [
			(24, 66),
			(24 + tail_offset - 2, 70),
			(22, 68)
		]
		pygame.draw.polygon(surf, (0, 120, 200), tail_detail_points)
		
		# Battle scars (optional detail)
		scar_color = (0, 40, 80)
		pygame.draw.line(surf, scar_color, (16, 35), (20, 38), 1)
		pygame.draw.line(surf, scar_color, (28, 40), (32, 43), 1)
		
		return surf

	def update_with_input(self, move_dict, dt):
		# Movement using move dictionary (supports both keyboard and controller)
		if move_dict['left']:
			self.rect.x -= self.speed
		if move_dict['right']:
			self.rect.x += self.speed
		if move_dict['up']:
			self.rect.y -= self.speed
		if move_dict['down']:
			self.rect.y += self.speed
		# Keep shark at bottom portion of screen
		self.rect.y = max(400, min(self.rect.y, 580))
		self.rect.x = max(0, min(self.rect.x, 768))
		# Animation
		self.frame_timer += dt
		if self.frame_timer > 1000 // self.frame_rate:
			self.current_frame = (self.current_frame + 1) % len(self.images)
			self.image = self.images[self.current_frame]
			self.frame_timer = 0
		# Weapon firing cooldown
		if self.fire_cooldown > 0:
			self.fire_cooldown -= dt
	
	def update(self, *args, **kwargs):
		# Fallback update method for sprite group compatibility
		pass

	def fire_laser(self):
		if self.laser_energy >= 10 and self.fire_cooldown <= 0:
			self.laser_energy -= 10
			self.fire_cooldown = 300  # ms cooldown
			print("Laser fired!")
			return True
		return False

	def fire_missile(self):
		if self.missiles > 0 and self.fire_cooldown <= 0:
			self.missiles -= 1
			self.fire_cooldown = 500
			print("Missile fired!")
			return True
		return False

	def fire_torpedo(self):
		if self.torpedoes > 0 and self.fire_cooldown <= 0:
			self.torpedoes -= 1
			self.fire_cooldown = 800
			print("Torpedo fired!")
			return True
		return False
