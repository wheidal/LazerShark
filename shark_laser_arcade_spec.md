# Lazer Shark Kill! Kill! - Design Specification v3.0

## Game Overview
**"Lazer Shark Kill! Kill!"** is a top-down, vertically scrolling arcade shooter. You play Subject 13, a shark that escaped Dr. Rask's lab with a laser bolted to its head. You swim up a winding channel through six areas, fight a boss at the end of each, and take your revenge on Dr. Rask in the last one.

The coast scrolls past on both sides. You eat fish to keep your energy up, shoot or dodge whatever is in the way, and pick up upgrades that make your laser stronger.

## Current Status
The whole journey is playable, from the intro to the ending. 347 automated tests drive the real game headlessly.

---

## 🧭 The Journey

Beating a boss moves the run on to the next area. Two areas have an interlude, a different stretch you reach once you're halfway to that area's boss.

| # | Area | Interlude | Special feature | Boss | Boss appears at score |
|---|------|-----------|-----------------|------|----------------------|
| 1 | The Reef | - | - | Giant Moray | 120 |
| 2 | The Ship Graveyard | The Flooded City | Giant wrecks you go around, or through for loot | Giant Squid | 400 |
| 3 | The Volcanic Rift | - | Lava geysers | Magma Crab | 800 |
| 4 | Atlantis | The NASA Graveyard | Guardian statues | Atlantean Guardian | 1300 |
| 5 | The Sunken Lab | - | Laser gates, electric cables | Rival Shark | 1900 |
| 6 | The Lab Core | - | Laser gates, electric cables | Dr. Rask (final) | 2600 |

Each area has its own coast colours, decorations, music, obstacles, enemies and hazards. Areas define these in `areas.py`.

### Bosses
- **Giant Moray:** hides in the rock and lunges across the arena. It attacks faster once it's half dead.
- **Giant Squid:** clings above the wreck. Its tentacles slam down and shield its head until they're destroyed.
- **Magma Crab:** armoured until it overheats. Vents erupt around you, then its shell opens to cool down.
- **Atlantean Guardian:** uses every attack and opens its core after each one.
- **Rival Shark:** Subject 14, built to replace you. Shoot the lit switch to drop its shield.
- **Dr. Rask:** in a walking mech. Its turrets shield it; then you shoot the glass tank he's in.

Beating a boss gives +100 score and refills energy and laser. Beating Dr. Rask plays the ending.

### Story
- An intro cutscene plays before the first run. Jumping straight to a boss skips it.
- Dr. Rask taunts you over the radio when you enter an area, when a boss appears and when you beat one (`story.py`).
- The ending is a cutscene, and then you can hunt again.

---

## 🦈 The Shark

- **Movement:** in all directions within the screen.
- **Energy:** 100 at most. It drains slowly all the time, a little faster while moving. Eating a fish gives +20. You lose when it reaches 0.
- **Laser energy:** each shot costs some. It recharges on its own, faster on easier difficulties.
- **Getting hit:** a real hit, not a slow drain, also knocks your weapon down one level.
- **Coast:** swimming into the coast costs 12 energy once. You're then pushed back into the channel and can't be hurt by the coast again for a moment.

### Weapon Ladder
Each upgrade pickup moves you one step up; each hit moves you one step down. A step up lasts 25 seconds before it drops back one.

| Level | Weapon | What it does |
|-------|--------|--------------|
| 1 | Laser | Straight and reliable. Your starting weapon |
| 2 | Shotgun | Sprays nine plasma balls across a wide arc |
| 3 | Rapid laser | Fires much faster, and empties your laser much faster |
| 4 | Fan laser | Seven shots in a spread |
| 5 | Homing laser | Three shots that curve towards the nearest target ahead, including boss parts |

At the top of the ladder, an upgrade pickup refills your laser instead.

Upgrades come from:
- A pickup that drifts in every 25 seconds, outside boss fights.
- Every 10 tough enemies destroyed.
- Loot inside giant wrecks.
- Destroying an Evil Sub, which drops either a laser cell or an upgrade.

### Pickups
| Pickup | Effect |
|--------|--------|
| **Fish** | +20 energy, +1 score |
| **Zombie fish** | Grey with red X eyes. It bites instead of feeding you. Appears from score 15 |
| **Laser cell** | +30 laser energy |
| **Weapon upgrade** | One step up the weapon ladder |
| **Shield** | Absorbs 100 points of damage for 20 seconds. It flickers for its last 4 seconds |

Shields come from destroying 4 of the same tough enemy, from giant-wreck loot, and from a broken shield, which drops 2 or 3 replacements. Collecting any pickup gives +2 score.

---

## 👾 Enemies

Each area has its own enemy list, and an enemy only appears once your score reaches its minimum. They get tougher by 8% and spawn 5% faster with each area.

| Enemy | From score | Behaviour |
|-------|-----------|-----------|
| Laser Manta | 20 | Stops on a red line, then fires straight down |
| Harpoon Diver | 20 | Fires slow harpoons from beside the coast |
| Pufferfish | 25 | Swells up close and bursts into spines |
| Radioactive Piranha | 30 | Chases you, and leaves radiation behind when killed |
| Urchin Drone | 30 | Sprays needles when destroyed. Kill it from far off |
| Anglerfish | 40 | Its lure looks like an upgrade |
| Cyber Barracuda | 45 | Weak alone, but they come in a weaving V. Wide weapons shred them |
| Hammerhead | 60 | A red line warns of its charge across the screen at your height |
| Evil Sub | 85 | Fires torpedoes and lays mines. Drops a pickup |
| Moray in the rock | 0 | Hides in the coast, eyes glow, then it lunges |
| Guardian Statue | 0 | Red eyes mean it's about to fire (Atlantis) |
| Kamikaze Tuna | 0 | Locks on, then charges. **Switched off for now** |

Kamikaze tuna are switched off to see if the game is better without them. Emptying `DISABLED_ENEMIES` in `enemies.py` brings them back.

---

## 🌊 Obstacles and Hazards

### Obstacles
Coral, shipwrecks, boulders, tumbling rocks, collapsed towers, rocket hulks and dead satellites block the way and can be shot apart. Some need special handling:

| Obstacle | Behaviour |
|----------|-----------|
| **Sea mine** | Senses you close by, blinks, then goes off. Shoot it from outside the blast |
| **Depth charge** | Sinks faster than the coast scrolls and goes off on a timer |
| **Radiation barrel** | Blinks, then leaks a draining cloud. Shoot it first and there's no leak |
| **Jellyfish** | Drift from side to side in swarms. One sting is mild |
| **EMP jellyfish** | Its sting knocks out your laser for 2 seconds, even through a shield |
| **Fishing net** | Doesn't hurt, but tangles you for a moment. Shoot it away |

### Hazards
| Hazard | Behaviour |
|--------|-----------|
| **Ink cloud** | Harmless, but hides whatever is inside |
| **Toxic sludge** | Drains energy and slows you, even shielded |
| **Magnetic field** | Tugs you sideways |
| **Radiation cloud** | Spreads and drains energy. It goes through your shield |
| **Lava geyser** | Glows as a warning, then erupts (Volcanic Rift) |
| **Laser gate** | A wall of laser across the channel. Shoot its green switch to shut it down (Lab) |
| **Electric cable** | Hangs from one bank, sparks, then arcs across part of the channel. Cross while it's dark |
| **Whirlpool** | Drags you towards its core, which hurts. **Switched off for now** |

Whirlpools are switched off to see if the game is better without them. Setting `WHIRLPOOLS_ON = True` in `channel.py` brings them back.

---

## ⚖️ Difficulty

Chosen in the settings menu. It affects the whole run.

| | Easy | Normal | Hard |
|---|------|--------|------|
| Time between enemies | 4.5 s | 2.9 s | 2.0 s |
| Most enemies on screen | 2 | 4 | 6 |
| Laser recharge (per second) | 18 | 12 | 7 |
| Boss health | 60-80 | 90-120 | 130-170 |
| Boss bite damage | 15-20 | 20-30 | 30-40 |

**Easy Mode** is a separate setting that gives unlimited laser energy.

---

## 🏆 Scoring and High Scores

- **Score from:** destroying obstacles and enemies (each has its own reward), eating fish (+1), collecting pickups (+2) and beating bosses (+100).
- **High-score table:** the best 10 runs, with three-letter initials and difficulty, saved in `high_scores.json` beside the settings file.
- **Entering initials:** a score that makes the table asks for initials on the Game Over screen. Pick letters with the arrows or a D-pad, or just type them.
- **Where it's shown:** the Game Over screen shows the table with your entry highlighted, and the title screen takes turns with it.
- **Practice runs aren't recorded:** runs started by jumping to a boss, and Easy Mode runs.

---

## 🕹️ Controls

### Keyboard
| Action | Default key | Remappable |
|--------|-------------|------------|
| Move | Arrow keys | ✅ |
| Fire | Space | ✅ |
| Pause | P | ✅ |
| Quit | Escape | ✅ (Escape always quits too) |
| Full screen | F11 | - |

On the title screen, **S** opens settings and **1-6** jump straight to a boss.

### Controller
Off by default; turn it on in settings.

| Action | Input |
|--------|-------|
| Move | Left stick |
| Fire | A (button 0) |
| Pause | Start |

### Settings Menu
Remap keys, controller on/off, Easy Mode, music on/off, music volume and difficulty. Settings are saved in `game_settings.json`.

---

## 🎬 Screens

1. **Title:** the game plays itself behind the title, taking turns with the high-score table.
2. **Intro cutscene:** the story so far.
3. **Briefing:** pages showing every pickup, weapon, hazard and enemy. Any key moves on.
4. **Play.**
5. **Game Over or REVENGE!:** the score, initials entry if it made the table, and the table.

---

## 🎵 Audio

- **Sound effects:** 24 WAV files in `sounds/`.
- **Music:** 10 placeholder tracks in `sounds/music/`: the title, six area tracks (the interludes reuse two of them), boss fights, the final boss and the victory.
- **Placeholders:** `tools/make_audio.py` writes the placeholder music and sounds. Any file can be swapped for a real one with the same name.
- **No sound card:** the game runs silently if there's no audio device.

---

## 🛠️ Technical Architecture

### Dependencies
- **Python 3.13** (tests that change the game's state while it runs need 3.13)
- **Pygame 2.6**

### Main Modules
```
main.py              Game loop, menus and state
attract.py           Title screen demo and briefing pages
areas.py             The areas and interludes
channel.py           The scrolling coast and its zones
boss.py, bosses.py   The boss fights and the boss roster
enemies.py           Enemy types, spawning and toughening
obstacle.py          Obstacles, mines, barrels and jellyfish
hazards.py           Radiation, whirlpools and fields
features.py          Lava geysers, laser gates and electric cables
giant_wreck.py       Giant wrecks
weapons.py           The weapon ladder and bolts
food.py, powerup.py  Fish and pickups
highscores.py        High-score table and initials entry
story.py, cutscenes.py  Radio taunts, intro and ending
music.py             Music director
hud.py               Energy, shield, laser and score display
shark_look.py, player.py, player_enhanced.py  The shark
graphics_enhancements.py, particle.py         Effects
settings_manager.py, resources.py            Settings and file paths
android_controls.py  Touch controls for the Android port (in progress)
tests/               Headless tests using SDL's dummy drivers
```

### Timing
The simulation steps at a fixed 60 Hz, so game speed doesn't depend on frame rate. It runs at most 5 steps per frame, then slows down instead of skipping ahead.

### Packaging
- **Windows:** `build_windows_installer.py` runs PyInstaller (`LazerSharkKillKill.spec`) and Inno Setup (`installer_setup.iss`), giving an installer and a portable zip. GitHub Actions builds both on every pull request and publishes them as a release when a `v*` tag is pushed. A packaged build saves settings and high scores per user in `%APPDATA%\LazerSharkKillKill`.
- **Android:** `buildozer.spec` and `android_porting_guide.md`.

---

## 📋 Testing

- 348 tests run the real game headlessly through a scripted harness (`tests/conftest.py`), plus unit tests for each part.
- Run them with `pytest`. The full suite takes about 5-7 minutes.
- Not yet covered: balance testing by people, real controllers and the Windows build.

---

## 🎯 Still To Do

- **Save system:** keep a run in progress between sessions.
- **Multiplayer:** local co-op or competitive play.
- **Android port:** touch controls are started (`android_controls.py`), but nothing shows it has been tested on a device or published.
- **Decide on tuna and whirlpools:** both are switched off while trying the game without them.
- **Balance testing** by real players.
- **Performance:** the worst frame in one test run took 25 ms, over the 16.7 ms available, and the cause isn't known.
- **Real music and sounds** to replace the placeholders.
- **Best score during play:** possibly show it in the corner of the screen.

---

## 🔄 Version History

### v3.0 (Current)
- **Journey:** six areas and two interludes, each with its own boss, look, music and hazards.
- **Bosses:** Giant Moray, Giant Squid, Magma Crab, Atlantean Guardian, Rival Shark and Dr. Rask.
- **Story:** Dr. Rask's radio taunts, plus intro and ending cutscenes.
- **Weapons:** a five-step weapon ladder in place of missiles, torpedoes and the triple laser.
- **Enemies:** twelve types that get tougher area by area.
- **Difficulty levels** and a scrolling channel with a coastline.
- **Front end:** a title screen that plays itself, and a briefing.
- **High scores** with arcade-style initials.
- **Testing:** a headless test suite.

### v2.0 - Audio Optimization
- Removed the NumPy dependency by pre-rendering all sound effects as WAV files.

### v1.0 - Core Implementation
- Shark, laser, missiles and torpedoes, obstacles, shields, settings menu and controller support.
