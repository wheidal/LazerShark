"""
Main entry point for Shark Laser Arcade Game.
Handles game loop and state management.
"""

import pygame
import sys
import random
import os
import math
from player import Shark
from player_enhanced import SharkWithSprites
from obstacle import OBSTACLE_TYPES
from food import SmallFish
from projectile import Laser, Missile, Torpedo
from powerup import LaserPowerup, MissilePowerup, TorpedoPowerup, ShieldPowerup
from particle import ParticleEmitter
from graphics_enhancements import (
    GraphicsEnhancer, ParticleEffects, AnimatedSprite, 
    ScreenEffects, EnhancedParticle
)
from settings_manager import SettingsManager
from resources import resource_path
from channel import ChannelDirector, BANK_DAMAGE, BANK_INVULN_MS, BANK_PUSH
from hud import Hud
from shark_look import SharkLook
from attract import AttractMode, Briefing
from boss import CONTACT_INVULN_MS, DEFAULT_DIFFICULTY, DIFFICULTIES, LASER_RECHARGE, VICTORY_SCORE
from bosses import BOSS_ROSTER
from enemies import ENEMY_LIMIT, ENEMY_SPAWN_MS, Enemy, choose_enemy
from weapons import WEAPONS, WeaponPowerup, WeaponState

# The simulation always advances in 60 Hz steps, so game speed doesn't depend on frame rate
STEP_MS = 1000 / 60
MAX_STEPS_PER_FRAME = 5
RESTART_LOCK_MS = 1000  # Ignore restart input briefly so mashing fire can't skip Game Over


class SilentSound:
    """Stands in for every sound when no audio device is available"""

    def play(self, *args, **kwargs):
        pass


def pixels_touch(sprite, other):
    """Pixel-accurate check, for sprites whose rects are mostly transparent"""
    return sprite.rect.colliderect(other.rect) and pygame.sprite.collide_mask(sprite, other)


def start_channel(banks, all_sprites):
    """Create a new channel with its coastline already covering the screen"""
    channel = ChannelDirector()
    for chunk, y in channel.prefill():
        new_banks = chunk.build(y)
        banks.add(new_banks)
        all_sprites.add(new_banks)
    return channel


def load_sound(filename):
    """Load a sound file from the sounds directory"""
    if not pygame.mixer.get_init():
        return SilentSound()
    try:
        sound_path = resource_path('sounds', filename)
        if os.path.exists(sound_path):
            return pygame.mixer.Sound(sound_path)
        else:
            print(f"Warning: Sound file not found: {sound_path}")
            # Return a dummy sound to prevent crashes
            return pygame.mixer.Sound(buffer=b'\x00' * 1024)
    except pygame.error as e:
        print(f"Error loading sound {filename}: {e}")
        return pygame.mixer.Sound(buffer=b'\x00' * 1024)


def main():
    pygame.init()
    # --- Load Pre-rendered Sound Effects ---
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(8)  # Ensure enough channels for all sounds
    except pygame.error as e:
        print(f"No audio device, continuing without sound: {e}")
    audio_available = pygame.mixer.get_init() is not None
    
    print("Loading sound effects...")
    
    # Load all sound effects
    laser_sound = load_sound('laser.wav')
    laser_triple_sound = load_sound('laser_triple.wav')
    missile_sound = load_sound('missile.wav')
    torpedo_sound = load_sound('torpedo.wav')
    
    # Collision sounds
    coral_collision_sound = load_sound('coral_collision.wav')
    shipwreck_collision_sound = load_sound('shipwreck_collision.wav')
    submarine_collision_sound = load_sound('submarine_collision.wav')
    generic_collision_sound = load_sound('generic_collision.wav')
    fatal_collision_sound = load_sound('fatal_collision.wav')
    
    # Game event sounds
    food_eat_sound = load_sound('food_eat.wav')
    powerup_collect_sound = load_sound('powerup_collect.wav')
    shield_activate_sound = load_sound('shield_activate.wav')
    obstacle_destroy_sound = load_sound('obstacle_destroy.wav')
    
    # UI sounds
    menu_beep_sound = load_sound('menu_beep.wav')
    upgrade_activate_sound = load_sound('upgrade_activate.wav')
    
    # Ambient sound
    ambient_ocean_sound = load_sound('ambient_ocean.wav')
    
    # Background music
    background_music_path = resource_path('sounds', 'shark.wav')
    
    print("All sound effects loaded successfully!")
    # Track destroyed obstacles for shield spawn
    destroyed_counts = {}

    # Drawn at 800x600 and scaled up to suit the monitor; F11 goes full screen
    try:
        screen = pygame.display.set_mode((800, 600), pygame.SCALED | pygame.RESIZABLE)
    except pygame.error:
        screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Lazer Shark Kill! Kill!")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)
    title_font = pygame.font.SysFont(None, 72)
    
    # Initialize graphics enhancer
    graphics_enhancer = GraphicsEnhancer(screen)
    enhanced_particles = pygame.sprite.Group()

    # --- Settings Menu ---
    # Load settings from file
    settings_manager = SettingsManager()
    
    # Load saved settings
    keymap = {}
    saved_keymap = settings_manager.get('keymap', {})
    for action, key_code in saved_keymap.items():
        keymap[action] = key_code
    
    controller_enabled = settings_manager.get('controller_enabled', False)
    easy_mode = settings_manager.get('easy_mode', False)
    difficulty = settings_manager.get('difficulty', DEFAULT_DIFFICULTY)
    if difficulty not in DIFFICULTIES:
        difficulty = DEFAULT_DIFFICULTY
    
    # Music settings
    music_enabled = settings_manager.get('music_enabled', True)
    music_volume = settings_manager.get('music_volume', 0.5)
    sfx_volume = settings_manager.get('sfx_volume', 1.0)
    
    # Initialize controller support
    pygame.joystick.init()
    controller = None
    if pygame.joystick.get_count() > 0:
        controller = pygame.joystick.Joystick(0)
        controller.init()
        print(f"Controller detected: {controller.get_name()}")
    def run_settings():
        nonlocal controller_enabled, easy_mode, difficulty, music_enabled, music_volume
        menu_items = [
            'Remap Keys',
            'Toggle Controller',
            'Toggle Easy Mode',
            'Toggle Music',
            'Music Volume',
            'Difficulty',
            'Continue'
        ]
        selected = 0
        in_settings = True
        adjusting_volume = False
        while in_settings:
            screen.fill((0, 0, 64))
            title = title_font.render("Settings", True, (255, 255, 0))
            screen.blit(title, (250, 80))
        
            # Show volume adjustment instructions when adjusting
            if adjusting_volume:
                instructions = font.render("Use LEFT/RIGHT arrows to adjust, ENTER to confirm", True, (200, 200, 200))
                screen.blit(instructions, (120, 540))
            for i, item in enumerate(menu_items):
                color = (255, 255, 255) if i != selected else (0, 255, 0)
                if item == 'Toggle Controller':
                    label = f"{item}: {'ON' if controller_enabled else 'OFF'}"
                elif item == 'Toggle Easy Mode':
                    label = f"{item}: {'ON' if easy_mode else 'OFF'}"
                elif item == 'Toggle Music':
                    label = f"{item}: {'ON' if music_enabled else 'OFF'}"
                elif item == 'Music Volume':
                    label = f"{item}: {int(music_volume * 100)}%"
                    # Draw volume bar
                    if i == selected and adjusting_volume:
                        pygame.draw.rect(screen, (100, 100, 100), (420, 180 + i * 50, 200, 20))
                        pygame.draw.rect(screen, (0, 255, 0), (420, 180 + i * 50, int(200 * music_volume), 20))
                elif item == 'Difficulty':
                    label = f"{item}: {difficulty.upper()}"
                else:
                    label = item
                text = font.render(label, True, color)
                screen.blit(text, (220, 180 + i * 50))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if not adjusting_volume:
                        if event.key == pygame.K_UP:
                            menu_beep_sound.play()
                            selected = (selected - 1) % len(menu_items)
                        elif event.key == pygame.K_DOWN:
                            menu_beep_sound.play()
                            selected = (selected + 1) % len(menu_items)
                        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                            powerup_collect_sound.play()  # Menu selection sound
                            if menu_items[selected] == 'Remap Keys':
                                # Simple remap: cycle through actions and wait for key press
                                remap_actions = list(keymap.keys())
                                for action in remap_actions:
                                    waiting = True
                                    while waiting:
                                        screen.fill((0, 0, 64))
                                        prompt = font.render(f"Press new key for {action.upper()}", True, (255, 255, 255))
                                        screen.blit(prompt, (180, 280))
                                        pygame.display.flip()
                                        for e in pygame.event.get():
                                            if e.type == pygame.QUIT:
                                                pygame.quit()
                                                sys.exit()
                                            if e.type == pygame.KEYDOWN:
                                                menu_beep_sound.play()  # Key remap confirmation
                                                keymap[action] = e.key
                                                waiting = False
                            elif menu_items[selected] == 'Toggle Controller':
                                controller_enabled = not controller_enabled
                                if controller_enabled and not controller:
                                    print("Warning: No controller detected. Please connect a controller.")
                                elif controller_enabled and controller:
                                    print(f"Controller enabled: {controller.get_name()}")
                                else:
                                    print("Controller disabled")
                            elif menu_items[selected] == 'Toggle Easy Mode':
                                easy_mode = not easy_mode
                            elif menu_items[selected] == 'Toggle Music':
                                music_enabled = not music_enabled
                                if audio_available:
                                    if music_enabled:
                                        pygame.mixer.music.unpause()
                                    else:
                                        pygame.mixer.music.pause()
                            elif menu_items[selected] == 'Music Volume':
                                adjusting_volume = True
                            elif menu_items[selected] == 'Difficulty':
                                levels = list(DIFFICULTIES)
                                difficulty = levels[(levels.index(difficulty) + 1) % len(levels)]
                            elif menu_items[selected] == 'Continue':
                                # Save settings before continuing
                                settings_manager.update(
                                    keymap=keymap,
                                    controller_enabled=controller_enabled,
                                    easy_mode=easy_mode,
                                    difficulty=difficulty,
                                    music_enabled=music_enabled,
                                    music_volume=music_volume,
                                    sfx_volume=sfx_volume
                                )
                                settings_manager.save_settings()
                                in_settings = False
                    else:
                        # Volume adjustment mode
                        if event.key == pygame.K_LEFT:
                            music_volume = max(0, music_volume - 0.1)
                            if audio_available:
                                pygame.mixer.music.set_volume(music_volume)
                            menu_beep_sound.play()
                        elif event.key == pygame.K_RIGHT:
                            music_volume = min(1.0, music_volume + 0.1)
                            if audio_available:
                                pygame.mixer.music.set_volume(music_volume)
                            menu_beep_sound.play()
                        elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                            adjusting_volume = False
                            powerup_collect_sound.play()


    # Start background music
    if not audio_available:
        music_enabled = False
    elif os.path.exists(background_music_path):
        pygame.mixer.music.load(background_music_path)
        pygame.mixer.music.set_volume(music_volume)
        if music_enabled:
            pygame.mixer.music.play(-1)  # Loop indefinitely
        else:
            # Started paused, so the Settings toggle can turn it on from the title screen
            pygame.mixer.music.play(-1)
            pygame.mixer.music.pause()
        print("Background music loaded and playing!")
    else:
        print(f"Warning: Background music file not found: {background_music_path}")
        music_enabled = False
    
    # Start ambient ocean sound loop on a dedicated channel
    if audio_available:
        ambient_channel = pygame.mixer.Channel(7)  # Use last channel for ambient
        ambient_channel.set_volume(sfx_volume * 0.3)  # Ambient at 30% of SFX volume
        ambient_channel.play(ambient_ocean_sound, loops=-1)  # Loop indefinitely
    
    # Title screen: the game plays itself until someone presses a key
    attract = AttractMode(screen, graphics_enhancer)
    start_boss = None  # Number keys jump straight to a boss
    splash = True
    while splash:
        dt = clock.tick(60)
        attract.update(dt)
        attract.draw_title(pygame.time.get_ticks())
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_s:
                    run_settings()
                elif pygame.K_1 <= event.key < pygame.K_1 + len(BOSS_ROSTER):
                    start_boss = event.key - pygame.K_1
                    splash = False
                else:
                    splash = False
            if event.type == pygame.JOYBUTTONDOWN:
                splash = False

    # Quick reminder of what everything does, which any key skips
    pygame.event.clear()
    briefing = Briefing(screen, keymap)
    while not briefing.finished:
        dt = clock.tick(60)
        attract.update(dt)
        attract.draw_world()
        briefing.draw(dt)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            elif event.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN):
                briefing.next_page()

    # Clear event queue and add a short delay to ensure splash screen is removed
    pygame.event.clear()
    pygame.time.wait(100)

    hud = Hud()

    # Use enhanced shark with sprites if available, fallback to procedural
    try:
        shark = SharkWithSprites(400, 580)  # Enhanced sprite-based shark
        print("Using enhanced shark sprites from hai_0.png")
    except Exception as e:
        print(f"Could not load enhanced sprites, using procedural shark: {e}")
        shark = Shark(400, 580)  # Fallback to procedural shark
    all_sprites = pygame.sprite.Group()  # The shark is drawn by SharkLook
    shark_look = SharkLook()
    obstacles = pygame.sprite.Group()
    foods = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    enemy_shots = pygame.sprite.Group()
    banks = pygame.sprite.Group()
    channel = start_channel(banks, all_sprites)
    bank_invuln = 0
    boss_phase = None  # Then 'approach' while the arena scrolls in, 'fight', and 'beaten'
    boss = None
    boss_invuln = 0
    next_boss = 0
    banner = None
    banner_timer = 0
    particles = pygame.sprite.Group()
    emitter = ParticleEmitter(particles)
    
    # Track time for animations
    # Weapon upgrade system
    obstacles_spawned = 0
    obstacles_destroyed = 0
    weapon = WeaponState()
    running = True
    game_over = False
    paused = False
    energy = 100
    spawn_timer = 0
    powerup_timer = 0
    enemy_timer = 0
    score = 0
    restart_lock = 0
    step_backlog = 0

    # Shield powerup state - Enhanced system
    shield_active = False
    shield_strength = 0  # 0-100, starts at 100 when activated
    shield_timer = 0
    next_shield_spawn = random.randint(180000, 300000)  # 3-5 min in ms
    
    if start_boss is not None:
        next_boss = start_boss
        score = BOSS_ROSTER[start_boss][1]

    while running:
        frame_ms = clock.tick(60)
        restart_requested = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                # Esc always exits, so a bad remap can't trap the player
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif event.key in (pygame.K_ESCAPE, keymap['quit']):
                    running = False
                elif event.key == keymap['pause'] and not game_over:
                    paused = not paused
                elif game_over:
                    restart_requested = True
            if event.type == pygame.JOYBUTTONDOWN and controller_enabled and controller:
                if event.button == 7 or event.button == 9:  # Start button on most controllers
                    if game_over:
                        running = False
                    else:
                        paused = not paused
                elif game_over:
                    restart_requested = True

        if game_over:
            restart_lock -= frame_ms
            if restart_requested and restart_lock <= 0:
                try:
                    shark = SharkWithSprites(400, 580)
                except Exception:
                    shark = Shark(400, 580)
                all_sprites = pygame.sprite.Group()
                shark_look.reset()
                obstacles.empty()
                foods.empty()
                projectiles.empty()
                powerups.empty()
                enemy_shots.empty()
                banks.empty()
                channel = start_channel(banks, all_sprites)
                bank_invuln = 0
                boss_phase = None
                boss = None
                boss_invuln = 0
                next_boss = 0
                banner = None
                banner_timer = 0
                particles.empty()
                enhanced_particles.empty()
                energy = 100
                spawn_timer = 0
                powerup_timer = 0
                enemy_timer = 0
                shield_active = False
                shield_strength = 0
                weapon = WeaponState()
                obstacles_destroyed = 0
                destroyed_counts = {}
                score = 0
                step_backlog = 0
                game_over = False
        if game_over:
            screen.fill((0, 0, 64))
            if controller_enabled and controller:
                # Show controller-specific instructions
                game_over_text = font.render("Game Over! Press any button to play again", True, (255, 0, 0))
                screen.blit(game_over_text, (120, 260))
                controller_text = font.render("(Start button to exit)", True, (255, 255, 255))
                screen.blit(controller_text, (270, 290))
            else:
                # Show keyboard instructions
                game_over_text = font.render("Game Over! Press any key to play again or ESC to exit.", True, (255, 0, 0))
                screen.blit(game_over_text, (80, 280))
            energy_text = font.render(f"Final Energy: {max(0, int(energy))}", True, (255, 255, 255))
            screen.blit(energy_text, (300, 320))
            final_score_text = font.render(f"Final Score: {score}", True, (255, 255, 0))
            screen.blit(final_score_text, (300, 350))
            pygame.display.flip()
            continue

        if paused:
            screen.fill((0, 0, 64))
            if controller_enabled and controller:
                pause_text = font.render("Paused - Press Start to resume", True, (255, 255, 0))
                screen.blit(pause_text, (200, 280))
            else:
                pause_text = font.render(f"Paused - Press '{pygame.key.name(keymap['pause']).upper()}' to resume", True, (255, 255, 0))
                screen.blit(pause_text, (220, 280))
            pygame.display.flip()
            continue

        graphics_enhancer.update(frame_ms)

        step_backlog += frame_ms
        steps = round(step_backlog / STEP_MS)
        if steps > MAX_STEPS_PER_FRAME:  # Too far behind to catch up: slow down instead
            steps = MAX_STEPS_PER_FRAME
            step_backlog = 0
        else:
            step_backlog -= steps * STEP_MS

        for _ in range(steps):
            dt = STEP_MS
            enhanced_particles.update()

            keys = pygame.key.get_pressed()
        
            # Controller support
            controller_fire = False
            controller_missile = False
            controller_torpedo = False
        
            if controller_enabled and controller:
                # Get controller input
                # Left stick for movement (axis 0 = left/right, axis 1 = up/down)
                x_axis = controller.get_axis(0) if controller.get_numaxes() > 0 else 0
                y_axis = controller.get_axis(1) if controller.get_numaxes() > 1 else 0
            
                # Deadzone to prevent drift
                deadzone = 0.2
                if abs(x_axis) < deadzone:
                    x_axis = 0
                if abs(y_axis) < deadzone:
                    y_axis = 0
            
                # Controller button mapping (common gamepad layout)
                # Button 0 (A/X) = Fire laser
                # Button 1 (B/Circle) = Fire missile  
                # Button 2 (X/Square) = Fire torpedo
                # Button 7 (Start) = Pause
                controller_fire = controller.get_button(0) if controller.get_numbuttons() > 0 else False
                controller_missile = controller.get_button(1) if controller.get_numbuttons() > 1 else False
                controller_torpedo = controller.get_button(2) if controller.get_numbuttons() > 2 else False
            
                # Use controller or keyboard input
                move = {
                    'left': keys[keymap['left']] or x_axis < 0,
                    'right': keys[keymap['right']] or x_axis > 0,
                    'up': keys[keymap['up']] or y_axis < 0,
                    'down': keys[keymap['down']] or y_axis > 0
                }
            else:
                # Use remapped keys for movement and actions
                move = {
                'left': keys[keymap['left']],
                'right': keys[keymap['right']],
                'up': keys[keymap['up']],
                'down': keys[keymap['down']]
            }
            # Update shark with movement input
            if hasattr(shark, 'update_with_input'):
                shark.update_with_input(move, dt)
            else:
                shark.update(dt, move)
            obstacles.update()
            foods.update()
            projectiles.update()
            powerups.update()
            enemy_shots.update()
            for sprite in obstacles.sprites():
                if isinstance(sprite, Enemy):
                    enemy_shots.add(sprite.new_shots)
                    all_sprites.add(sprite.new_shots)
                    # Anything released inside the reef would just sit there out of reach
                    released = [thing for thing in sprite.new_obstacles
                                if not pygame.sprite.spritecollideany(thing, banks, pixels_touch)]
                    obstacles.add(released)
                    all_sprites.add(released)
                    sprite.steer_clear_of(banks)
                    sprite.new_shots = []
                    sprite.new_obstacles = []
            particles.update()

            shark.laser_energy = min(100, shark.laser_energy + LASER_RECHARGE[difficulty] * STEP_MS / 1000)

            # Firing controls (remapped + controller support)
            if keys[keymap['fire']] or controller_fire:
                # Easy mode: unlimited laser energy
                if easy_mode:
                    shark.laser_energy = 100
                if shark.fire_laser(weapon.cost, weapon.cooldown):
                    shots = weapon.fire(shark.rect.centerx, shark.rect.top)
                    projectiles.add(shots)
                    all_sprites.add(shots)
                    if len(shots) > 1:
                        laser_triple_sound.play()  # Different sound for spreads
                    else:
                        laser_sound.play()
            if keys[keymap['missile']] or controller_missile:
                if shark.fire_missile():
                    missile = Missile(shark.rect.centerx, shark.rect.top)
                    projectiles.add(missile)
                    all_sprites.add(missile)
                    missile_sound.play()
            if keys[keymap['torpedo']] or controller_torpedo:
                if shark.fire_torpedo():
                    # Find nearest obstacle
                    nearest = None
                    min_dist = float('inf')
                    for obs in list(obstacles) + (boss.targets() if boss else []):
                        dist = abs(obs.rect.centerx - shark.rect.centerx) + abs(obs.rect.centery - shark.rect.centery)
                        if dist < min_dist:
                            min_dist = dist
                            nearest = obs
                    torpedo = Torpedo(shark.rect.centerx, shark.rect.top, target=nearest)
                    projectiles.add(torpedo)
                    all_sprites.add(torpedo)
                    torpedo_sound.play()

            # Energy drains while swimming (remapped) - Rebalanced for better gameplay
            if move['left'] or move['right'] or move['up'] or move['down']:
                energy -= 0.06  # Reduced from 0.08 for better balance
            else:
                energy -= 0.02  # Idle drain
            energy = max(0, min(energy, 100))

            # Extend the coastline as it scrolls into view
            arena_locked = boss_phase == 'fight'  # The coast holds still so the eel's lair stays put
            chunk = None if arena_locked else channel.update(score)
            if chunk:
                new_banks = chunk.build()
                banks.add(new_banks)
                all_sprites.add(new_banks)

            # Reaching the boss score opens up the arena ahead
            if boss_phase != 'approach' and boss_phase != 'fight' and next_boss < len(BOSS_ROSTER):
                boss_class, boss_score = BOSS_ROSTER[next_boss]
                if score < boss_score:
                    boss_class = None
            else:
                boss_class = None
            if boss_class:
                boss_phase = 'approach'
                channel.enter_arena(boss_class.arena_reef)
                banner = boss_class.arrival
                banner_timer = 4000
            if boss_phase == 'approach' and channel.arena_ready and not obstacles and not enemy_shots:
                boss_phase = 'fight'
                boss = BOSS_ROSTER[next_boss][0](*channel.arena_edges, difficulty)
                print(f"{boss.name} ({difficulty}): health {boss.health}, bite {boss.bite_damage}, warning {boss.warn_steps} steps")
                # Everyone starts the fight able to win it, however the journey went
                shark.laser_energy = 100
                shark.missiles = max(shark.missiles, 2)
                shark.torpedoes = max(shark.torpedoes, 1)
                banner = f"{boss.name}!"
                banner_timer = 2000
            banner_timer -= dt

            # Spawn obstacles and food every 1.5 seconds, inside the channel
            spawn_timer += dt
            if spawn_timer > 1500:
                spawn_timer = 0
                kinds = channel.obstacle_kinds()  # The arena has none, even while leaving it after a win
                if kinds and random.random() < 0.5 and boss_phase not in ('approach', 'fight'):  # 50% fish
                    kind = OBSTACLE_TYPES[random.choice(kinds)]
                    spawn_x = channel.spawn_x(kind.WIDTH, blocking=True, height=kind.HEIGHT)
                    if spawn_x is not None:
                        new_obstacles = kind.create(spawn_x)
                        obstacles.add(new_obstacles)
                        all_sprites.add(new_obstacles)
                else:
                    fish = SmallFish(channel.spawn_x(26), -10)
                    foods.add(fish)
                    all_sprites.add(fish)

            # Spawn powerups every 4 seconds
            powerup_timer += dt
            if powerup_timer > 4000:
                powerup_timer = 0
                px = channel.spawn_x(30)
                # Mostly lasers during a fight, so nobody is left unable to hurt the boss
                ptype = random.choice(['laser', 'laser', 'missile', 'torpedo'] if boss else ['laser', 'missile', 'torpedo', 'weapon'])
                if ptype == 'weapon':
                    p = WeaponPowerup(px, -16, random.choice(list(WEAPONS)))
                elif ptype == 'laser':
                    p = LaserPowerup(px, -16)
                elif ptype == 'missile':
                    p = MissilePowerup(px, -16)
                else:
                    p = TorpedoPowerup(px, -16)
                powerups.add(p)
                all_sprites.add(p)

            # Spawn enemies, up to the limit for this difficulty
            enemy_timer += dt
            if enemy_timer > ENEMY_SPAWN_MS[difficulty] and boss_phase not in ('approach', 'fight'):
                enemy_timer = 0
                on_screen = sum(isinstance(sprite, Enemy) for sprite in obstacles)
                kind = choose_enemy(channel.enemy_kinds(), score)
                if kind and on_screen < ENEMY_LIMIT[difficulty]:
                    spawn_x = channel.spawn_x(kind.WIDTH, blocking=True, height=kind.HEIGHT)
                    if spawn_x is not None:
                        new_enemies = kind.create(spawn_x, shark.rect)
                        obstacles.add(new_enemies)
                        all_sprites.add(new_enemies)

            # Scroll obstacles, food and powerups downward
            for sprite in obstacles:
                sprite.rect.y += 3
                if sprite.rect.top > 600:
                    sprite.kill()
            for sprite in banks:
                if arena_locked:
                    break
                sprite.rect.y += 3
                if sprite.rect.top > 600:
                    sprite.kill()
            for sprite in foods:
                sprite.rect.y += 3
                if sprite.rect.top > 600:
                    sprite.kill()
            for sprite in powerups:
                sprite.rect.y += 3
                if sprite.rect.top > 600:
                    sprite.kill()

            energy_before_hits = energy
            shield_before_hits = shield_strength if shield_active else 0

            # Collision detection
            # Shark hits obstacle: how much it costs depends on the obstacle
            blown_up = []
            hit = pygame.sprite.spritecollide(shark, obstacles, False, pixels_touch)
            if hit:
                if shield_active and shield_strength > 0:
                    shield_activate_sound.play()  # Play shield sound when it blocks damage
                    shield_strength -= sum(obstacle.damage for obstacle in hit)
                    print(f"Shield protected the shark! Shield strength: {shield_strength:.1f}")
                
                    # Check if shield is depleted
                    if shield_strength <= 0:
                        shield_active = False
                        shield_strength = 0
                        print("Shield depleted! Spawning replacement powerups...")
                        # Spawn 2-3 shield powerups when shield breaks
                        for i in range(random.randint(2, 3)):
                            px = channel.spawn_x(26)
                            shield_powerup = ShieldPowerup(px, -16)
                            powerups.add(shield_powerup)
                            all_sprites.add(shield_powerup)
                
                    for obstacle in hit:
                        # Enhanced explosion effect for shield-blocked obstacles
                        ParticleEffects.create_explosion(enhanced_particles, obstacle.rect.center,
                                                        [(100, 200, 255), (150, 220, 255), (200, 240, 255)], 25)
                        emitter.emit(obstacle.rect.center, color=(200,255,255), count=18, size=10, speed=5, lifetime=24)
                        obstacle.kill()
                        if obstacle.blast_radius:
                            blown_up.append(obstacle)
                else:
                    energy -= sum(obstacle.damage for obstacle in hit)
                
                    # Play appropriate collision sound based on obstacle type
                    for obstacle in hit:
                        obstacle_name = getattr(obstacle, 'name', 'Unknown')
                        if 'Coral' in obstacle_name:
                            coral_collision_sound.play()
                            print(f"Playing coral collision sound for {obstacle_name}!")
                        elif 'Sub' in obstacle_name:
                            submarine_collision_sound.play()
                        elif 'Shipwreck' in obstacle_name:
                            shipwreck_collision_sound.play()
                            print(f"Playing shipwreck collision sound for {obstacle_name}!")
                        else:
                            generic_collision_sound.play()
                            print(f"Playing generic collision sound for {obstacle_name}!")
                    
                        print(f"Ouch! Shark hit an obstacle: {obstacle_name}. Energy: {energy:.1f}")
                        obstacle.kill()
                        if obstacle.blast_radius:
                            blown_up.append(obstacle)
                    
                        # Enhanced explosion effect
                        ParticleEffects.create_explosion(enhanced_particles, obstacle.rect.center,
                                                        [(255, 100, 0), (255, 200, 0), (255, 255, 100)], 30)
                    
                    emitter.emit(shark.rect.center, color=(255,255,0), count=16, size=12, speed=6, lifetime=22)
                    # Trigger damage flash effect
                    graphics_enhancer.trigger_damage_effect()
                    if energy <= 0:
                        fatal_collision_sound.play()  # Different sound for fatal collision
                        emitter.emit(shark.rect.center, color=(255,0,0), count=32, size=18, speed=8, lifetime=32)
                        game_over = True
                        restart_lock = RESTART_LOCK_MS
                        # Let fatal collision particles finish before pausing
                        particle_wait = True
                        particle_timer = 0
                        while particle_wait:
                            dt = clock.tick(60)
                            particle_timer += dt
                            screen.fill((0, 0, 64))
                            all_sprites.draw(screen)
                            shark_look.draw_shark(screen, shark, weapon.kind, dt)
                            particles.update()
                            particles.draw(screen)
                            pygame.display.flip()
                            # Wait until all particles are gone or 1.5 seconds have passed
                            if len(particles) == 0 or particle_timer > 1500:
                                particle_wait = False
                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    pygame.quit()
                                    sys.exit()
                        pygame.event.clear()  # Discard buffered events from the animation wait

            # Coastline can't be destroyed: it costs energy once, then pushes the shark toward
            # the channel, and the shark stays safe until it has been clear for a moment
            touching = pygame.sprite.spritecollide(shark, banks, False, pixels_touch)
            if touching:
                if bank_invuln <= 0:
                    if shield_active and shield_strength > 0:
                        shield_activate_sound.play()
                        shield_strength -= BANK_DAMAGE
                        if shield_strength <= 0:
                            shield_active = False
                            shield_strength = 0
                    else:
                        energy -= BANK_DAMAGE
                        coral_collision_sound.play()
                        graphics_enhancer.trigger_damage_effect()
                    emitter.emit(shark.rect.center, color=(180,180,200), count=14, size=8, speed=5, lifetime=20)
                bank_invuln = BANK_INVULN_MS
                to_channel = touching[0].channel_center - shark.rect.centerx
                shark.rect.centerx += max(-BANK_PUSH, min(BANK_PUSH, to_channel))
                shark.rect.x = max(0, min(shark.rect.x, 800 - shark.rect.width))
            elif bank_invuln > 0:
                bank_invuln -= dt

            # Shots stop dead against the coastline
            for shot in pygame.sprite.groupcollide(projectiles, banks, True, False, pixels_touch):
                emitter.emit(shot.rect.midtop, color=(200,200,210), count=6, size=4, speed=3, lifetime=12)

            # Lasers wear an obstacle down; missiles and torpedoes destroy it outright
            destroyed = []
            for shot in pygame.sprite.groupcollide(projectiles, obstacles, False, False, pixels_touch).keys():
                targets = pygame.sprite.spritecollide(shot, obstacles, False, pixels_touch)
                if isinstance(shot, Laser):
                    if shot.pierce:
                        targets = [obs for obs in targets if obs not in shot.already_hit]
                        shot.already_hit.update(targets)
                    for obs in targets:
                        obs.hits += shot.power
                        emitter.emit(shot.rect.midtop, color=obs.debris_color, count=4, size=4, speed=3, lifetime=10)
                        if obs.hits >= obs.toughness and obs not in destroyed:
                            destroyed.append(obs)
                else:
                    color = (255,128,0) if isinstance(shot, Missile) else (0,255,255)
                    for obs in targets:
                        emitter.emit(obs.rect.center, color=color, count=24, size=10, speed=5, lifetime=28)
                        if obs not in destroyed:
                            destroyed.append(obs)
                if not (isinstance(shot, Laser) and shot.pierce):
                    shot.kill()

            # Beams hit once, through a shield first
            for beam in pygame.sprite.spritecollide(shark, enemy_shots, False, pixels_touch):
                if beam.active:
                    beam.active = False
                    if shield_active and shield_strength > 0:
                        shield_activate_sound.play()
                        shield_strength -= beam.damage
                        if shield_strength <= 0:
                            shield_active = False
                            shield_strength = 0
                    else:
                        energy -= beam.damage
                        generic_collision_sound.play()
                        graphics_enhancer.trigger_damage_effect()

            # A charging tuna blows up on the coast too
            for sprite in obstacles.sprites():
                if sprite.bursts_on_coast and sprite.state == 'charge' and \
                        pygame.sprite.spritecollideany(sprite, banks, pixels_touch):
                    sprite.kill()
                    blown_up.append(sprite)

            # A mine's blast clears the obstacles around it, which can set off other mines.
            # One the shark touched has already cost it energy, so its blast spares the shark.
            queue = destroyed + blown_up
            while queue:
                obs = queue.pop(0)
                obs.kill()
                if obs.blast_radius:
                    center = pygame.math.Vector2(obs.rect.center)
                    ParticleEffects.create_explosion(enhanced_particles, obs.rect.center,
                                                    [(255, 120, 30), (255, 210, 80), (255, 255, 200)], 45)
                    for nearby in obstacles:
                        if nearby not in destroyed and center.distance_to(nearby.rect.center) <= obs.blast_radius:
                            destroyed.append(nearby)
                            queue.append(nearby)
                    if obs not in blown_up and center.distance_to(shark.rect.center) <= obs.blast_radius:
                        if shield_active and shield_strength > 0:
                            shield_strength -= obs.blast_damage
                            if shield_strength <= 0:
                                shield_active = False
                                shield_strength = 0
                        else:
                            energy -= obs.blast_damage
                            graphics_enhancer.trigger_damage_effect()
                if obs in blown_up:
                    continue
                emitter.emit(obs.rect.center, color=obs.debris_color, count=18, size=8, speed=4, lifetime=24)
                print(f"{obs.name} destroyed!")
                obstacle_destroy_sound.play()
                score += obs.reward
                if obs.drops_pickup:
                    px = max(40, min(760, obs.rect.centerx))
                    p = random.choice([LaserPowerup(px, obs.rect.centery), MissilePowerup(px, obs.rect.centery),
                                       TorpedoPowerup(px, obs.rect.centery),
                                       WeaponPowerup(px, obs.rect.centery, random.choice(list(WEAPONS)))])
                    powerups.add(p)
                    all_sprites.add(p)
                if obs.counts_for_rewards:
                    destroyed_counts[obs.name] = destroyed_counts.get(obs.name, 0) + 1
                    if destroyed_counts[obs.name] >= 4 and not shield_active:
                        px = channel.spawn_x(26)
                        shield_powerup = ShieldPowerup(px, -16)
                        powerups.add(shield_powerup)
                        all_sprites.add(shield_powerup)
                        destroyed_counts[obs.name] = 0
                    obstacles_destroyed += 1
                    if obstacles_destroyed >= 5:
                        weapon.earn()
                        obstacles_destroyed = 0
                        upgrade_activate_sound.play()

            # The boss: bites on contact, and any shot that lands hurts it
            if boss:
                boss.update(shark.rect)
                while boss.rubble_due:
                    boss.rubble_due -= 1
                    kind = OBSTACLE_TYPES[random.choice(['coral', 'coral', 'mine'])]
                    spawn_x = channel.spawn_x(kind.WIDTH, blocking=True, height=kind.HEIGHT)
                    if spawn_x is not None:
                        rubble = kind.create(spawn_x)
                        obstacles.add(rubble)
                        all_sprites.add(rubble)
                boss_invuln = max(0, boss_invuln - dt)
                if boss_invuln <= 0 and boss.touching(shark, pixels_touch):
                    boss_invuln = CONTACT_INVULN_MS
                    if shield_active and shield_strength > 0:
                        shield_activate_sound.play()
                        shield_strength -= boss.bite_damage
                        if shield_strength <= 0:
                            shield_active = False
                            shield_strength = 0
                    else:
                        energy -= boss.bite_damage
                        generic_collision_sound.play()
                        graphics_enhancer.trigger_damage_effect()
                    emitter.emit(shark.rect.center, color=(255,80,60), count=16, size=10, speed=6, lifetime=22)
                for shot, parts in pygame.sprite.groupcollide(projectiles, boss.parts, False, False, pixels_touch).items():
                    is_laser = isinstance(shot, Laser)
                    if is_laser and boss in shot.already_hit:
                        continue  # A piercing shot hurts the boss once, however much of it passes through
                    boss.shot_power = shot.power if is_laser else 1
                    boss.on_shot(parts, not is_laser)
                    if is_laser and shot.pierce:
                        shot.already_hit.add(boss)
                    else:
                        shot.kill()
                    emitter.emit(shot.rect.midtop, color=(255,220,120), count=6, size=5, speed=3, lifetime=12)
                if boss.dead:
                    for part in boss.parts:
                        ParticleEffects.create_explosion(enhanced_particles, part.rect.center,
                                                        [(255, 120, 30), (255, 210, 80), (180, 220, 100)], 12)
                    obstacle_destroy_sound.play()
                    upgrade_activate_sound.play()
                    print(f"{boss.name} defeated!")
                    score += VICTORY_SCORE
                    energy = 100
                    shark.laser_energy = 100
                    shark.missiles = 3
                    shark.torpedoes = 3
                    channel.leave_arena()
                    boss_phase = 'beaten'
                    next_boss += 1
                    banner = f"{boss.name} DEFEATED!  Fully repaired"
                    boss = None
                    banner_timer = 3500

            # A real hit, not the slow drain from swimming, costs a weapon level
            if energy_before_hits - energy > 1:
                weapon.lose_level()
                shark_look.hit()
            shield_now = shield_strength if shield_active else 0
            if shield_now < shield_before_hits:
                if shield_now > 0:
                    blow = hit[0].rect.center if hit else touching[0].rect.center if touching else None
                    shark_look.shield_hit(shark.rect.center, blow)
                else:
                    shark_look.shield_break(shark.rect.center)

            # Shark eats food: remove food and gain energy
            eaten = pygame.sprite.spritecollide(shark, foods, True)
            if eaten:
                energy = min(energy + 20 * len(eaten), 100)
                score += len(eaten)
                food_eat_sound.play()
                print(f"Yum! Shark ate {len(eaten)} fish. Energy: {energy:.1f}")

            # Shark collects powerups
            collected = pygame.sprite.spritecollide(shark, powerups, True)
            for p in collected:
                if isinstance(p, LaserPowerup):
                    shark.laser_energy = min(shark.laser_energy + 30, 100)
                    powerup_collect_sound.play()
                    print("Laser energy powerup collected!")
                elif isinstance(p, MissilePowerup):
                    shark.missiles = min(shark.missiles + 2, 3)
                    powerup_collect_sound.play()
                    print("Missile powerup collected!")
                elif isinstance(p, TorpedoPowerup):
                    shark.torpedoes = min(shark.torpedoes + 1, 3)
                    powerup_collect_sound.play()
                    print("Torpedo powerup collected!")
                elif isinstance(p, ShieldPowerup):
                    shield_active = True
                    shield_strength = 100  # Full strength shield
                    shield_timer = 0
                    shield_activate_sound.play()  # Special sound for shield
                    print("Shield activated at full strength!")
                elif isinstance(p, WeaponPowerup):
                    weapon.collect(p.kind)
                    upgrade_activate_sound.play()
                    banner = f"{weapon.label}!"
                    banner_timer = 1200
                score += 2

            # Out of energy from swimming: checked after
            # eating so a fish caught on the last drop still saves the shark
            if energy <= 0 and not game_over:
                fatal_collision_sound.play()
                game_over = True
                restart_lock = RESTART_LOCK_MS

            if game_over:
                break

        # Draw enhanced background using graphics enhancer
        graphics_enhancer.render_background()
        
        # Add bubble sources from moving objects
        bubble_sources = []
        bubble_sources.append(shark.rect.center)
        for torpedo in [p for p in projectiles if isinstance(p, Torpedo)]:
            bubble_sources.append(torpedo.rect.center)
        graphics_enhancer.add_bubble_sources(bubble_sources)
        
        all_sprites.draw(screen)
        shark_look.draw_shark(screen, shark, weapon.kind, frame_ms)
        shark_look.draw_shield(screen, shark.rect.center, shield_strength if shield_active else 0,
                               pygame.time.get_ticks(), frame_ms)
        for sprite in obstacles:
            if isinstance(sprite, Enemy):
                sprite.draw_warning(screen)
        particles.draw(screen)
        enhanced_particles.draw(screen)
        # Blink a ring around the shark while it can't be hurt by the coastline
        if bank_invuln > 0 and int(bank_invuln / 100) % 2:
            pygame.draw.circle(screen, (255, 255, 255), shark.rect.center, 62, 2)
        if boss:
            boss.draw(screen)
        hud.draw(screen, shark.rect, energy, shield_strength if shield_active else 0, shark.laser_energy,
                 weapon.label, shark.missiles, shark.torpedoes, score, pygame.time.get_ticks())
        if boss:
            hud.draw_boss_bar(screen, boss.name, boss.health / boss.max_health)
        if banner and banner_timer > 0:
            hud.draw_banner(screen, banner, (255, 225, 90))

        # Apply post-processing effects
        graphics_enhancer.render_effects()
        
        pygame.display.flip()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
