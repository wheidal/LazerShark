"""
Settings manager for persisting game preferences.
"""

import json
import os

class SettingsManager:
    """Manages loading and saving game settings."""

    def __init__(self, settings_file="game_settings.json"):
        self.settings_file = settings_file
        self.default_settings = {
            'music_enabled': True,
            'music_volume': 0.5,
            'sfx_volume': 1.0,
            'controller_enabled': False,
            'easy_mode': False,
            'keymap': {
                'left': 276,  # pygame.K_LEFT
                'right': 275,  # pygame.K_RIGHT
                'up': 273,    # pygame.K_UP
                'down': 274,  # pygame.K_DOWN
                'fire': 32,   # pygame.K_SPACE
                'missile': 308,  # pygame.K_LALT
                'torpedo': 306,  # pygame.K_LCTRL
                'pause': 112,    # pygame.K_p
                'quit': 27       # pygame.K_ESCAPE
            }
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load settings from file or return defaults."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Deep-merge with defaults to handle missing keys
                    settings = self.default_settings.copy()
                    if 'keymap' in loaded_settings:
                        merged_keymap = self.default_settings['keymap'].copy()
                        merged_keymap.update(loaded_settings['keymap'])
                        loaded_settings = dict(loaded_settings)
                        loaded_settings['keymap'] = merged_keymap
                    settings.update(loaded_settings)
                    return settings
            except (json.JSONDecodeError, IOError):
                print(f"Warning: Could not load settings from {self.settings_file}, using defaults")
                return self.default_settings.copy()
        return self.default_settings.copy()
    
    def save_settings(self):
        """Save current settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            return True
        except IOError as e:
            print(f"Warning: Could not save settings: {e}")
            return False
    
    def get(self, key, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set a setting value."""
        self.settings[key] = value
    
    def update(self, **kwargs):
        """Update multiple settings at once."""
        self.settings.update(kwargs)
