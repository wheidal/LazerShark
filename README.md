# 🦈 Lazer Shark Kill! Kill!

A thrilling underwater arcade shooter where you control a laser-equipped shark navigating through dangerous ocean depths!

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Pygame](https://img.shields.io/badge/pygame-v2.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🎮 Game Overview

Take control of a powerful shark armed with lasers, missiles, and torpedoes as you navigate through treacherous underwater environments. Avoid obstacles, collect food to maintain energy, gather powerups to enhance your weapons, and survive as long as possible in this action-packed arcade experience!

### ✨ Key Features

- **🔫 Multiple Weapon Systems**: Lasers, missiles, and homing torpedoes
- **🛡️ Shield System**: Temporary protection from obstacles
- **🐟 Energy Management**: Eat fish to maintain energy levels
- **🎵 Immersive Audio**: 16 custom underwater sound effects
- **🌊 Beautiful Visuals**: Animated water caustics, floating bubbles, and swaying kelp
- **🎮 Controller Support**: Full gamepad compatibility
- **⚙️ Customizable Controls**: Remap keys to your preference
- **😌 Easy Mode**: For casual players

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Windows, macOS, or Linux

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/lazer-shark-arcade.git
   cd lazer-shark-arcade
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the game:**
   ```bash
   python main.py
   ```

## 🎯 How to Play

### 🕹️ Default Controls

| Action | Keyboard | Controller |
|--------|----------|------------|
| Move | Arrow Keys | Left Stick |
| Fire Laser | Space | A Button |
| Fire Missile | Left Alt | B Button |
| Fire Torpedo | Left Ctrl | X Button |
| Pause | P | Start Button |
| Restart Game (Game Over) | Any Key | Any Button (except Start) |
| Quit | Escape | Start Button (Game Over) |

### 🎮 Gameplay Mechanics

#### Weapons
- **🔴 Laser**: Fast-firing energy weapon (requires energy)
- **🟠 Missile**: Powerful explosive projectile (limited ammo)
- **🔵 Torpedo**: Homing weapon that tracks nearest obstacle (limited ammo)

#### Energy System
- Energy depletes while moving and firing lasers
- Eat small fish to restore energy
- Running out of energy means game over!

#### Obstacles
- **🪸 Coral Reefs**: Organic obstacles that crack and break
- **🚢 Shipwrecks**: Metallic obstacles with hollow sounds
- **🤖 Friendly Submarines**: Avoid these allies!

#### Powerups
- **🔴 Laser Powerup**: Restores laser energy
- **🟠 Missile Powerup**: Adds 2 missiles to inventory
- **🔵 Torpedo Powerup**: Adds 1 torpedo to inventory
- **🛡️ Shield Powerup**: Temporary invincibility (spawns after destroying 2 identical obstacles)

## 🛠️ Game Features

### 🎵 Audio System
The game features a complete underwater audio experience with 16 custom sound effects:
- Weapon firing sounds (laser, missile, torpedo)
- Material-specific collision sounds (coral, metal, submarine)
- UI feedback sounds
- Ambient ocean atmosphere

### 🎨 Visual Effects
- **Dynamic underwater background** with depth-based color gradients
- **Animated water caustics** creating realistic light patterns
- **Floating bubble particles** for depth perception
- **Swaying kelp forests** in the background
- **Particle explosions** for impacts and destructions

### ⚙️ Customization Options
- **Key Remapping**: Customize all controls to your preference
- **Controller Toggle**: Enable/disable gamepad support
- **Easy Mode**: Unlimited laser energy for casual play

## 📁 Project Structure

```
lazer-shark-arcade/
├── main.py                 # Main game loop and logic
├── player.py              # Shark player class
├── obstacle.py            # Obstacle classes (coral, shipwrecks)
├── food.py               # Fish food class
├── projectile.py         # Weapon projectile classes
├── powerup.py            # Powerup classes
├── particle.py           # Particle effect system
├── ui.py                 # User interface components
├── settings.py           # Game configuration
├── resources.py          # Resource management
├── requirements.txt      # Python dependencies
├── sounds/              # Pre-rendered audio files
│   ├── laser.wav
│   ├── missile.wav
│   ├── torpedo.wav
│   ├── coral_collision.wav
│   ├── shipwreck_collision.wav
│   ├── submarine_collision.wav
│   ├── fatal_collision.wav
│   ├── food_eat.wav
│   ├── powerup_collect.wav
│   ├── shield_activate.wav
│   ├── obstacle_destroy.wav
│   ├── menu_beep.wav
│   ├── upgrade_activate.wav
│   ├── ambient_ocean.wav
│   └── ...
├── assets/              # Game sprites and images
└── README.md           # This file
```

## 🔧 Development

### 🏗️ Architecture

The game follows a modular design pattern:
- **Component-based entities** for game objects
- **Sprite groups** for efficient collision detection
- **Event-driven input system** supporting multiple input methods
- **Particle system** for visual effects
- **Audio manager** with pre-rendered sound effects

### 🎵 Audio System

The game originally used procedural audio generation with NumPy, but has been optimized to use pre-rendered WAV files for:
- Better performance
- Improved compatibility
- Easier audio editing and customization

### 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🐛 Troubleshooting

### Common Issues

#### Pygame Import Error on Windows
If you encounter DLL load errors with pygame on Python 3.13:
```bash
pip uninstall pygame
pip install pygame --pre
```

#### Audio Not Working
Ensure all files in the `sounds/` directory are present. If sounds are missing, the game will continue but audio may be silent.

#### Controller Not Detected
- Ensure your controller is connected before starting the game
- Enable controller support in the settings menu
- The game supports most standard gamepads (Xbox, PlayStation, etc.)

## 📋 Requirements

- **Python**: 3.8+
- **Pygame**: 2.0+
- **Operating System**: Windows 10+, macOS 10.14+, or Linux

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Pygame](https://www.pygame.org/)
- Inspired by classic arcade shooters
- Sound effects generated using procedural audio techniques
- Special thanks to the Python gaming community

## 📸 Screenshots

*Add screenshots of your game here when available*

---

**Enjoy the underwater mayhem! 🦈💥**

For questions, suggestions, or bug reports, please open an issue on GitHub.
