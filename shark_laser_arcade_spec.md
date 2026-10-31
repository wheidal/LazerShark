# Shark Laser Arcade Game - Design Specification v2.0

## Game Overview
**"Lazer Shark Kill! Kill!"** is a top-down, arcade-style underwater shooter where the player controls a cybernetically enhanced shark equipped with multiple weapon systems. The shark navigates through dangerous ocean depths, avoiding obstacles, collecting powerups, and eating fish to survive as long as possible.

## Current Implementation Status: ✅ COMPLETE

The game is fully playable with all core features implemented and optimized.

---

## 🎮 Core Gameplay Features

### Player Character
- **Shark**: Cybernetically enhanced with weapon systems
- **Movement**: 360-degree movement within screen boundaries
- **Energy System**: Depletes over time and when damaged; restored by eating fish
- **Visual**: Animated sprite with weapon attachments

### Weapon Systems
| Weapon | Ammo Type | Damage | Special Properties |
|--------|-----------|--------|--------------------|
| **Laser** | Energy-based | Medium | Fast firing, requires energy |
| **Missile** | Limited (max 3) | High | Explosive, one-hit obstacle destruction |
| **Torpedo** | Limited (max 3) | High | Homing capability, tracks nearest obstacle |

### Triple Laser Upgrade
- **Activation**: Temporary upgrade triggered by destroying obstacles
- **Effect**: Fires three lasers simultaneously with unique sound
- **Duration**: Maintained by continued obstacle destruction

### Shield System
- **Activation**: Collect shield powerups (spawn after destroying 4 identical obstacles - made rarer)
- **Strength**: 100 points, depletes by 33 per collision (3 hits maximum)
- **Visual**: Strength bar with color coding (green→yellow→orange) and arc indicator
- **Regeneration**: When shield depletes, 2-3 new shield powerups spawn immediately
- **UI**: Always visible progress bar (greyed out when inactive)

---

## 🌊 Game Environment

### Underwater Setting
- **Background**: Dynamic gradient with depth-based coloring
- **Visual Effects**:
  - Animated water caustics (light patterns)
  - Floating bubble particles
  - Swaying kelp forests
  - Particle explosion effects

### Obstacles
| Obstacle Type | Durability | Sound Effect | Behavior |
|---------------|------------|--------------|----------|
| **Coral Reefs** | 3 laser hits | Organic cracking | Static, destructible |
| **Shipwrecks** | 3 laser hits | Metallic clang | Static, destructible |
| **Friendly Submarines** | Invulnerable | Sonar ping | Moving, causes damage |

### Food & Powerups
- **Small Fish**: Restore 15 energy points
- **Laser Powerups**: Restore 30 laser energy
- **Missile Powerups**: Add 2 missiles to inventory
- **Torpedo Powerups**: Add 1 torpedo to inventory
- **Shield Powerups**: Activate temporary invincibility

---

## 🎵 Audio System (v2.0 - Optimized)

### Technical Implementation
- **Pre-rendered Audio**: 16 custom WAV files (eliminated NumPy dependency)
- **Sound Categories**:
  - Weapon sounds (4 files)
  - Collision sounds (5 files)
  - Game event sounds (4 files)
  - UI sounds (2 files)
  - Ambient sound (1 file)

### Audio Files
```
sounds/
├── laser.wav              # Standard laser firing
├── laser_triple.wav       # Triple laser upgrade
├── missile.wav            # Missile launch
├── torpedo.wav           # Torpedo launch
├── coral_collision.wav    # Hitting coral reefs
├── shipwreck_collision.wav # Hitting shipwrecks
├── submarine_collision.wav # Hitting submarines
├── generic_collision.wav  # Default collision
├── fatal_collision.wav    # Game over collision
├── food_eat.wav          # Eating fish
├── powerup_collect.wav   # Collecting powerups
├── shield_activate.wav   # Shield activation
├── obstacle_destroy.wav  # Destroying obstacles
├── menu_beep.wav         # UI navigation
├── upgrade_activate.wav  # Weapon upgrades
└── ambient_ocean.wav     # Background ambience
```

---

## 🕹️ Controls & Input

### Default Keyboard Controls
| Action | Default Key | Remappable |
|--------|-------------|------------|
| Move Left | Left Arrow | ✅ |
| Move Right | Right Arrow | ✅ |
| Move Up | Up Arrow | ✅ |
| Move Down | Down Arrow | ✅ |
| Fire Laser | Spacebar | ✅ |
| Fire Missile | Left Alt | ✅ |
| Fire Torpedo | Left Ctrl | ✅ |
| Pause | P | ✅ |
| Quit | Escape | ✅ |

### Controller Support
| Action | Controller Input |
|--------|------------------|
| Movement | Left Analog Stick |
| Fire Laser | A Button |
| Fire Missile | B Button |
| Fire Torpedo | X Button |
| Pause | Start Button |

### Settings Menu Features
- **Key Remapping**: Full customization of all controls
- **Controller Toggle**: Enable/disable gamepad support
- **Easy Mode**: Unlimited laser energy for casual play

---

## 🎯 Game Mechanics

### Energy Management
- **Depletion Rate**: 0.06/frame while moving, 0.02/frame while idle (rebalanced)
- **Restoration**: +20 energy per fish consumed (increased from 15)
- **Maximum**: 100 energy points
- **Game Over**: Energy reaches 0
- **Fish Spawn Rate**: 50% (increased from 33% for better balance)

### Collision System
- **Obstacle Hit**: -33 energy (1/3 of total)
- **Submarine Hit**: -20 energy
- **Shield Protection**: Blocks all damage and destroys obstacles

### Scoring & Progression
- **Obstacle Destruction**: Points awarded
- **Fish Consumption**: Energy restoration
- **Powerup Collection**: Weapon/ability enhancement
- **Survival**: Time-based scoring

---

## 🛠️ Technical Architecture

### Modular Design
```
Project Structure:
├── main.py              # Game loop and state management
├── player.py            # Shark class and mechanics
├── obstacle.py          # Obstacle classes (coral, shipwrecks)
├── food.py             # Fish food mechanics
├── projectile.py       # Weapon projectile classes
├── powerup.py          # Powerup system
├── particle.py         # Visual effects system
├── ui.py               # User interface components
├── settings.py         # Game configuration
├── resources.py        # Resource management
├── requirements.txt    # Dependencies (pygame only)
└── sounds/            # Audio assets directory
```

### Dependencies
- **Python**: 3.8+ (tested with 3.13.5)
- **Pygame**: 2.0+ (using 2.6.1)
- **No NumPy**: Eliminated for better compatibility

### Performance Optimizations
- **Pre-rendered Audio**: Faster loading, no runtime generation
- **Efficient Collision Detection**: Pygame sprite groups
- **Particle System**: Optimized visual effects
- **Resource Management**: Centralized asset loading

---

## 🎨 Visual Design

### Sprite System
- **Shark**: Animated swimming motion
- **Obstacles**: Distinct visual styles (organic coral, metallic shipwrecks)
- **Projectiles**: Weapon-specific appearances
- **Powerups**: Color-coded by type
- **Scaling**: 50% larger than original design for better visibility

### UI Elements
- **Energy Bar**: Visual health indicator
- **Laser Energy**: Weapon charge display
- **Weapon Inventory**: Missile/torpedo counters (max 3 each)
- **Shield Status**: Active protection indicator
- **HUD**: Comprehensive status display

---

## 🚀 Deployment & Distribution

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, Linux
- **Python**: 3.8 or higher
- **Memory**: 256MB RAM minimum
- **Storage**: 50MB for game files

### Installation Process
1. Clone repository
2. Create virtual environment
3. Install pygame dependency
4. Run main.py

---

## 🔄 Version History

### v2.0 (Current) - Audio Optimization
- ✅ Eliminated NumPy dependency
- ✅ Pre-rendered all 16 sound effects as WAV files
- ✅ Improved game startup performance
- ✅ Enhanced cross-platform compatibility
- ✅ Comprehensive README documentation

### v1.0 - Core Implementation
- ✅ Complete gameplay mechanics
- ✅ All weapon systems functional
- ✅ Settings menu with customization
- ✅ Controller support
- ✅ Particle effects system
- ✅ Procedural audio generation (NumPy-based)

---

## 🎯 Future Enhancement Opportunities

### Potential Additions
- **Boss Battles**: Large enemy encounters
- **Level Progression**: Increasing difficulty stages
- **Score Persistence**: High score tracking
- **Additional Weapons**: New weapon types
- **Multiplayer**: Local co-op or competitive modes
- **Mobile Port**: Touch-based controls

### Technical Improvements
- **Sprite Animations**: More detailed character animations
- **Background Music**: Looping soundtrack
- **Save System**: Game state persistence
- **Performance Profiling**: Optimization opportunities

---

## 📋 Testing & Quality Assurance

### Tested Platforms
- ✅ Windows 10/11 with Python 3.13.5
- ✅ Pygame 2.6.1 compatibility
- ✅ Keyboard and controller input
- ✅ Audio system functionality

### Known Issues
- **Pygame DLL Issues**: Resolved with pre-release installation
- **Python 3.13 Compatibility**: Addressed with proper dependency versions

---

This specification reflects the current state of the fully implemented and optimized "Lazer Shark Kill! Kill!" arcade game.