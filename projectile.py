"""
Projectile sprites for laser, missile, and torpedo.
"""
import pygame
import math

class Laser(pygame.sprite.Sprite):
    power = 1  # Damage is multiplied by this
    pierce = False  # Passes through what it hits, hurting each thing once

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((8, 20), pygame.SRCALPHA)
        
        # Create glowing laser beam effect
        # Outer glow (larger, dimmer)
        pygame.draw.rect(self.image, (255, 100, 100, 128), (1, 0, 6, 20))
        # Middle beam (brighter)
        pygame.draw.rect(self.image, (255, 150, 150), (2, 0, 4, 20))
        # Core beam (brightest)
        pygame.draw.rect(self.image, (255, 255, 255), (3, 0, 2, 20))
        
        # Add energy sparkles
        for i in range(3):
            y_pos = i * 6 + 2
            pygame.draw.circle(self.image, (255, 255, 255), (4, y_pos), 1)
        
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.speed = -12
        self.already_hit = set()
        
    def update(self, *args, **kwargs):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

class Missile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 24), pygame.SRCALPHA)
        
        # Enhanced missile with better details
        # Main body (metallic gray with shading)
        pygame.draw.rect(self.image, (120, 120, 120), (3, 4, 4, 16))  # Dark side
        pygame.draw.rect(self.image, (180, 180, 180), (2, 4, 4, 16))  # Light side
        pygame.draw.rect(self.image, (200, 200, 200), (2, 6, 6, 12))  # Main body
        
        # Nose cone (pointed tip)
        pygame.draw.polygon(self.image, (160, 160, 160), [(2, 4), (8, 4), (5, 0)])
        pygame.draw.polygon(self.image, (200, 200, 200), [(3, 4), (7, 4), (5, 1)])  # Highlight
        
        # Fins (stabilizers)
        fin_color = (140, 140, 140)
        pygame.draw.polygon(self.image, fin_color, [(1, 18), (3, 16), (3, 20)])  # Left fin
        pygame.draw.polygon(self.image, fin_color, [(7, 16), (9, 18), (7, 20)])  # Right fin
        
        # Exhaust trail effect
        pygame.draw.rect(self.image, (255, 200, 100, 180), (4, 20, 2, 4))  # Flame
        pygame.draw.rect(self.image, (255, 150, 50, 120), (3, 22, 4, 2))   # Outer flame
        
        # Tech details
        pygame.draw.line(self.image, (100, 100, 100), (2, 10), (8, 10), 1)  # Panel line
        pygame.draw.rect(self.image, (80, 80, 80), (4, 8, 2, 1))  # Sensor
        
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.speed = -8
        
    def update(self, *args, **kwargs):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

class Torpedo(pygame.sprite.Sprite):
    def __init__(self, x, y, target=None):
        super().__init__()
        self.image = pygame.Surface((12, 28), pygame.SRCALPHA)
        
        # Enhanced torpedo with underwater design
        # Main body (cylindrical, darker colors for underwater)
        pygame.draw.rect(self.image, (0, 120, 140), (3, 6, 6, 18))  # Main body
        pygame.draw.rect(self.image, (0, 160, 180), (2, 6, 6, 18))  # Highlight side
        pygame.draw.rect(self.image, (0, 200, 220), (3, 8, 6, 14))  # Center highlight
        
        # Nose cone (streamlined for water)
        pygame.draw.polygon(self.image, (0, 100, 120), [(3, 6), (9, 6), (6, 0)])
        pygame.draw.polygon(self.image, (0, 140, 160), [(4, 6), (8, 6), (6, 2)])  # Highlight
        
        # Propeller/fins at back
        prop_color = (0, 80, 100)
        pygame.draw.polygon(self.image, prop_color, [(2, 22), (4, 20), (4, 26)])  # Left prop
        pygame.draw.polygon(self.image, prop_color, [(8, 20), (10, 22), (8, 26)]) # Right prop
        pygame.draw.polygon(self.image, prop_color, [(5, 18), (7, 18), (6, 24)])  # Top prop
        
        # Sonar/guidance system (glowing)
        pygame.draw.circle(self.image, (100, 255, 255), (6, 10), 2)
        pygame.draw.circle(self.image, (200, 255, 255), (6, 10), 1)
        
        # Underwater bubbles trail
        pygame.draw.circle(self.image, (150, 200, 255, 100), (4, 24), 1)
        pygame.draw.circle(self.image, (150, 200, 255, 80), (8, 25), 1)
        pygame.draw.circle(self.image, (150, 200, 255, 60), (6, 26), 1)
        
        # Tech markings
        pygame.draw.line(self.image, (0, 60, 80), (3, 12), (9, 12), 1)
        pygame.draw.line(self.image, (0, 60, 80), (3, 16), (9, 16), 1)
        pygame.draw.rect(self.image, (0, 180, 200), (5, 14, 2, 1))  # Status light
        
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.speed = -6
        self.target = target
    def update(self, *args, **kwargs):
        if self.target and self.target.alive():
            # Home in on target
            dx = self.target.rect.centerx - self.rect.centerx
            dy = self.target.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.rect.x += int(dx / dist * 4)
                self.rect.y += int(dy / dist * 4)
        else:
            self.rect.y += self.speed
        if self.rect.bottom < 0 or self.rect.top > 600:
            self.kill()
