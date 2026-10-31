"""
Advanced Graphics Enhancement Module for Shark Laser Arcade
Adds visual effects, improved animations, and graphical polish
"""

import pygame
import math
import random
from typing import Tuple, List, Optional

class LightingSystem:
    """Dynamic lighting effects for underwater atmosphere"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.width = screen_width
        self.height = screen_height
        self.light_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.time = 0
        
    def create_volumetric_rays(self, surface: pygame.Surface, time_offset: float):
        """Create animated volumetric light rays from surface"""
        self.light_surface.fill((0, 0, 0, 0))
        
        # Create multiple light rays
        num_rays = 8
        for i in range(num_rays):
            # Calculate ray position and angle
            base_x = (i + 0.5) * (self.width / num_rays)
            sway = math.sin(time_offset * 0.001 + i * 0.5) * 30
            
            # Ray parameters
            ray_width = 60 + math.sin(time_offset * 0.002 + i) * 20
            ray_opacity = 30 + math.sin(time_offset * 0.003 + i * 0.7) * 15
            
            # Draw ray as gradient polygon
            points = [
                (base_x + sway - ray_width/2, 0),
                (base_x + sway + ray_width/2, 0),
                (base_x + sway*2 + ray_width, self.height),
                (base_x + sway*2 - ray_width, self.height)
            ]
            
            # Create gradient effect by drawing multiple overlapping shapes
            for j in range(5):
                opacity = ray_opacity * (1 - j * 0.2)
                width_mod = j * 10
                gradient_points = [
                    (points[0][0] + width_mod, points[0][1]),
                    (points[1][0] - width_mod, points[1][1]),
                    (points[2][0] - width_mod*2, points[2][1]),
                    (points[3][0] + width_mod*2, points[3][1])
                ]
                pygame.draw.polygon(self.light_surface, 
                                  (200, 220, 255, int(opacity)), 
                                  gradient_points)
        
        surface.blit(self.light_surface, (0, 0), special_flags=pygame.BLEND_ADD)
    
    def create_depth_fog(self, surface: pygame.Surface, depth: float = 0.5):
        """Add depth-based fog effect"""
        fog_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Create gradient fog from top (deeper) to bottom (shallower)
        for y in range(0, self.height, 4):
            fog_intensity = int(50 * (1 - y / self.height) * depth)
            pygame.draw.rect(fog_surface, (0, 30, 60, fog_intensity), 
                           (0, y, self.width, 4))
        
        surface.blit(fog_surface, (0, 0))


class WaterEffects:
    """Advanced water visual effects"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.width = screen_width
        self.height = screen_height
        self.ripple_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.distortion_offset = 0
        
    def create_water_distortion(self, surface: pygame.Surface, time: float):
        """Create water distortion/refraction effect"""
        # This would ideally use a shader, but we'll simulate with surface manipulation
        distortion_surface = surface.copy()
        
        # Apply wave-like distortion
        for y in range(0, self.height, 10):
            offset = int(math.sin(time * 0.002 + y * 0.02) * 3)
            if 0 < y < self.height - 10:
                strip = surface.subsurface((0, y, self.width, 10))
                distortion_surface.blit(strip, (offset, y))
        
        return distortion_surface
    
    def add_bubble_stream(self, surface: pygame.Surface, sources: List[Tuple[int, int]], time: float):
        """Add animated bubble streams from specific sources"""
        for source_x, source_y in sources:
            for i in range(5):
                bubble_offset = (time * 0.1 + i * 100) % self.height
                bubble_x = source_x + math.sin(time * 0.003 + i) * 10
                bubble_y = source_y - bubble_offset
                
                if 0 < bubble_y < self.height:
                    bubble_size = 2 + (i % 3)
                    # Bubble with highlight
                    pygame.draw.circle(surface, (150, 200, 255, 100), 
                                     (int(bubble_x), int(bubble_y)), bubble_size)
                    pygame.draw.circle(surface, (255, 255, 255, 200), 
                                     (int(bubble_x - bubble_size/3), int(bubble_y - bubble_size/3)), 
                                     bubble_size // 2)


class ParticleEffects:
    """Enhanced particle system with various effect types"""
    
    @staticmethod
    def create_explosion(particles_group, center: Tuple[int, int], 
                        color_palette: List[Tuple[int, int, int]], 
                        intensity: int = 30):
        """Create an explosion effect with multiple particle types"""
        # Core explosion particles
        for i in range(intensity):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            vel = (math.cos(angle) * speed, math.sin(angle) * speed)
            color = random.choice(color_palette)
            size = random.randint(3, 8)
            lifetime = random.randint(20, 40)
            
            particle = EnhancedParticle(center, vel, color, size, lifetime, 
                                       particle_type='explosion')
            particles_group.add(particle)
        
        # Smoke/debris particles
        for i in range(intensity // 2):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 3)
            vel = (math.cos(angle) * speed, math.sin(angle) * speed - 1)
            color = (100, 100, 100, 128)
            size = random.randint(5, 10)
            lifetime = random.randint(30, 50)
            
            particle = EnhancedParticle(center, vel, color, size, lifetime, 
                                       particle_type='smoke')
            particles_group.add(particle)
    
    @staticmethod
    def create_trail(particles_group, position: Tuple[int, int], 
                    direction: Tuple[float, float], color: Tuple[int, int, int]):
        """Create a trail effect for moving objects"""
        for i in range(3):
            offset_x = random.uniform(-2, 2)
            offset_y = random.uniform(-2, 2)
            pos = (position[0] + offset_x, position[1] + offset_y)
            vel = (-direction[0] * 0.5 + random.uniform(-0.5, 0.5), 
                   -direction[1] * 0.5 + random.uniform(-0.5, 0.5))
            size = random.randint(2, 4)
            lifetime = random.randint(10, 20)
            
            particle = EnhancedParticle(pos, vel, color, size, lifetime, 
                                       particle_type='trail')
            particles_group.add(particle)


class EnhancedParticle(pygame.sprite.Sprite):
    """Enhanced particle with fade effects and physics"""
    
    def __init__(self, pos: Tuple[int, int], vel: Tuple[float, float], 
                 color: Tuple[int, int, int], size: int, lifetime: int, 
                 particle_type: str = 'default'):
        super().__init__()
        # Ensure color values are valid
        if len(color) >= 3:
            self.original_color = tuple(max(0, min(255, int(c))) for c in color[:3])
        else:
            self.original_color = (255, 255, 255)  # Default white
        self.alpha = max(0, min(255, color[3] if len(color) == 4 else 255))
        self.size = size
        self.original_size = size
        self.image = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.vel = pygame.Vector2(vel)
        self.lifetime = lifetime
        self.age = 0
        self.particle_type = particle_type
        self.gravity = 0.1 if particle_type == 'smoke' else 0
        
        self._draw_particle()
    
    def _draw_particle(self):
        """Draw the particle with current properties"""
        self.image.fill((0, 0, 0, 0))
        
        # Calculate current alpha based on age
        alpha_factor = max(0, 1 - (self.age / self.lifetime))
        current_alpha = max(0, min(255, int(self.alpha * alpha_factor)))
        
        # Ensure size is valid
        if self.size <= 0:
            return
        
        if self.particle_type == 'explosion':
            # Glowing explosion particle
            for i in range(3):
                glow_size = self.size + (2 - i) * 2
                glow_alpha = max(0, min(255, current_alpha // (i + 1)))
                color_with_alpha = (*self.original_color, glow_alpha)
                pygame.draw.circle(self.image, color_with_alpha, 
                                 (self.size, self.size), glow_size)
        
        elif self.particle_type == 'smoke':
            # Soft smoke particle
            smoke_alpha = max(0, min(255, current_alpha // 2))
            color_with_alpha = (*self.original_color, smoke_alpha)
            pygame.draw.circle(self.image, color_with_alpha, 
                             (self.size, self.size), self.size)
        
        elif self.particle_type == 'trail':
            # Sharp trail particle
            color_with_alpha = (*self.original_color, current_alpha)
            pygame.draw.circle(self.image, color_with_alpha, 
                             (self.size, self.size), self.size)
        
        else:
            # Default particle
            color_with_alpha = (*self.original_color, current_alpha)
            pygame.draw.circle(self.image, color_with_alpha, 
                             (self.size, self.size), self.size)
    
    def update(self):
        """Update particle position and properties"""
        self.rect.x += int(self.vel.x)
        self.rect.y += int(self.vel.y)
        
        # Apply physics
        self.vel.y += self.gravity
        self.vel.x *= 0.98  # Air resistance
        
        # Age and fade
        self.age += 1
        
        # Shrink certain particle types
        if self.particle_type == 'explosion' and self.age > self.lifetime * 0.5:
            self.size = max(1, int(self.original_size * (1 - self.age / self.lifetime)))
        
        # Redraw with new properties
        self._draw_particle()
        
        if self.age > self.lifetime:
            self.kill()


class AnimatedSprite:
    """Enhanced sprite animation system"""
    
    @staticmethod
    def create_animated_shark(frame_count: int = 8) -> List[pygame.Surface]:
        """Create enhanced animated shark sprites"""
        frames = []
        
        for frame in range(frame_count):
            surf = pygame.Surface((64, 96), pygame.SRCALPHA)
            t = frame / frame_count * math.pi * 2
            
            # Calculate animation offsets
            tail_sway = math.sin(t) * 8
            fin_flap = math.sin(t * 2) * 3
            body_twist = math.sin(t * 0.5) * 2
            
            # Main body with metallic sheen
            body_gradient = [
                (20, 60, 100),   # Dark blue-gray (top)
                (40, 80, 130),   # Medium blue
                (60, 100, 160),  # Light blue
                (80, 120, 180),  # Lighter blue
                (100, 140, 200)  # Belly
            ]
            
            # Draw layered body for 3D effect
            for i, color in enumerate(body_gradient):
                y_offset = i * 3
                body_width = 48 - i * 4
                body_height = 64 - i * 6
                if body_width > 0 and body_height > 0:
                    body_rect = pygame.Rect(8 + i * 2 + body_twist, 
                                           16 + y_offset, 
                                           body_width, body_height)
                    pygame.draw.ellipse(surf, color, body_rect)
            
            # Cybernetic enhancements (laser mount)
            laser_mount_color = (150, 150, 180)
            pygame.draw.rect(surf, laser_mount_color, (28, 20, 8, 12))
            pygame.draw.circle(surf, (255, 50, 50), (32, 26), 3)  # Laser lens
            
            # Animated tail
            tail_points = [
                (32 + tail_sway, 70),
                (24 + tail_sway * 1.5, 80),
                (32 + tail_sway * 2, 90),
                (40 + tail_sway * 1.5, 80)
            ]
            pygame.draw.polygon(surf, (30, 70, 110), tail_points)
            
            # Side fins with animation
            left_fin = [
                (12 - fin_flap, 45),
                (4 - fin_flap * 2, 52),
                (8 - fin_flap, 58),
                (16, 52)
            ]
            right_fin = [
                (52 + fin_flap, 45),
                (60 + fin_flap * 2, 52),
                (56 + fin_flap, 58),
                (48, 52)
            ]
            pygame.draw.polygon(surf, (40, 80, 120), left_fin)
            pygame.draw.polygon(surf, (40, 80, 120), right_fin)
            
            # Dorsal fin
            dorsal_points = [
                (32, 35),
                (28 - fin_flap, 20),
                (36 + fin_flap, 20)
            ]
            pygame.draw.polygon(surf, (30, 60, 100), dorsal_points)
            
            # Eyes with glow effect
            pygame.draw.circle(surf, (200, 200, 255), (24, 30), 3)
            pygame.draw.circle(surf, (200, 200, 255), (40, 30), 3)
            pygame.draw.circle(surf, (100, 100, 255), (24, 30), 2)
            pygame.draw.circle(surf, (100, 100, 255), (40, 30), 2)
            
            # Teeth/mouth detail
            for i in range(3):
                pygame.draw.polygon(surf, (255, 255, 255), 
                                   [(26 + i * 4, 38), 
                                    (27 + i * 4, 35), 
                                    (28 + i * 4, 38)])
            
            frames.append(surf)
        
        return frames


class ScreenEffects:
    """Post-processing and screen effects"""
    
    @staticmethod
    def apply_underwater_tint(surface: pygame.Surface):
        """Apply underwater color tinting"""
        tint_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        tint_surface.fill((0, 20, 40, 30))  # Slight blue-green tint
        surface.blit(tint_surface, (0, 0))
    
    @staticmethod
    def create_vignette(surface: pygame.Surface, intensity: float = 0.3):
        """Add vignette effect to edges of screen"""
        width, height = surface.get_size()
        vignette = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Create radial gradient from center
        center_x, center_y = width // 2, height // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)
        
        for y in range(0, height, 8):
            for x in range(0, width, 8):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                alpha = int((dist / max_dist) * 255 * intensity)
                pygame.draw.rect(vignette, (0, 0, 0, alpha), (x, y, 8, 8))
        
        surface.blit(vignette, (0, 0))
    
    @staticmethod
    def add_scan_lines(surface: pygame.Surface, time: float):
        """Add retro CRT scan line effect"""
        height = surface.get_height()
        scan_position = int((time * 0.1) % height)

        # Draw scan lines
        for y in range(0, height, 4):
            alpha = 20
            if abs(y - scan_position) < 20:
                alpha = 40 + int(20 * (1 - abs(y - scan_position) / 20))

            pygame.draw.line(surface, (0, 0, 0, alpha), (0, y), (surface.get_width(), y))

    @staticmethod
    def add_caustic_shimmer(surface: pygame.Surface, time: float):
        """Simulate refracted sunlight caustics drifting across the seafloor"""
        width, height = surface.get_size()
        caustic_surf = pygame.Surface((width, height), pygame.SRCALPHA)

        for i in range(8):
            t = time * 0.001 + i * 0.85
            x = int(width  * (0.5 + 0.44 * math.sin(t * 0.6 + i * 0.4)))
            y = int(height * (0.5 + 0.38 * math.cos(t * 0.45 + i * 0.65)))
            radius = int(55 + 28 * math.sin(t * 0.9 + i * 0.5))
            alpha  = max(0, min(255, int(13 + 7 * math.sin(t * 1.3 + i))))
            pygame.draw.circle(caustic_surf, (165, 212, 255, alpha), (x, y), radius)

        surface.blit(caustic_surf, (0, 0), special_flags=pygame.BLEND_ADD)
    
    @staticmethod
    def create_damage_flash(surface: pygame.Surface, intensity: float):
        """Create red flash effect when taking damage"""
        flash_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        flash_surface.fill((255, 0, 0, int(intensity * 128)))
        surface.blit(flash_surface, (0, 0))
    
    @staticmethod
    def create_powerup_glow(surface: pygame.Surface, position: Tuple[int, int], 
                           color: Tuple[int, int, int], radius: int, time: float):
        """Create animated glow effect for powerups"""
        glow_surface = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        
        # Pulsing effect
        pulse = 1 + math.sin(time * 0.005) * 0.3
        current_radius = int(radius * pulse)
        
        # Draw multiple layers for glow
        for i in range(5):
            layer_radius = current_radius + i * 5
            alpha = 100 - i * 20
            glow_color = (*color, alpha)
            pygame.draw.circle(glow_surface, glow_color, 
                             (radius * 2, radius * 2), layer_radius)
        
        surface.blit(glow_surface, 
                    (position[0] - radius * 2, position[1] - radius * 2), 
                    special_flags=pygame.BLEND_ADD)


class BackgroundLayers:
    """Parallax background system"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.width = screen_width
        self.height = screen_height
        self.layers = []
        
    def add_layer(self, surface: pygame.Surface, scroll_speed: float, opacity: int = 255):
        """Add a background layer with parallax scrolling"""
        self.layers.append({
            'surface': surface,
            'scroll_speed': scroll_speed,
            'opacity': opacity,
            'y_offset': 0
        })
    
    def update(self, delta_time: float):
        """Update layer positions"""
        for layer in self.layers:
            layer['y_offset'] += layer['scroll_speed'] * delta_time
            if layer['y_offset'] > self.height:
                layer['y_offset'] -= self.height * 2
    
    def draw(self, surface: pygame.Surface):
        """Draw all layers with parallax effect"""
        for layer in self.layers:
            # Draw layer twice for seamless scrolling
            temp_surface = layer['surface'].copy()
            temp_surface.set_alpha(layer['opacity'])
            surface.blit(temp_surface, (0, layer['y_offset']))
            surface.blit(temp_surface, (0, layer['y_offset'] - self.height))


# Integration helper class
class GraphicsEnhancer:
    """Main class to integrate all graphics enhancements"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.lighting = LightingSystem(self.width, self.height)
        self.water = WaterEffects(self.width, self.height)
        self.backgrounds = BackgroundLayers(self.width, self.height)
        
        self.time = 0
        self.damage_flash = 0
        
    def update(self, delta_time: float):
        """Update all enhancement systems"""
        self.time += delta_time
        self.backgrounds.update(delta_time)
        
        if self.damage_flash > 0:
            self.damage_flash -= delta_time * 0.01
    
    def render_background(self):
        """Render enhanced background"""
        # Create gradient ocean background
        for y in range(0, self.height, 2):
            depth_factor = y / self.height
            blue_value = int(20 + depth_factor * 60)
            green_value = int(10 + depth_factor * 30)
            color = (0, green_value, blue_value)
            pygame.draw.rect(self.screen, color, (0, y, self.width, 2))
        
        # Add background layers
        self.backgrounds.draw(self.screen)
        
        # Add volumetric lighting
        # self.lighting.create_volumetric_rays(self.screen, self.time)
        
        # Add depth fog
        self.lighting.create_depth_fog(self.screen, 0.3)
    
    def render_effects(self):
        """Apply post-processing effects"""
        # Water tint
        ScreenEffects.apply_underwater_tint(self.screen)
        
        # Vignette
        ScreenEffects.create_vignette(self.screen, 0.2)
        
        # Underwater caustic light shimmer
        # ScreenEffects.add_caustic_shimmer(self.screen, self.time)
        
        # Damage flash if active
        if self.damage_flash > 0:
            ScreenEffects.create_damage_flash(self.screen, self.damage_flash)
    
    def trigger_damage_effect(self):
        """Trigger damage visual effect"""
        self.damage_flash = 1.0
    
    def add_bubble_sources(self, sources: List[Tuple[int, int]]):
        """Add bubble stream sources"""
        self.water.add_bubble_stream(self.screen, sources, self.time)
