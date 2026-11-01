"""
Sprite Sheet Loader and Animation System
Handles loading sprites from image files and creating animations
"""

import pygame
import os
from typing import List, Tuple, Optional
from resources import resource_path

LASER_SHOT_COST = 3

class SpriteSheet:
    """Load and extract sprites from a sprite sheet"""
    
    def __init__(self, filename: str):
        """Load the sprite sheet image"""
        self.sheet = pygame.image.load(filename).convert_alpha()
        self.sheet_rect = self.sheet.get_rect()
    
    def get_sprite(self, x: int, y: int, width: int, height: int, 
                   scale: Optional[float] = None) -> pygame.Surface:
        """Extract a single sprite from the sheet"""
        sprite = pygame.Surface((width, height), pygame.SRCALPHA)
        sprite.blit(self.sheet, (0, 0), (x, y, width, height))
        
        if scale:
            new_width = int(width * scale)
            new_height = int(height * scale)
            sprite = pygame.transform.scale(sprite, (new_width, new_height))
        
        return sprite
    
    def get_sprites_from_row(self, row: int, sprite_width: int, sprite_height: int, 
                            count: int, scale: Optional[float] = None) -> List[pygame.Surface]:
        """Extract multiple sprites from a single row"""
        sprites = []
        y = row * sprite_height
        
        for i in range(count):
            x = i * sprite_width
            sprite = self.get_sprite(x, y, sprite_width, sprite_height, scale)
            sprites.append(sprite)
        
        return sprites
    
    def auto_detect_sprites(self, rows: int, cols: int, 
                           scale: Optional[float] = None) -> List[List[pygame.Surface]]:
        """Automatically divide the sheet into a grid and extract all sprites"""
        sprites = []
        sprite_width = self.sheet_rect.width // cols
        sprite_height = self.sheet_rect.height // rows
        
        for row in range(rows):
            row_sprites = self.get_sprites_from_row(row, sprite_width, sprite_height, cols, scale)
            sprites.append(row_sprites)
        
        return sprites


class AnimatedSprite(pygame.sprite.Sprite):
    """Base class for animated sprites using sprite sheets"""
    
    def __init__(self, frames: List[pygame.Surface], position: Tuple[int, int], 
                 animation_speed: float = 0.15):
        super().__init__()
        self.frames = frames
        self.current_frame = 0
        self.animation_speed = animation_speed
        self.animation_timer = 0
        
        # Set initial image and rect
        self.image = self.frames[0] if frames else pygame.Surface((32, 32))
        self.rect = self.image.get_rect(center=position)
        
        # Store original images for transformations
        self.original_frames = frames.copy()
    
    def update_animation(self, dt: float):
        """Update the animation frame"""
        if len(self.frames) > 1:
            self.animation_timer += dt * 0.001  # Convert to seconds
            
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.image = self.frames[self.current_frame]
    
    def flip_horizontal(self):
        """Flip all frames horizontally"""
        self.frames = [pygame.transform.flip(frame, True, False) for frame in self.original_frames]
        self.image = self.frames[self.current_frame]
    
    def flip_vertical(self):
        """Flip all frames vertically"""
        self.frames = [pygame.transform.flip(frame, False, True) for frame in self.original_frames]
        self.image = self.frames[self.current_frame]
    
    def rotate(self, angle: float):
        """Rotate all frames by the given angle"""
        self.frames = [pygame.transform.rotate(frame, angle) for frame in self.original_frames]
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(center=self.rect.center)
    
    def scale(self, scale_factor: float):
        """Scale all frames by the given factor"""
        self.frames = []
        for frame in self.original_frames:
            width = int(frame.get_width() * scale_factor)
            height = int(frame.get_height() * scale_factor)
            scaled = pygame.transform.scale(frame, (width, height))
            self.frames.append(scaled)
        
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(center=self.rect.center)


class EnhancedShark(AnimatedSprite):
    """Enhanced shark sprite using actual sprite sheet"""
    
    def __init__(self, x: int, y: int, sprite_sheet_path: str = resource_path('assets', 'hai_0.png')):
        # Try to load the sprite sheet
        try:
            if os.path.exists(sprite_sheet_path):
                sheet = SpriteSheet(sprite_sheet_path)
                
                # Assuming the shark sprites are in the last row and there are 4 frames
                # You mentioned the last horizontal row of four images
                # We'll need to know the dimensions - let's try auto-detection
                # Assuming a common sprite sheet layout
                
                # Try different common sprite dimensions
                sprite_sizes = [
                    (32, 32, 8, 8),   # 32x32 sprites, 8x8 grid
                    (64, 64, 4, 4),   # 64x64 sprites, 4x4 grid
                    (48, 48, 5, 5),   # 48x48 sprites, 5x5 grid
                    (16, 16, 16, 16), # 16x16 sprites, 16x16 grid
                ]
                
                frames = []
                for width, height, cols, rows in sprite_sizes:
                    try:
                        # Try to get the last row
                        last_row = rows - 1
                        frames = sheet.get_sprites_from_row(
                            last_row, width, height, 4, scale=2.0
                        )
                        if frames and all(frame for frame in frames):
                            break
                    except Exception:
                        continue
                
                # If we couldn't load sprites, use fallback
                if not frames:
                    print(f"Could not extract sprites from {sprite_sheet_path}, using procedural sprites")
                    frames = self._create_procedural_frames()
            else:
                print(f"Sprite sheet not found: {sprite_sheet_path}, using procedural sprites")
                frames = self._create_procedural_frames()
        except Exception as e:
            print(f"Error loading sprite sheet: {e}, using procedural sprites")
            frames = self._create_procedural_frames()
        
        super().__init__(frames, (x, y), animation_speed=0.1)
        
        # Shark-specific attributes
        self.speed = 5
        self.laser_energy = 100
        self.missiles = 3
        self.torpedoes = 1
        self.fire_cooldown = 0
        
        # Movement state for animation
        self.is_moving = False
        self.movement_direction = 0  # -1 for left, 0 for straight, 1 for right
    
    def _create_procedural_frames(self) -> List[pygame.Surface]:
        """Create procedural shark frames as fallback"""
        import math
        frames = []
        
        for phase in range(4):
            surf = pygame.Surface((64, 96), pygame.SRCALPHA)
            t = phase / 4 * math.pi * 2
            
            # Main body
            body_colors = [
                (20, 60, 100),
                (40, 80, 130),
                (60, 100, 160),
                (80, 120, 180),
            ]
            
            for i, color in enumerate(body_colors):
                y_offset = i * 3
                body_width = 48 - i * 4
                body_height = 64 - i * 6
                if body_width > 0 and body_height > 0:
                    body_rect = pygame.Rect(8 + i * 2 + int(math.sin(t) * 2), 
                                           16 + y_offset, 
                                           body_width, body_height)
                    pygame.draw.ellipse(surf, color, body_rect)
            
            # Animated tail
            tail_sway = math.sin(t) * 8
            tail_points = [
                (32 + tail_sway, 70),
                (24 + tail_sway * 1.5, 80),
                (32 + tail_sway * 2, 90),
                (40 + tail_sway * 1.5, 80)
            ]
            pygame.draw.polygon(surf, (30, 70, 110), tail_points)
            
            # Fins
            fin_flap = math.sin(t * 2) * 3
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
            
            # Eyes
            pygame.draw.circle(surf, (200, 200, 255), (24, 30), 3)
            pygame.draw.circle(surf, (200, 200, 255), (40, 30), 3)
            
            # Laser mount (cybernetic enhancement)
            pygame.draw.rect(surf, (150, 150, 180), (28, 20, 8, 12))
            pygame.draw.circle(surf, (255, 50, 50), (32, 26), 3)
            
            frames.append(surf)
        
        return frames
    
    def update(self, dt: float, move: dict = None):
        """Update shark animation and position"""
        # Update animation
        self.update_animation(dt)
        
        # Handle movement
        if move:
            old_center = self.rect.center
            
            if move.get('left'):
                self.rect.x -= self.speed
                self.movement_direction = -1
                self.is_moving = True
            elif move.get('right'):
                self.rect.x += self.speed
                self.movement_direction = 1
                self.is_moving = True
            else:
                self.movement_direction = 0
            
            if move.get('up'):
                self.rect.y -= self.speed
                self.is_moving = True
            elif move.get('down'):
                self.rect.y += self.speed
                self.is_moving = True
            else:
                if not move.get('left') and not move.get('right'):
                    self.is_moving = False
            
            # Keep the whole shark on screen, in the bottom portion
            self.rect.x = max(0, min(self.rect.x, 800 - self.rect.width))
            self.rect.y = max(400, min(self.rect.y, 600 - self.rect.height))
            
            # Adjust animation speed based on movement
            if self.is_moving:
                self.animation_speed = 0.08  # Faster animation when moving
            else:
                self.animation_speed = 0.15  # Slower when idle
        
        # Update fire cooldown
        if self.fire_cooldown > 0:
            self.fire_cooldown -= dt * 0.001
    
    def fire_laser(self, cost=LASER_SHOT_COST, cooldown=0.1) -> bool:
        """Fire laser if energy available"""
        if self.laser_energy >= cost and self.fire_cooldown <= 0:
            self.laser_energy -= cost
            self.fire_cooldown = cooldown
            return True
        return False
    
    def fire_missile(self) -> bool:
        """Fire missile if available"""
        if self.missiles > 0 and self.fire_cooldown <= 0:
            self.missiles -= 1
            self.fire_cooldown = 0.3  # 300ms cooldown
            return True
        return False
    
    def fire_torpedo(self) -> bool:
        """Fire torpedo if available"""
        if self.torpedoes > 0 and self.fire_cooldown <= 0:
            self.torpedoes -= 1
            self.fire_cooldown = 0.5  # 500ms cooldown
            return True
        return False


def load_enhanced_sprites():
    """Load and enhance all game sprites from files"""
    sprites = {}
    
    # Load shark sprite
    shark_path = resource_path('assets', 'hai_0.png')
    if os.path.exists(shark_path):
        try:
            sheet = SpriteSheet(shark_path)
            # This would need to be adjusted based on actual sprite sheet layout
            sprites['shark'] = sheet
        except:
            print("Could not load shark sprite sheet")
    
    # Load other sprites if available
    sprite_files = {
        'coral': resource_path('assets', 'coral.png'),
        'shipwreck': resource_path('assets', 'shipwreck.png'),
        'fish': resource_path('assets', 'fish.png'),
        'submarine': resource_path('assets', 'submarine.png')
    }
    
    for name, path in sprite_files.items():
        if os.path.exists(path):
            try:
                sprites[name] = pygame.image.load(path).convert_alpha()
            except:
                print(f"Could not load {name} sprite")
    
    return sprites


# Enhanced sprite effects
class SpriteEffects:
    """Apply visual effects to sprites"""
    
    @staticmethod
    def add_glow(sprite: pygame.Surface, color: Tuple[int, int, int], 
                 intensity: float = 1.0) -> pygame.Surface:
        """Add a glow effect around a sprite"""
        width, height = sprite.get_size()
        glow_surf = pygame.Surface((width + 20, height + 20), pygame.SRCALPHA)
        
        # Draw multiple layers of the sprite with decreasing alpha
        for i in range(5, 0, -1):
            alpha = int(50 * intensity / i)
            temp = sprite.copy()
            temp.fill((*color, alpha), special_flags=pygame.BLEND_RGBA_MULT)
            
            for dx in range(-i, i+1, i):
                for dy in range(-i, i+1, i):
                    if dx != 0 or dy != 0:
                        glow_surf.blit(temp, (10 + dx, 10 + dy))
        
        # Draw the original sprite on top
        glow_surf.blit(sprite, (10, 10))
        return glow_surf
    
    @staticmethod
    def add_outline(sprite: pygame.Surface, color: Tuple[int, int, int], 
                   thickness: int = 2) -> pygame.Surface:
        """Add an outline around a sprite"""
        width, height = sprite.get_size()
        outlined = pygame.Surface((width + thickness * 2, height + thickness * 2), pygame.SRCALPHA)
        
        # Create mask from original sprite
        mask = pygame.mask.from_surface(sprite)
        
        # Draw outline
        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):
                if dx != 0 or dy != 0:
                    outlined.blit(sprite, (thickness + dx, thickness + dy))
        
        # Fill outline with color
        outlined.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MIN)
        
        # Draw original sprite on top
        outlined.blit(sprite, (thickness, thickness))
        return outlined
    
    @staticmethod
    def add_shadow(sprite: pygame.Surface, offset: Tuple[int, int] = (5, 5), 
                  opacity: int = 128) -> pygame.Surface:
        """Add a drop shadow to a sprite"""
        width, height = sprite.get_size()
        shadowed = pygame.Surface((width + abs(offset[0]), height + abs(offset[1])), pygame.SRCALPHA)
        
        # Create shadow
        shadow = sprite.copy()
        shadow.fill((0, 0, 0, opacity), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Draw shadow offset
        shadow_x = max(0, offset[0])
        shadow_y = max(0, offset[1])
        shadowed.blit(shadow, (shadow_x, shadow_y))
        
        # Draw original sprite
        sprite_x = max(0, -offset[0])
        sprite_y = max(0, -offset[1])
        shadowed.blit(sprite, (sprite_x, sprite_y))
        
        return shadowed
