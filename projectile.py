"""
The laser shot.
"""
import pygame
import math

class Laser(pygame.sprite.Sprite):
    power = 1  # Damage is multiplied by this

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
        
    def update(self, *args, **kwargs):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()
