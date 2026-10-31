"""
Main entry point for Shark Laser Arcade Game.
Handles game loop and state management.
"""

import pygame
import sys
import random
import os
from player import Shark
from obstacle import CoralReef, Shipwreck
from food import SmallFish
from projectile import Laser, Missile, Torpedo
from powerup import LaserPowerup, MissilePowerup, TorpedoPowerup, FriendlySubmarine, ShieldPowerup
from particle import ParticleEmitter


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
    
    print("All sound effects loaded successfully!")
    # Track destroyed obstacles for shield spawn
    destroyed_counts = {}
    pygame.init()

    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Lazer Shark Kill! Kill!")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 32)
    title_font = pygame.font.SysFont(None, 72)

    # --- Settings Menu ---
    # Default controls
    keymap = {
        'left': pygame.K_LEFT,
        'right': pygame.K_RIGHT,
        'up': pygame.K_UP,
        'down': pygame.K_DOWN,
        'fire': pygame.K_SPACE,
        'missile': pygame.K_LALT,  # Default: Left Alt
        'torpedo': pygame.K_LCTRL, # Default: Left Ctrl
        'pause': pygame.K_p,
        'quit': pygame.K_ESCAPE
    }
    controller_enabled = False
    easy_mode = False
    
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
        'Continue'
    ]
    selected = 0
    in_settings = True
    while in_settings:
        screen.fill((0, 0, 64))
        title = title_font.render("Settings", True, (255, 255, 0))
        screen.blit(title, (250, 80))
        for i, item in enumerate(menu_items):
            color = (255, 255, 255) if i != selected else (0, 255, 0)
            if item == 'Toggle Controller':
                label = f"{item}: {'ON' if controller_enabled else 'OFF'}"
            elif item == 'Toggle Easy Mode':
                label = f"{item}: {'ON' if easy_mode else 'OFF'}"
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
                    elif menu_items[selected] == 'Continue':
                        in_settings = False

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

    shark = Shark(400, 580)  # Start at bottom center
    all_sprites = pygame.sprite.Group(shark)
    obstacles = pygame.sprite.Group()
    foods = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    subs = pygame.sprite.Group()
    particles = pygame.sprite.Group()
    emitter = ParticleEmitter(particles)
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

    # Shield powerup state
    shield_active = False
    shield_timer = 0
    next_shield_spawn = random.randint(180000, 300000)  # 3-5 min in ms
    
    # Start ambient ocean sound loop on a dedicated channel
    ambient_channel = pygame.mixer.Channel(7)  # Use last channel for ambient
    ambient_channel.play(ambient_ocean_sound, loops=-1)  # Loop indefinitely
    
    while running:
        dt = clock.tick(60)

    # Shield powerup now spawns after two identical obstacles are destroyed
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
                        shark = Shark(400, 580)
                        all_sprites = pygame.sprite.Group(shark)
                        obstacles.empty()
                        foods.empty()
                        energy = 100
                        spawn_timer = 0
                        game_over = False
        if game_over:
            screen.fill((0, 0, 64))
            game_over_text = font.render("Game Over! Press any key to play again or ESC to exit.", True, (255, 0, 0))
            screen.blit(game_over_text, (80, 280))
            energy_text = font.render(f"Final Energy: {int(energy)}", True, (255, 255, 255))
            screen.blit(energy_text, (300, 320))
            pygame.display.flip()
            continue

        if paused:
            screen.fill((0, 0, 64))
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
                'left': keys[keymap['left']] or x_axis < -0.2,
                'right': keys[keymap['right']] or x_axis > 0.2,
                'up': keys[keymap['up']] or y_axis < -0.2,
                'down': keys[keymap['down']] or y_axis > 0.2
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
        shark.update_with_input(move, dt)
        # Update other sprites
        for sprite in all_sprites:
            if sprite != shark:
                sprite.update()
        obstacles.update()
        foods.update()
        projectiles.update()
        powerups.update()
        subs.update()
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

        # Energy drains while swimming (remapped)
        if move['left'] or move['right'] or move['up'] or move['down']:
            energy -= 0.08  # Drain rate per frame
        else:
            energy -= 0.02  # Idle drain
        energy = max(0, min(energy, 100))

        # Spawn obstacles and food every 1.5 seconds
        spawn_timer += dt
        if spawn_timer > 1500:
            spawn_timer = 0
            spawn_x = random.randint(40, 760)
            choice = random.choice(['coral', 'shipwreck', 'fish'])
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
            sprite.rect.y += 2
            if sprite.rect.top > 600:
                sprite.kill()

        # Collision detection
        # Shark hits obstacle: lose a third of energy per hit
        hit = pygame.sprite.spritecollide(shark, obstacles, False)
        if hit:
            if shield_active:
                shield_activate_sound.play()  # Play shield sound when it blocks damage
                print("Shield protected the shark from damage and destroyed the obstacle!")
                for obstacle in hit:
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
                    
                emitter.emit(shark.rect.center, color=(255,255,0), count=16, size=12, speed=6, lifetime=22)
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
                    # Now show restart message
                    screen.fill((0, 0, 64))
                    all_sprites.draw(screen)
                    particles.draw(screen)
                    msg = font.render('Hit Any Key to Play Again.', True, (255, 255, 255))
                    screen.blit(msg, (180, 280))
                    pygame.display.flip()
                    waiting = True
                    while waiting:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            if event.type == pygame.KEYDOWN:
                                waiting = False

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
                        # Count destroyed obstacles for shield spawn
                        obs_type = getattr(obs, 'name', type(obs).__name__)
                        destroyed_counts[obs_type] = destroyed_counts.get(obs_type, 0) + 1
                        if destroyed_counts[obs_type] == 2 and not shield_active:
                            px = random.randint(40, 760)
                            shield_powerup = ShieldPowerup(px, -16)
                            powerups.add(shield_powerup)
                            all_sprites.add(shield_powerup)
                            destroyed_counts[obs_type] = 0
                        obstacle_destroy_sound.play()
                        obs.kill()

        # Missile hits any obstacle: destroy obstacle with one hit
        for missile in [s for s in projectiles if isinstance(s, Missile)]:
            obs_hit = pygame.sprite.spritecollide(missile, obstacles, False)
            for obs in obs_hit:
                emitter.emit(obs.rect.center, color=(255,128,0), count=22, size=10, speed=5, lifetime=28)
                print(f"{getattr(obs, 'name', 'Obstacle')} destroyed by missile!")
                # Count destroyed obstacles for shield spawn
                obs_type = getattr(obs, 'name', type(obs).__name__)
                destroyed_counts[obs_type] = destroyed_counts.get(obs_type, 0) + 1
                if destroyed_counts[obs_type] == 2 and not shield_active:
                    px = random.randint(40, 760)
                    shield_powerup = ShieldPowerup(px, -16)
                    powerups.add(shield_powerup)
                    all_sprites.add(shield_powerup)
                    destroyed_counts[obs_type] = 0
                obstacle_destroy_sound.play()
                obs.kill()
                missile.kill()

        # Torpedo hits any obstacle: destroy obstacle with one hit
        for torpedo in [s for s in projectiles if isinstance(s, Torpedo)]:
            obs_hit = pygame.sprite.spritecollide(torpedo, obstacles, False)
            for obs in obs_hit:
                emitter.emit(obs.rect.center, color=(0,255,255), count=26, size=12, speed=6, lifetime=32)
                print(f"{getattr(obs, 'name', 'Obstacle')} destroyed by torpedo!")
                # Count destroyed obstacles for shield spawn
                obs_type = getattr(obs, 'name', type(obs).__name__)
                destroyed_counts[obs_type] = destroyed_counts.get(obs_type, 0) + 1
                if destroyed_counts[obs_type] == 2 and not shield_active:
                    px = random.randint(40, 760)
                    shield_powerup = ShieldPowerup(px, -16)
                    powerups.add(shield_powerup)
                    all_sprites.add(shield_powerup)
                    destroyed_counts[obs_type] = 0
                obstacle_destroy_sound.play()
                obs.kill()
                torpedo.kill()

        # Shark eats food: remove food and gain energy
        eaten = pygame.sprite.spritecollide(shark, foods, True)
        if eaten:
            energy = min(energy + 15 * len(eaten), 100)
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
                shark.missiles += 2
                powerup_collect_sound.play()
                print("Missile powerup collected!")
            elif isinstance(p, TorpedoPowerup):
                shark.torpedoes += 1
                powerup_collect_sound.play()
                print("Torpedo powerup collected!")
            elif isinstance(p, ShieldPowerup):
                shield_active = True
                shield_timer = 0
                shield_activate_sound.play()  # Special sound for shield
                print("Shield activated!")

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

        # Enhanced underwater background with gradient and effects
        # Create ocean gradient background
        for y in range(0, 600, 2):
            # Gradient from darker (top/deeper) to lighter (bottom/shallower)
            depth_factor = y / 600.0
            blue_value = int(40 + depth_factor * 40)  # 40 to 80
            green_value = int(10 + depth_factor * 20)  # 10 to 30
            color = (0, green_value, blue_value)
            pygame.draw.rect(screen, color, (0, y, 800, 2))
        
        # Add animated water caustics effect (light patterns)
        import math
        caustic_timer = pygame.time.get_ticks() / 100.0
        for i in range(8):
            for j in range(6):
                x = i * 100 + int(20 * math.sin(caustic_timer + i))
                y = j * 100 + int(20 * math.cos(caustic_timer + j))
                size = int(40 + 10 * math.sin(caustic_timer * 0.5 + i + j))
                alpha = int(20 + 10 * math.sin(caustic_timer * 0.3))
                
                # Draw light caustic circles
                caustic_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(caustic_surf, (100, 150, 200, alpha), (size, size), size)
                screen.blit(caustic_surf, (x, y), special_flags=pygame.BLEND_ADD)
        
        # Add floating particles/bubbles for depth
        bubble_timer = pygame.time.get_ticks() / 50.0
        for i in range(15):
            bubble_x = int(50 + i * 50 + 10 * math.sin(bubble_timer * 0.5 + i * 2))
            bubble_y = int((bubble_timer * 20 + i * 40) % 650 - 50)
            bubble_size = 2 + (i % 3)
            bubble_alpha = 40 + (i % 3) * 20
            
            bubble_surf = pygame.Surface((bubble_size * 2, bubble_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(bubble_surf, (150, 200, 255, bubble_alpha), 
                             (bubble_size, bubble_size), bubble_size)
            screen.blit(bubble_surf, (bubble_x, bubble_y))
        
        # Draw kelp/seaweed in background
        kelp_sway = int(5 * math.sin(pygame.time.get_ticks() / 500.0))
        for i in range(0, 800, 120):
            kelp_base_x = i + 20
            kelp_top_x = kelp_base_x + kelp_sway
            
            # Draw multiple kelp strands
            for j in range(3):
                offset = j * 8
                kelp_color = (0, 40 + j * 10, 20 + j * 5)
                points = [
                    (kelp_base_x + offset, 600),
                    (kelp_base_x + offset - 5, 500),
                    (kelp_top_x + offset + 3, 400),
                    (kelp_top_x + offset, 300)
                ]
                pygame.draw.lines(screen, kelp_color, False, points, 3 - j)
        
        all_sprites.draw(screen)
        particles.draw(screen)
        # Draw energy bar
        pygame.draw.rect(screen, (0, 200, 0), (20, 20, int(energy * 3), 20))
        pygame.draw.rect(screen, (255, 255, 255), (20, 20, 300, 20), 2)
        energy_text = font.render(f"Energy", True, (255, 255, 255))
        screen.blit(energy_text, (330, 16))
        # Draw shield status
        if shield_active:
            shield_text = font.render("Shield: ACTIVE", True, (0, 255, 128))
            screen.blit(shield_text, (20, 80))
            # Draw white arc directly in front of the shark's mouth
            arc_width = 80
            arc_height = 60
            arc_x = shark.rect.centerx - arc_width // 2
            arc_y = shark.rect.centery - arc_height // 2 - 30  # Move arc up to align with mouth
            arc_rect = pygame.Rect(arc_x, arc_y, arc_width, arc_height)
            pygame.draw.arc(screen, (255,255,255), arc_rect, 0.57, 2.57, 6)
        # Draw laser power bar
        pygame.draw.rect(screen, (255, 0, 0), (20, 48, int(shark.laser_energy * 3), 14))
        pygame.draw.rect(screen, (255, 255, 255), (20, 48, 300, 14), 1)
        laser_text = font.render("Laser", True, (255, 0, 0))
        screen.blit(laser_text, (330, 44))
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
        pygame.display.flip()
        pygame.draw.rect(screen, (255, 0, 0), (20, 48, int(shark.laser_energy * 3), 14))
        pygame.draw.rect(screen, (255, 255, 255), (20, 48, 300, 14), 1)
        laser_text = font.render("Laser", True, (255, 0, 0))
        screen.blit(laser_text, (330, 44))
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
        pygame.display.flip()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
