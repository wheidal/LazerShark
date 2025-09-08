
import pygame
import random
import math

class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, vel, color, size, lifetime):
        super().__init__()
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (size // 2, size // 2), size // 2)
        self.rect = self.image.get_rect(center=pos)
        self.vel = pygame.Vector2(vel)
        self.lifetime = lifetime
        self.age = 0
    def update(self, *args, **kwargs):
        self.rect.x += int(self.vel.x)
        self.rect.y += int(self.vel.y)
        self.age += 1
        if self.age > self.lifetime:
            self.kill()

class ParticleEmitter:
    def __init__(self, group):
        self.group = group
    def emit(self, pos, color=(255,255,255), count=10, size=6, speed=3, lifetime=20):
        for _ in range(count):
            angle = random.uniform(0, 2 * 3.14159)
            vel = (speed * random.uniform(0.5, 1.2) * math.cos(angle), speed * random.uniform(0.5, 1.2) * math.sin(angle))
            p = Particle(pos, vel, color, size, lifetime)
            self.group.add(p)
