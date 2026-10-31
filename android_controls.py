"""
Touch control system for Android version of Lazer Shark Kill! Kill!
Provides virtual joystick and button controls for mobile gameplay.
"""

import pygame
import math

class AndroidTouchControls:
    """Complete touch control system for Android devices"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Virtual joystick configuration
        self.joystick_center = (150, screen_height - 150)
        self.joystick_radius = 80
        self.joystick_dead_zone = 0.2  # 20% dead zone
        
        # Action buttons configuration
        self.button_size = 60
        self.button_spacing = 80
        
        # Position buttons on the right side
        base_x = screen_width - 120
        base_y = screen_height - 200
        
        self.buttons = {
            'laser': {
                'pos': (base_x, base_y + self.button_spacing),
                'color': (255, 0, 0),
                'label': 'L',
                'radius': self.button_size
            },
            'missile': {
                'pos': (base_x - self.button_spacing, base_y),
                'color': (255, 165, 0),
                'label': 'M',
                'radius': self.button_size - 10
            },
            'torpedo': {
                'pos': (base_x + self.button_spacing, base_y),
                'color': (0, 100, 255),
                'label': 'T',
                'radius': self.button_size - 10
            },
            'pause': {
                'pos': (screen_width - 50, 50),
                'color': (128, 128, 128),
                'label': '||',
                'radius': 30
            }
        }
        
        # Touch tracking
        self.touches = {}
        self.joystick_touch_id = None
        self.button_touches = {}
        
        # Visual feedback
        self.joystick_position = (0, 0)
        self.pressed_buttons = set()
        
        # Font for button labels
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 24, bold=True)
        self.small_font = pygame.font.SysFont('Arial', 16)
    
    def handle_event(self, event):
        """Process touch events"""
        if event.type == pygame.FINGERDOWN:
            # Convert normalized coordinates to screen coordinates
            touch_x = event.x * self.screen_width
            touch_y = event.y * self.screen_height
            touch_id = event.finger_id
            
            self.touches[touch_id] = (touch_x, touch_y)
            
            # Check if touch is on joystick
            if self._is_point_in_circle(touch_x, touch_y, *self.joystick_center, self.joystick_radius):
                self.joystick_touch_id = touch_id
            
            # Check if touch is on any button
            for button_name, button_info in self.buttons.items():
                if self._is_point_in_circle(touch_x, touch_y, *button_info['pos'], button_info['radius']):
                    self.button_touches[touch_id] = button_name
                    self.pressed_buttons.add(button_name)
        
        elif event.type == pygame.FINGERUP:
            touch_id = event.finger_id
            
            # Release joystick
            if touch_id == self.joystick_touch_id:
                self.joystick_touch_id = None
                self.joystick_position = (0, 0)
            
            # Release button
            if touch_id in self.button_touches:
                button_name = self.button_touches[touch_id]
                self.pressed_buttons.discard(button_name)
                del self.button_touches[touch_id]
            
            # Remove touch from tracking
            if touch_id in self.touches:
                del self.touches[touch_id]
        
        elif event.type == pygame.FINGERMOTION:
            touch_x = event.x * self.screen_width
            touch_y = event.y * self.screen_height
            touch_id = event.finger_id
            
            self.touches[touch_id] = (touch_x, touch_y)
            
            # Update joystick position if this is the joystick touch
            if touch_id == self.joystick_touch_id:
                self._update_joystick_position(touch_x, touch_y)
    
    def _is_point_in_circle(self, px, py, cx, cy, radius):
        """Check if a point is inside a circle"""
        dx = px - cx
        dy = py - cy
        return (dx * dx + dy * dy) <= (radius * radius)
    
    def _update_joystick_position(self, touch_x, touch_y):
        """Update joystick position based on touch"""
        dx = touch_x - self.joystick_center[0]
        dy = touch_y - self.joystick_center[1]
        
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 0:
            # Normalize and clamp to joystick radius
            if distance > self.joystick_radius:
                dx = (dx / distance) * self.joystick_radius
                dy = (dy / distance) * self.joystick_radius
            
            # Apply dead zone
            normalized_distance = distance / self.joystick_radius
            if normalized_distance < self.joystick_dead_zone:
                self.joystick_position = (0, 0)
            else:
                # Scale from dead zone to full range
                scale = (normalized_distance - self.joystick_dead_zone) / (1.0 - self.joystick_dead_zone)
                self.joystick_position = (
                    (dx / self.joystick_radius) * scale,
                    (dy / self.joystick_radius) * scale
                )
        else:
            self.joystick_position = (0, 0)
    
    def get_movement(self):
        """Get current joystick movement vector (-1 to 1 for x and y)"""
        return self.joystick_position
    
    def is_button_pressed(self, button_name):
        """Check if a specific button is currently pressed"""
        return button_name in self.pressed_buttons
    
    def draw(self, screen):
        """Draw all touch controls on screen"""
        # Draw joystick base
        pygame.draw.circle(screen, (100, 100, 100, 128), 
                          self.joystick_center, self.joystick_radius, 3)
        
        # Draw joystick crosshair
        pygame.draw.line(screen, (100, 100, 100, 128),
                        (self.joystick_center[0] - self.joystick_radius, self.joystick_center[1]),
                        (self.joystick_center[0] + self.joystick_radius, self.joystick_center[1]), 2)
        pygame.draw.line(screen, (100, 100, 100, 128),
                        (self.joystick_center[0], self.joystick_center[1] - self.joystick_radius),
                        (self.joystick_center[0], self.joystick_center[1] + self.joystick_radius), 2)
        
        # Draw joystick position indicator
        if self.joystick_touch_id is not None:
            indicator_x = self.joystick_center[0] + self.joystick_position[0] * self.joystick_radius
            indicator_y = self.joystick_center[1] + self.joystick_position[1] * self.joystick_radius
            pygame.draw.circle(screen, (255, 255, 255, 200), 
                             (int(indicator_x), int(indicator_y)), 20)
        
        # Draw joystick label
        label = self.small_font.render("MOVE", True, (150, 150, 150))
        label_rect = label.get_rect(center=self.joystick_center)
        screen.blit(label, label_rect)
        
        # Draw action buttons
        for button_name, button_info in self.buttons.items():
            # Button background
            if button_name in self.pressed_buttons:
                # Pressed state - filled circle
                pygame.draw.circle(screen, button_info['color'], 
                                 button_info['pos'], button_info['radius'])
                label_color = (0, 0, 0)  # Black text on filled button
            else:
                # Normal state - outlined circle
                pygame.draw.circle(screen, (*button_info['color'], 128), 
                                 button_info['pos'], button_info['radius'], 3)
                label_color = button_info['color']
            
            # Button label
            label = self.font.render(button_info['label'], True, label_color)
            label_rect = label.get_rect(center=button_info['pos'])
            screen.blit(label, label_rect)
    
    def get_input_state(self):
        """Get complete input state for game logic"""
        return {
            'movement': self.get_movement(),
            'fire_laser': self.is_button_pressed('laser'),
            'fire_missile': self.is_button_pressed('missile'),
            'fire_torpedo': self.is_button_pressed('torpedo'),
            'pause': self.is_button_pressed('pause')
        }


class AndroidAdapter:
    """Adapter to integrate Android controls with existing game code"""
    
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.controls = AndroidTouchControls(self.width, self.height)
        
        # Track button states for edge detection
        self.prev_button_states = {}
        self.current_button_states = {}
    
    def handle_event(self, event):
        """Process events and convert to game-compatible format"""
        self.controls.handle_event(event)
        
        # Update button states for edge detection
        self.prev_button_states = self.current_button_states.copy()
        self.current_button_states = {
            'laser': self.controls.is_button_pressed('laser'),
            'missile': self.controls.is_button_pressed('missile'),
            'torpedo': self.controls.is_button_pressed('torpedo'),
            'pause': self.controls.is_button_pressed('pause')
        }
    
    def was_button_just_pressed(self, button_name):
        """Check if button was just pressed (rising edge)"""
        return (self.current_button_states.get(button_name, False) and 
                not self.prev_button_states.get(button_name, False))
    
    def get_movement_keys(self):
        """Convert joystick input to keyboard-like movement flags"""
        movement = self.controls.get_movement()
        threshold = 0.3  # Minimum joystick displacement to register movement
        
        return {
            'left': movement[0] < -threshold,
            'right': movement[0] > threshold,
            'up': movement[1] < -threshold,
            'down': movement[1] > threshold
        }
    
    def draw(self):
        """Draw controls on screen"""
        self.controls.draw(self.screen)


# Example integration code for main.py
def integrate_android_controls(main_game_code):
    """
    Example of how to integrate Android controls into main.py
    
    Add this at the beginning of main.py:
    
    # Android detection
    try:
        import android
        ANDROID = True
    except ImportError:
        ANDROID = False
    
    if ANDROID:
        from android_controls import AndroidAdapter
    
    # In the game initialization:
    if ANDROID:
        android_controls = AndroidAdapter(screen)
    
    # In the event loop:
    for event in pygame.event.get():
        if ANDROID:
            android_controls.handle_event(event)
            
            # Convert touch controls to game actions
            if android_controls.was_button_just_pressed('pause'):
                paused = not paused
        else:
            # Regular keyboard/controller handling
            ...
    
    # In the game update loop:
    if ANDROID:
        # Get movement from touch controls
        movement = android_controls.get_movement_keys()
        if movement['left']:
            shark.move_left()
        if movement['right']:
            shark.move_right()
        # etc...
        
        # Handle weapon firing
        if android_controls.controls.is_button_pressed('laser'):
            shark.fire_laser()
    
    # In the draw loop:
    if ANDROID:
        android_controls.draw()
    """
    pass
