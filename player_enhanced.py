"""
Enhanced Player (Shark) with sprite sheet animation
Uses actual sprite images from hai_0.png
"""
import pygame
import os
import math
from sprite_loader import EnhancedShark, SpriteSheet, SpriteEffects
from resources import resource_path

class SharkWithSprites(EnhancedShark):
    """Enhanced shark using actual sprite sheet with special effects"""
    
    def __init__(self, x, y):
        # Initialize with sprite sheet
        super().__init__(x, y, resource_path('assets', 'hai_0.png'))
        
        # Try to load the sprite sheet with specific dimensions
        self.load_shark_sprites()
        
        # Add shield visual
        self.shield_active = False
        self.shield_surface = self.create_shield_effect()
        
        # Power-up visual effects
        self.power_up_glow = 0
        self.damage_flash = 0
        
    def load_shark_sprites(self):
        """Load shark sprites from hai_0.png with correct dimensions"""
        sprite_path = resource_path('assets', 'hai_0.png')
        saved_center = self.rect.center

        if os.path.exists(sprite_path):
            try:
                # Load the image to check its dimensions
                temp_image = pygame.image.load(sprite_path)
                img_width = temp_image.get_width()
                img_height = temp_image.get_height()
                
                # hai_0.png is 592x564 pixels
                # With 4 sprites per row: 592/4 = 148 pixels wide
                # Assuming square or near-square sprites: ~148 pixels tall
                # 564/148 ≈ 3.8, so likely 4 rows of 141 pixels each (564/4 = 141)
                # Or could be 148x141 sprites
                
                if img_width == 592 and img_height == 564:
                    # Specific dimensions for hai_0.png
                    sprite_width = 148  # 592 / 4
                    sprite_height = 141  # 564 / 4
                    rows = 4
                else:
                    # Fallback auto-detection
                    sprite_width = img_width // 4
                    sprite_height = img_height // 4  # Assume 4 rows
                    rows = 4
                
                sheet = SpriteSheet(sprite_path)
                
                # Get the last row (shark sprites)
                last_row = rows - 1
                self.frames = []
                
                for i in range(4):  # 4 frames in the row
                    sx = i * sprite_width
                    sy = last_row * sprite_height

                    # Extract and scale sprite (reduced by 50% from 1.5 to 0.75)
                    sprite = sheet.get_sprite(sx, sy, sprite_width, sprite_height, scale=0.75)

                    # Apply enhancements
                    sprite = self.enhance_sprite(sprite)
                    self.frames.append(sprite)

                # Update the original frames for transformations
                self.original_frames = self.frames.copy()
                self.image = self.frames[0]
                self.rect = self.image.get_rect(center=saved_center)
                
                print(f"Successfully loaded shark sprites: {sprite_width}x{sprite_height}, {len(self.frames)} frames")
                
            except Exception as e:
                print(f"Error loading shark sprites: {e}")
                # Keep procedural sprites as fallback
    
    def enhance_sprite(self, sprite):
        """Apply visual enhancements to the sprite"""
        # Add subtle outline for better visibility
        sprite = SpriteEffects.add_outline(sprite, (0, 50, 100), 1)
        
        # Add cybernetic enhancements (laser mount)
        # This could be drawn on top of the sprite
        enhanced = sprite.copy()
        
        # Add laser mount indicator
        mount_rect = pygame.Rect(
            enhanced.get_width() // 2 - 4,
            enhanced.get_height() // 4,
            8, 6
        )
        pygame.draw.rect(enhanced, (150, 150, 180), mount_rect)
        pygame.draw.circle(enhanced, (255, 50, 50), mount_rect.center, 2)
        
        return enhanced
    
    def create_shield_effect(self):
        """Create a shield bubble effect"""
        size = 80  # Reduced from 120 to match smaller shark
        shield = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Draw concentric circles for shield effect
        for i in range(3):
            radius = size // 2 - i * 7  # Adjusted spacing for smaller size
            alpha = 50 - i * 15
            pygame.draw.circle(shield, (100, 200, 255, alpha), (size // 2, size // 2), radius, 2)
        
        return shield
    
    def update(self, dt, move=None):
        """Update with visual effects"""
        super().update(dt, move)
        
        # Update visual effects timers
        if self.power_up_glow > 0:
            self.power_up_glow -= dt * 0.001
        
        if self.damage_flash > 0:
            self.damage_flash -= dt * 0.002
    
    def draw(self, screen):
        """Draw the shark with effects"""
        # Draw shadow first
        shadow = SpriteEffects.add_shadow(self.image, (3, 3), 100)
        shadow_rect = shadow.get_rect(center=(self.rect.centerx + 3, self.rect.centery + 3))
        screen.blit(shadow, shadow_rect)
        
        # Draw the shark
        if self.damage_flash > 0:
            # Flash red when damaged
            flash_surf = self.image.copy()
            flash_amount = int(self.damage_flash * 128)
            flash_surf.fill((255, 0, 0, flash_amount), special_flags=pygame.BLEND_RGBA_ADD)
            screen.blit(flash_surf, self.rect)
        elif self.power_up_glow > 0:
            # Glow when powered up
            glowing = SpriteEffects.add_glow(self.image, (255, 255, 100), self.power_up_glow)
            glow_rect = glowing.get_rect(center=self.rect.center)
            screen.blit(glowing, glow_rect)
        else:
            screen.blit(self.image, self.rect)
        
        # Draw shield on top if active
        if self.shield_active:
            shield_rect = self.shield_surface.get_rect(center=self.rect.center)
            screen.blit(self.shield_surface, shield_rect)
    
    def take_damage(self, amount):
        """Trigger damage effect"""
        self.damage_flash = 1.0
    
    def collect_powerup(self):
        """Trigger power-up effect"""
        self.power_up_glow = 1.0
    
    def activate_shield(self):
        """Activate shield visual"""
        self.shield_active = True
    
    def deactivate_shield(self):
        """Deactivate shield visual"""
        self.shield_active = False


# Function to integrate into existing game
def create_enhanced_shark(x, y):
    """Factory function to create an enhanced shark sprite"""
    return SharkWithSprites(x, y)
