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
from obstacle import CoralReef, Shipwreck, create_reef_wall
from food import SmallFish
from projectile import Laser, Missile, Torpedo
from powerup import LaserPowerup, MissilePowerup, TorpedoPowerup, FriendlySubmarine, ShieldPowerup
from particle import ParticleEmitter
from graphics_enhancements import (
    GraphicsEnhancer, ParticleEffects, AnimatedSprite, 
    ScreenEffects, EnhancedParticle
)
from settings_manager import SettingsManager


def load_sound(filename):
    """Load a sound file from the sounds directory"""
    try:
        sound_path = os.path.join('sounds', filename)
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
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    pygame.mixer.set_num_channels(8)  # Ensure enough channels for all sounds
    
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
    background_music_path = os.path.join('sounds', 'shark.wav')
    
    print("All sound effects loaded successfully!")
    # Track destroyed obstacles for shield spawn
    destroyed_counts = {}

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
    menu_items = [
        'Remap Keys',
        'Toggle Controller',
        'Toggle Easy Mode',
        'Toggle Music',
        'Music Volume',
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
            screen.blit(instructions, (120, 500))
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
                            if music_enabled:
                                pygame.mixer.music.unpause()
                            else:
                                pygame.mixer.music.pause()
                        elif menu_items[selected] == 'Music Volume':
                            adjusting_volume = True
                        elif menu_items[selected] == 'Continue':
                            # Save settings before continuing
                            settings_manager.update(
                                keymap=keymap,
                                controller_enabled=controller_enabled,
                                easy_mode=easy_mode,
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
                        pygame.mixer.music.set_volume(music_volume)
                        menu_beep_sound.play()
                    elif event.key == pygame.K_RIGHT:
                        music_volume = min(1.0, music_volume + 0.1)
                        pygame.mixer.music.set_volume(music_volume)
                        menu_beep_sound.play()
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        adjusting_volume = False
                        powerup_collect_sound.play()

    # Splash screen
    splash = True
    while splash:
        screen.fill((0, 0, 64))
        title_text = title_font.render("Lazer Shark Kill! Kill!", True, (255, 0, 0))
        prompt_text = font.render("Press any key to start", True, (255, 255, 255))
        screen.blit(title_text, (60, 200))
        screen.blit(prompt_text, (250, 320))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                splash = False

    # Clear event queue and add a short delay to ensure splash screen is removed
    pygame.event.clear()
    pygame.time.wait(100)

    # Use enhanced shark with sprites if available, fallback to procedural
    try:
        shark = SharkWithSprites(400, 580)  # Enhanced sprite-based shark
        print("Using enhanced shark sprites from hai_0.png")
    except Exception as e:
        print(f"Could not load enhanced sprites, using procedural shark: {e}")
        shark = Shark(400, 580)  # Fallback to procedural shark
    all_sprites = pygame.sprite.Group(shark)
    obstacles = pygame.sprite.Group()
    foods = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    subs = pygame.sprite.Group()
    particles = pygame.sprite.Group()
    emitter = ParticleEmitter(particles)
    
    # Track time for animations
    # Weapon upgrade system
    obstacles_spawned = 0
    obstacles_destroyed = 0
    upgrade_active = False
    upgrade_timer = 0
    running = True
    game_over = False
    paused = False
    energy = 100
    spawn_timer = 0
    powerup_timer = 0
    sub_timer = 0
    reef_wall_timer = 0
    score = 0

    # Shield powerup state - Enhanced system
    shield_active = False
    shield_strength = 0  # 0-100, starts at 100 when activated
    shield_timer = 0
    next_shield_spawn = random.randint(180000, 300000)  # 3-5 min in ms
    
    # Start background music
    if os.path.exists(background_music_path):
        pygame.mixer.music.load(background_music_path)
        pygame.mixer.music.set_volume(music_volume)
        if music_enabled:
            pygame.mixer.music.play(-1)  # Loop indefinitely
        print("Background music loaded and playing!")
    else:
        print(f"Warning: Background music file not found: {background_music_path}")
        music_enabled = False
    
    # Start ambient ocean sound loop on a dedicated channel
    ambient_channel = pygame.mixer.Channel(7)  # Use last channel for ambient
    ambient_channel.set_volume(sfx_volume * 0.3)  # Ambient at 30% of SFX volume
    ambient_channel.play(ambient_ocean_sound, loops=-1)  # Loop indefinitely
    
    while running:
        dt = clock.tick(60)

        # Update graphics enhancer
        graphics_enhancer.update(dt)
        enhanced_particles.update()

        if upgrade_active:
            upgrade_timer -= dt
            if upgrade_timer <= 0:
                upgrade_active = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_p:
                    paused = not paused
            # Controller pause button (Start button - typically button 7 or 9)
            if event.type == pygame.JOYBUTTONDOWN and controller_enabled and controller:
                if event.button == 7 or event.button == 9:  # Start button on most controllers
                    paused = not paused
            if game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        # Restart game
                        try:
                            shark = SharkWithSprites(400, 580)
                        except Exception:
                            shark = Shark(400, 580)
                        all_sprites = pygame.sprite.Group(shark)
                        obstacles.empty()
                        foods.empty()
                        projectiles.empty()
                        powerups.empty()
                        subs.empty()
                        particles.empty()
                        enhanced_particles.empty()
                        energy = 100
                        spawn_timer = 0
                        powerup_timer = 0
                        sub_timer = 0
                        shield_active = False
                        shield_strength = 0
                        upgrade_active = False
                        upgrade_timer = 0
                        obstacles_destroyed = 0
                        destroyed_counts = {}
                        score = 0
                        reef_wall_timer = 0
                        game_over = False
                # Controller support for game restart
                elif event.type == pygame.JOYBUTTONDOWN and controller_enabled and controller:
                    if event.button == 7 or event.button == 9:  # Start button - exit game
                        running = False
                    else:  # Any other button - restart game
                        try:
                            shark = SharkWithSprites(400, 580)
                        except Exception:
                            shark = Shark(400, 580)
                        all_sprites = pygame.sprite.Group(shark)
                        obstacles.empty()
                        foods.empty()
                        projectiles.empty()
                        powerups.empty()
                        subs.empty()
                        particles.empty()
                        enhanced_particles.empty()
                        energy = 100
                        spawn_timer = 0
                        powerup_timer = 0
                        sub_timer = 0
                        shield_active = False
                        shield_strength = 0
                        upgrade_active = False
                        upgrade_timer = 0
                        obstacles_destroyed = 0
                        destroyed_counts = {}
                        score = 0
                        reef_wall_timer = 0
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
            energy_text = font.render(f"Final Energy: {int(energy)}", True, (255, 255, 255))
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
                pause_text = font.render("Paused - Press 'P' to resume", True, (255, 255, 0))
                screen.blit(pause_text, (220, 280))
            pygame.display.flip()
            continue

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
        subs.update()
        for sub in subs:
            for supply in sub.pending_drops:
                powerups.add(supply)
                all_sprites.add(supply)
            sub.pending_drops.clear()
        particles.update()

        # Firing controls (remapped + controller support)
        if keys[keymap['fire']] or controller_fire:
            # Easy mode: unlimited laser energy
            if easy_mode:
                shark.laser_energy = 100
            if shark.fire_laser():
                if upgrade_active:
                    for offset in [-12, 0, 12]:
                        laser = Laser(shark.rect.centerx + offset, shark.rect.top)
                        projectiles.add(laser)
                        all_sprites.add(laser)
                    laser_triple_sound.play()  # Different sound for triple laser
                else:
                    laser = Laser(shark.rect.centerx, shark.rect.top)
                    projectiles.add(laser)
                    all_sprites.add(laser)
                    laser_sound.play()
                    # Add laser trail effect
                    ParticleEffects.create_trail(enhanced_particles, 
                                                (shark.rect.centerx, shark.rect.top),
                                                (0, -1), (255, 100, 100))
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
                for obs in obstacles:
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

        # Spawn obstacles and food every 1.5 seconds
        spawn_timer += dt
        if spawn_timer > 1500:
            spawn_timer = 0
            spawn_x = random.randint(40, 760)
            choice = random.choice(['coral', 'shipwreck', 'fish', 'fish'])  # 50% fish, 50% obstacles
            if choice == 'coral':
                coral = CoralReef(spawn_x, -24)
                obstacles.add(coral)
                all_sprites.add(coral)
            elif choice == 'shipwreck':
                wreck = Shipwreck(spawn_x, -28)
                obstacles.add(wreck)
                all_sprites.add(wreck)
            else:
                fish = SmallFish(spawn_x, -10)
                foods.add(fish)
                all_sprites.add(fish)

        # Spawn powerups every 4 seconds
        powerup_timer += dt
        if powerup_timer > 4000:
            powerup_timer = 0
            px = random.randint(40, 760)
            ptype = random.choice(['laser', 'missile', 'torpedo'])
            if ptype == 'laser':
                p = LaserPowerup(px, -16)
            elif ptype == 'missile':
                p = MissilePowerup(px, -16)
            else:
                p = TorpedoPowerup(px, -16)
            powerups.add(p)
            all_sprites.add(p)

        # Spawn friendly submarine every 12 seconds
        sub_timer += dt
        if sub_timer > 12000:
            sub_timer = 0
            sx = random.randint(60, 740)
            sub = FriendlySubmarine(sx, -18)
            subs.add(sub)
            all_sprites.add(sub)

        # Spawn reef wall every 5 seconds; coverage grows at half the rate of score
        reef_wall_timer += dt
        if reef_wall_timer > 5000:
            reef_wall_timer = 0
            reef_coverage = min(0.30 + score * 0.005, 0.70)
            for seg in create_reef_wall(reef_coverage):
                obstacles.add(seg)
                all_sprites.add(seg)

        # Scroll obstacles, food, powerups, and subs downward
        for sprite in obstacles:
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
        for sprite in subs:
            if sprite.rect.top > 600:
                sprite.kill()

        # Collision detection
        # Shark hits obstacle: lose a third of energy per hit
        hit = pygame.sprite.spritecollide(shark, obstacles, False)
        if hit:
            if shield_active and shield_strength > 0:
                shield_activate_sound.play()  # Play shield sound when it blocks damage
                shield_strength -= 33  # Reduce shield by 1/3 per collision
                print(f"Shield protected the shark! Shield strength: {shield_strength:.1f}")
                
                # Check if shield is depleted
                if shield_strength <= 0:
                    shield_active = False
                    shield_strength = 0
                    print("Shield depleted! Spawning replacement powerups...")
                    # Spawn 2-3 shield powerups when shield breaks
                    for i in range(random.randint(2, 3)):
                        px = random.randint(40, 760)
                        shield_powerup = ShieldPowerup(px, -16 - i * 30)  # Stagger spawn positions
                        powerups.add(shield_powerup)
                        all_sprites.add(shield_powerup)
                
                for obstacle in hit:
                    # Enhanced explosion effect for shield-blocked obstacles
                    ParticleEffects.create_explosion(enhanced_particles, obstacle.rect.center,
                                                    [(100, 200, 255), (150, 220, 255), (200, 240, 255)], 25)
                    emitter.emit(obstacle.rect.center, color=(200,255,255), count=18, size=10, speed=5, lifetime=24)
                    obstacle.kill()
            else:
                energy -= 33
                
                # Play appropriate collision sound based on obstacle type
                for obstacle in hit:
                    obstacle_name = getattr(obstacle, 'name', 'Unknown')
                    if 'Coral' in obstacle_name:
                        coral_collision_sound.play()
                        print(f"Playing coral collision sound for {obstacle_name}!")
                    elif 'Shipwreck' in obstacle_name:
                        shipwreck_collision_sound.play()
                        print(f"Playing shipwreck collision sound for {obstacle_name}!")
                    else:
                        generic_collision_sound.play()
                        print(f"Playing generic collision sound for {obstacle_name}!")
                    
                    print(f"Ouch! Shark hit an obstacle: {obstacle_name}. Energy: {energy:.1f}")
                    obstacle.kill()
                    
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
                    # Let fatal collision particles finish before pausing
                    particle_wait = True
                    particle_timer = 0
                    while particle_wait:
                        dt = clock.tick(60)
                        particle_timer += dt
                        screen.fill((0, 0, 64))
                        all_sprites.draw(screen)
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

        # Laser hits coral reefs and shipwrecks: increment hit counter, break after 3 hits
        for laser in [s for s in projectiles if isinstance(s, Laser)]:
            obs_hit = pygame.sprite.spritecollide(laser, obstacles, False)
            for obs in obs_hit:
                if hasattr(obs, 'hits'):
                    obs.hits += 1
                    laser.kill()
                    if obs.hits >= 3:
                        emitter.emit(obs.rect.center, color=(255,200,0), count=18, size=8, speed=4, lifetime=24)
                        print(f"{getattr(obs, 'name', 'Obstacle')} destroyed by lasers!")
                        obs_type = getattr(obs, 'name', type(obs).__name__)
                        destroyed_counts[obs_type] = destroyed_counts.get(obs_type, 0) + 1
                        if destroyed_counts[obs_type] == 4 and not shield_active:
                            px = random.randint(40, 760)
                            shield_powerup = ShieldPowerup(px, -16)
                            powerups.add(shield_powerup)
                            all_sprites.add(shield_powerup)
                            destroyed_counts[obs_type] = 0
                        obstacles_destroyed += 1
                        if obstacles_destroyed >= 5 and not upgrade_active:
                            upgrade_active = True
                            upgrade_timer = 10000
                            obstacles_destroyed = 0
                            upgrade_activate_sound.play()
                        obstacle_destroy_sound.play()
                        obs.kill()
                        score += 3

        # Missile hits any obstacle: destroy obstacle with one hit
        for missile in [s for s in projectiles if isinstance(s, Missile)]:
            obs_hit = pygame.sprite.spritecollide(missile, obstacles, False)
            for obs in obs_hit:
                emitter.emit(obs.rect.center, color=(255,128,0), count=22, size=10, speed=5, lifetime=28)
                print(f"{getattr(obs, 'name', 'Obstacle')} destroyed by missile!")
                obs_type = getattr(obs, 'name', type(obs).__name__)
                destroyed_counts[obs_type] = destroyed_counts.get(obs_type, 0) + 1
                if destroyed_counts[obs_type] == 4 and not shield_active:
                    px = random.randint(40, 760)
                    shield_powerup = ShieldPowerup(px, -16)
                    powerups.add(shield_powerup)
                    all_sprites.add(shield_powerup)
                    destroyed_counts[obs_type] = 0
                obstacles_destroyed += 1
                if obstacles_destroyed >= 5 and not upgrade_active:
                    upgrade_active = True
                    upgrade_timer = 10000
                    obstacles_destroyed = 0
                    upgrade_activate_sound.play()
                obstacle_destroy_sound.play()
                obs.kill()
                missile.kill()
                score += 3

        # Torpedo hits any obstacle: destroy obstacle with one hit
        for torpedo in [s for s in projectiles if isinstance(s, Torpedo)]:
            obs_hit = pygame.sprite.spritecollide(torpedo, obstacles, False)
            for obs in obs_hit:
                emitter.emit(obs.rect.center, color=(0,255,255), count=26, size=12, speed=6, lifetime=32)
                print(f"{getattr(obs, 'name', 'Obstacle')} destroyed by torpedo!")
                obs_type = getattr(obs, 'name', type(obs).__name__)
                destroyed_counts[obs_type] = destroyed_counts.get(obs_type, 0) + 1
                if destroyed_counts[obs_type] == 4 and not shield_active:
                    px = random.randint(40, 760)
                    shield_powerup = ShieldPowerup(px, -16)
                    powerups.add(shield_powerup)
                    all_sprites.add(shield_powerup)
                    destroyed_counts[obs_type] = 0
                obstacles_destroyed += 1
                if obstacles_destroyed >= 5 and not upgrade_active:
                    upgrade_active = True
                    upgrade_timer = 10000
                    obstacles_destroyed = 0
                    upgrade_activate_sound.play()
                obstacle_destroy_sound.play()
                obs.kill()
                torpedo.kill()
                score += 3

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
            score += 2

        # Shark collides with friendly submarine: lose energy
        sub_hit = pygame.sprite.spritecollide(shark, subs, False)
        if sub_hit:
            energy -= 20
            submarine_collision_sound.play()  # Add submarine collision sound
            print("Ouch! Collided with friendly submarine.")
            for s in sub_hit:
                s.kill()
            if energy <= 0:
                fatal_collision_sound.play()  # Fatal collision sound for submarine too
                game_over = True

        # Draw enhanced background using graphics enhancer
        graphics_enhancer.render_background()
        
        # Add bubble sources from moving objects
        bubble_sources = []
        bubble_sources.append(shark.rect.center)
        for torpedo in [p for p in projectiles if isinstance(p, Torpedo)]:
            bubble_sources.append(torpedo.rect.center)
        graphics_enhancer.add_bubble_sources(bubble_sources)
        
        all_sprites.draw(screen)
        particles.draw(screen)
        enhanced_particles.draw(screen)
        # Draw energy bar
        pygame.draw.rect(screen, (0, 200, 0), (20, 20, int(energy * 3), 20))
        pygame.draw.rect(screen, (255, 255, 255), (20, 20, 300, 20), 2)
        energy_text = font.render(f"Energy", True, (255, 255, 255))
        screen.blit(energy_text, (330, 16))
        # Draw shield status and strength bar
        shield_bar_y = 80
        if shield_active and shield_strength > 0:
            # Active shield with strength bar
            shield_text = font.render("Shield", True, (0, 255, 128))
            screen.blit(shield_text, (20, shield_bar_y))
            
            # Shield strength bar (similar to energy bar)
            shield_width = int(shield_strength * 2)  # 200px max width
            shield_color = (0, 255, 128) if shield_strength > 66 else (255, 255, 0) if shield_strength > 33 else (255, 128, 0)
            pygame.draw.rect(screen, shield_color, (20, shield_bar_y + 25, shield_width, 15))
            pygame.draw.rect(screen, (255, 255, 255), (20, shield_bar_y + 25, 200, 15), 2)  # Border
            
            # Shield strength text
            strength_text = font.render(f"{int(shield_strength)}", True, (255, 255, 255))
            screen.blit(strength_text, (230, shield_bar_y + 21))
            
            # Draw white arc directly in front of the shark's mouth
            arc_width = 80
            arc_height = 60
            arc_x = shark.rect.centerx - arc_width // 2
            arc_y = shark.rect.centery - arc_height // 2 - 30  # Move arc up to align with mouth
            arc_rect = pygame.Rect(arc_x, arc_y, arc_width, arc_height)
            pygame.draw.arc(screen, (255,255,255), arc_rect, 0.57, 2.57, 6)
        else:
            # Inactive/no shield - greyed out bar
            shield_text = font.render("Shield", True, (100, 100, 100))
            screen.blit(shield_text, (20, shield_bar_y))
            
            # Greyed out empty bar
            pygame.draw.rect(screen, (50, 50, 50), (20, shield_bar_y + 25, 200, 15))
            pygame.draw.rect(screen, (100, 100, 100), (20, shield_bar_y + 25, 200, 15), 2)  # Border
            
            # "INACTIVE" text
            inactive_text = font.render("INACTIVE", True, (100, 100, 100))
            screen.blit(inactive_text, (230, shield_bar_y + 21))
        # Draw laser power bar (moved down to accommodate shield bar)
        laser_bar_y = 125
        pygame.draw.rect(screen, (255, 0, 0), (20, laser_bar_y, int(shark.laser_energy * 3), 14))
        pygame.draw.rect(screen, (255, 255, 255), (20, laser_bar_y, 300, 14), 1)
        laser_text = font.render("Laser", True, (255, 0, 0))
        screen.blit(laser_text, (330, laser_bar_y - 4))
        # Draw missile inventory (max 3)
        for i in range(3):
            color = (255, 128, 0) if i < min(shark.missiles, 3) else (80, 40, 0)
            pygame.draw.rect(screen, color, (420 + i*28, 20, 18, 18))
            pygame.draw.rect(screen, (255, 255, 255), (420 + i*28, 20, 18, 18), 2)
        missile_text = font.render("Missiles", True, (255, 128, 0))
        screen.blit(missile_text, (420, 44))
        # Draw torpedo inventory (max 3)
        for i in range(3):
            color = (0, 255, 255) if i < min(shark.torpedoes, 3) else (0, 64, 64)
            pygame.draw.ellipse(screen, color, (540 + i*28, 20, 18, 18))
            pygame.draw.ellipse(screen, (255, 255, 255), (540 + i*28, 20, 18, 18), 2)
        torpedo_text = font.render("Torpedoes", True, (0, 255, 255))
        screen.blit(torpedo_text, (540, 44))
        score_text = font.render(f"Score: {score}", True, (255, 255, 0))
        screen.blit(score_text, (660, 20))

        # Apply post-processing effects
        graphics_enhancer.render_effects()
        
        pygame.display.flip()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
