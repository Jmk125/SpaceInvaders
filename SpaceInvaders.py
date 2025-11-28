import pygame
import sys
import random
import math
import time
import json
import os

# Initialize Pygame
pygame.init()
pygame.joystick.init()

# Constants - 16:9 Fullscreen
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
DARK_GREEN = (0, 128, 0)
GRAY = (128, 128, 128)
GOLD = (255, 215, 0)

# Game settings
BASE_PLAYER_SPEED = 8
BASE_BULLET_SPEED = 10
BASE_ENEMY_SPEED = 0.2
BASE_SHOOT_COOLDOWN = 300
ENEMY_DROP_SPEED = 30
RAPID_FIRE_COOLDOWN = 100
AFTERIMAGE_INTERVAL = 80
RESPAWN_IMMUNITY_DURATION = 1000

# XP and Leveling System Configuration
XP_BASE_REQUIREMENT = 500  # Starting XP needed for level 2
XP_INCREASE_RATE = 0.10  # 10% increase per level (configurable)
UPGRADE_PERCENTAGE = 0.1  # 5% increase per upgrade (configurable)
MAX_UPGRADE_MULTIPLIER = 2.0  # 100% increase maximum (configurable)
BASE_POWERUP_DURATION = 10000  # Base power-up duration in milliseconds

# Boss Configuration
BOSS_HEALTH_BASE = 50  # Base boss health
BOSS_HEALTH_PER_LEVEL = 10  # Additional health per boss level
BOSS_SPEED_BASE = 2.0  # Base boss speed
BOSS_SHOOT_FREQUENCY = 50  # Lower = more frequent shooting
ENEMY_SPEED_PROGRESSION = 0.15  # Speed increase per boss level (every 5 levels)

# Alien Overlord Boss Configuration
ALIEN_BOSS_HEAD_HEALTH_BASE = 65
ALIEN_BOSS_HEAD_HEALTH_PER_LEVEL = 15
ALIEN_BOSS_HAND_HEALTH_BASE = 35
ALIEN_BOSS_HAND_HEALTH_PER_LEVEL = 10
ALIEN_BOSS_HAND_SPEED_BASE = 4.0
ALIEN_BOSS_HAND_SPEED_GROWTH = 0.35
ALIEN_BOSS_DROP_COOLDOWN_BASE = 4200  # ms between hand drops
ALIEN_BOSS_DROP_COOLDOWN_SCALE = 0.9  # Multiplier applied each encounter
ALIEN_BOSS_FIREBALL_COOLDOWN_BASE = 2600  # ms between fireballs
ALIEN_BOSS_FIREBALL_COOLDOWN_SCALE = 0.88

# High scores files
SINGLE_SCORES_FILE = "high_scores_single.json"
COOP_SCORES_FILE = "high_scores_coop.json"

class SoundManager:
    def __init__(self):
        # Initialize pygame mixer with more channels and better settings
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(32)  # Increase from default 8 to 32 channels
        
        # Sound storage
        self.sounds = {}
        self.sound_volume = 0.7  # Global volume control (0.0 to 1.0)
        self.music_volume = 0.5
        
        # Channel management for rapid fire
        self.shoot_channel = None
        self.last_shoot_time = 0
        self.shoot_cooldown = 50  # Minimum ms between shoot sounds to prevent audio spam
        
        # Load all sounds
        self.load_sounds()
        
    def load_sounds(self):
        """Load all sound files"""
        sound_files = {
            'menu_change': 'assets/sounds/menu_change.wav',
            'menu_select': 'assets/sounds/menu_select.wav',
            'shoot': 'assets/sounds/shoot.wav',
            'enemy_shoot': 'assets/sounds/enemy_shoot.wav',
            'explosion_small': 'assets/sounds/explosion_small.wav',
            'explosion_large': 'assets/sounds/explosion_large.wav',
            'laser': 'assets/sounds/laser.wav',
            'powerup': 'assets/sounds/powerup.wav',
            'ufo_hit': 'assets/sounds/ufo_hit.wav',
            'levelup': 'assets/sounds/levelup.wav',
            'player_explosion': 'assets/sounds/player_explosion.wav' 
        }
        
        for sound_name, file_path in sound_files.items():
            try:
                sound = pygame.mixer.Sound(file_path)
                sound.set_volume(self.sound_volume)
                self.sounds[sound_name] = sound
                print(f"Loaded sound: {sound_name}")
            except pygame.error as e:
                print(f"Could not load sound {file_path}: {e}")
                # Create a silent sound as fallback
                self.sounds[sound_name] = None
    
    def play_sound(self, sound_name, volume_override=None):
        """Play a sound effect"""
        if sound_name in self.sounds and self.sounds[sound_name]:
            sound = self.sounds[sound_name]
            if volume_override is not None:
                sound.set_volume(volume_override)
            else:
                sound.set_volume(self.sound_volume)
            sound.play()
    
    def set_volume(self, volume):
        """Set global sound volume (0.0 to 1.0)"""
        self.sound_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(self.sound_volume)
    
    def stop_all_sounds(self):
        """Stop all currently playing sounds"""
        pygame.mixer.stop()

    def play_sound(self, sound_name, volume_override=None, force_play=False):
        """Play a sound effect with smart channel management"""
        if sound_name not in self.sounds or not self.sounds[sound_name]:
            return
            
        sound = self.sounds[sound_name]
        
        # Special handling for shoot sounds to prevent audio spam
        if sound_name == 'shoot':
            current_time = pygame.time.get_ticks()
            
            # If not forcing and too soon since last shoot sound, skip
            if not force_play and current_time - self.last_shoot_time < self.shoot_cooldown:
                return
                
            # Try to reuse the same channel for shoot sounds
            if self.shoot_channel and self.shoot_channel.get_busy():
                # If channel is busy, either skip or force stop depending on situation
                if current_time - self.last_shoot_time < 100:  # Very rapid fire
                    return  # Skip this shot sound
                else:
                    self.shoot_channel.stop()  # Stop previous sound for new one
            
            # Set volume and play
            if volume_override is not None:
                sound.set_volume(volume_override)
            else:
                sound.set_volume(self.sound_volume)
                
            self.shoot_channel = sound.play()
            self.last_shoot_time = current_time
        else:
            # Normal sound playing for non-shoot sounds
            if volume_override is not None:
                sound.set_volume(volume_override)
            else:
                sound.set_volume(self.sound_volume)
            sound.play()
    
    def play_shoot_sound(self, volume_override=None):
        """Dedicated method for shoot sounds with rate limiting"""
        self.play_sound('shoot', volume_override, force_play=False)

class XPSystem:
    def __init__(self):
        self.current_xp = 0
        self.level = 1
        self.xp_for_next_level = XP_BASE_REQUIREMENT
        
    def add_xp(self, amount):
        """Add XP and check for level up"""
        self.current_xp += amount
        leveled_up = False
        
        while self.current_xp >= self.xp_for_next_level:
            self.current_xp -= self.xp_for_next_level
            self.level += 1
            leveled_up = True
            # Calculate next level requirement with exponential growth
            self.xp_for_next_level = int(XP_BASE_REQUIREMENT * (1 + XP_INCREASE_RATE) ** (self.level - 1))
            
        return leveled_up
    
    def get_xp_progress(self):
        """Get XP progress as percentage"""
        return self.current_xp / self.xp_for_next_level if self.xp_for_next_level > 0 else 0

class PlayerUpgrades:
    def __init__(self):
        self.shot_speed_level = 0
        self.fire_rate_level = 0
        self.movement_speed_level = 0
        self.powerup_duration_level = 0
        self.pierce_level = 0
        self.bullet_length_level = 0
        self.barrier_phase_level = 0
        self.powerup_spawn_level = 0
        self.boss_damage_level = 0
        self.ammo_capacity_level = 0
        self.extra_bullet_level = 0
        
    def get_max_upgrade_level(self):
        """Calculate maximum upgrade level based on multiplier"""
        # If max multiplier is 2.0 (100% increase) and each upgrade is 5%, max level is 20
        return int((MAX_UPGRADE_MULTIPLIER - 1.0) / UPGRADE_PERCENTAGE)
        
    def can_upgrade(self, stat):
        """Check if a stat can be upgraded further"""
        if stat in ["pierce", "powerup_spawn", "boss_damage", "ammo_capacity"]:
            max_levels = 5
        elif stat == "barrier_phase":
            max_levels = 1
        elif stat == "extra_bullet":
            max_levels = 1
        elif stat == "bullet_length":
            max_levels = None  # Infinite scaling
        else:
            max_levels = self.get_max_upgrade_level()

        current_level = getattr(self, f"{stat}_level")
        if max_levels is None:
            return True
        return current_level < max_levels
        
    def upgrade_stat(self, stat):
        """Upgrade a specific stat"""
        if self.can_upgrade(stat):
            setattr(self, f"{stat}_level", getattr(self, f"{stat}_level") + 1)
            return True
        return False
        
    def get_multiplier(self, stat):
        """Get the multiplier for a specific stat"""
        level = getattr(self, f"{stat}_level")
        if stat == "bullet_length":
            return 1.0 + (level * 0.10)
        if stat == "powerup_spawn":
            return 1.0 + (level * 0.05)
        if stat == "boss_damage":
            return 1.0 + (level * 0.10)
        return 1.0 + (level * UPGRADE_PERCENTAGE)

    def get_pierce_hits(self):
        return self.pierce_level

    def can_phase_barriers(self):
        return self.barrier_phase_level > 0

    def get_bullet_length_multiplier(self):
        return self.get_multiplier("bullet_length")

    def get_powerup_spawn_bonus(self):
        # Base 5% chance plus stacking 5% bonuses
        return self.powerup_spawn_level * 5

    def get_boss_damage_multiplier(self):
        return self.get_multiplier("boss_damage")

    def get_ammo_powerup_capacity(self):
        return 1 + self.ammo_capacity_level

    def has_extra_bullet(self):
        return self.extra_bullet_level > 0

class FloatingText:
    def __init__(self, x, y, text, color=YELLOW, duration=1000):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.font = pygame.font.Font(None, 36)
        
    def update(self):
        """Update floating text position and check if expired"""
        self.y -= 1  # Float upward
        current_time = pygame.time.get_ticks()
        return current_time - self.start_time < self.duration
        
    def draw(self, screen):
        """Draw the floating text with fade effect"""
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        alpha = max(0, 255 - int((elapsed / self.duration) * 255))
        
        text_surface = self.font.render(self.text, True, self.color)
        text_surface.set_alpha(alpha)
        screen.blit(text_surface, (self.x, self.y))
        
class LevelUpScreen:
    def __init__(self, screen, players, is_coop=False, sound_manager=None, xp_level=1):
        self.screen = screen
        self.players = players
        self.is_coop = is_coop
        self.sound_manager = sound_manager
        self.xp_level = xp_level
        self.font_large = pygame.font.Font(None, 96)
        self.font_medium = pygame.font.Font(None, 64)
        self.font_small = pygame.font.Font(None, 48)
        self.tiny_font = pygame.font.Font(None, 36)
        
        self.base_upgrade_options = [
            ("shot_speed", "Shot Speed", "Increase bullet travel speed"),
            ("fire_rate", "Fire Rate", "Reduce shooting cooldown"),
            ("movement_speed", "Movement Speed", "Increase player movement speed"),
            ("powerup_duration", "Power-up Duration", "Extend power-up effects")
        ]

        self.permanent_upgrade_pool = [
            ("pierce", "Piercing Shot", "Bullets pierce through +1 enemy (stacks to 5)"),
            ("bullet_length", "Longer Bullets", "Bullet length grows by 10% (stackable)"),
            ("barrier_phase", "Barrier Phasing", "Bullets pass through green barriers"),
            ("powerup_spawn", "Lucky Drops", "Power-ups spawn 5% more often (up to 5)"),
            ("boss_damage", "Boss Breaker", "Bullets deal +10% boss damage (up to 5)"),
            ("ammo_capacity", "Ammo Belt", "Store extra ammo power-ups (up to 5)"),
            ("extra_bullet", "Twin Shot", "Add +1 bullet to every shot (one time)")
        ]

        self.player_options = []
        for player in self.players:
            options = list(self.base_upgrade_options)
            if self.xp_level % 5 == 0:
                options.append(("extra_life", "Extra Life", "Gain +1 life instead of a stat upgrade"))
                permanent_choice = self.get_random_permanent_option(player)
                if permanent_choice:
                    options.append(permanent_choice)
            self.player_options.append(options)

        self.upgrade_options = self.player_options[0] if self.player_options else []
        
        # For co-op mode, track each player's selection
        self.player1_selection = 0
        self.player2_selection = 0
        self.player1_confirmed = False
        self.player2_confirmed = False
        
        # For single player
        self.current_selection = 0
        
        # Input delay and countdown system
        self.start_time = pygame.time.get_ticks()
        self.input_delay = 2000  # 2 seconds input lock
        self.countdown_start = None
        self.countdown_duration = 3000  # 3 seconds countdown
        
        # Visual feedback for upgrades
        self.upgrade_effects = []  # Store floating upgrade indicators

        # Controllers
        self.controllers = []
        for i in range(pygame.joystick.get_count()):
            controller = pygame.joystick.Joystick(i)
            controller.init()
            self.controllers.append(controller)

    def get_available_permanent_options(self, player):
        available = []
        for stat_name, display_name, description in self.permanent_upgrade_pool:
            if player.upgrades.can_upgrade(stat_name):
                available.append((stat_name, display_name, description))
        return available

    def get_random_permanent_option(self, player):
        options = self.get_available_permanent_options(player)
        if not options:
            return None
        return random.choice(options)

    def get_options_for_player(self, player_index):
        if 0 <= player_index < len(self.player_options):
            return self.player_options[player_index]
        return self.upgrade_options

    def get_option_at(self, player_index, row_index):
        options = self.get_options_for_player(player_index)
        if 0 <= row_index < len(options):
            return options[row_index]
        return None
          
    def handle_events(self):
        # FIXED: During input delay, consume ALL events to prevent buffering
        if pygame.time.get_ticks() - self.start_time < self.input_delay:
            # Clear the event queue during input delay to prevent input buffering
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
            return None
            
        # If countdown is active, don't accept input
        if self.countdown_start is not None:
            if pygame.time.get_ticks() - self.countdown_start >= self.countdown_duration:
                return "continue"
            return None
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if not self.is_coop:
                    # Single player keyboard controls
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        if self.sound_manager:
                            self.sound_manager.play_sound('menu_change')
                        options = self.get_options_for_player(0)
                        self.current_selection = (self.current_selection - 1) % len(options)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        if self.sound_manager:
                            self.sound_manager.play_sound('menu_change')
                        options = self.get_options_for_player(0)
                        self.current_selection = (self.current_selection + 1) % len(options)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        options = self.get_options_for_player(0)
                        stat_name = options[self.current_selection][0]
                        if stat_name == "extra_life":
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_select')
                            self.grant_extra_life(0, stat_name)
                            self.countdown_start = pygame.time.get_ticks()
                            self.countdown_duration = 2000
                        elif self.players[0].upgrades.can_upgrade(stat_name):
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_select')
                            old_multiplier = self.players[0].upgrades.get_multiplier(stat_name)
                            self.players[0].upgrades.upgrade_stat(stat_name)
                            new_multiplier = self.players[0].upgrades.get_multiplier(stat_name)
                            self.create_upgrade_effect(0, stat_name, old_multiplier, new_multiplier)
                            # Start a brief countdown for single player too
                            self.countdown_start = pygame.time.get_ticks()
                            self.countdown_duration = 2000  # 2 seconds to see the effect
                else:
                    # Co-op keyboard controls (Player 1)
                    if not self.player1_confirmed:
                        if event.key == pygame.K_UP or event.key == pygame.K_w:
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_change')
                            p1_options = self.get_options_for_player(0)
                            self.player1_selection = (self.player1_selection - 1) % len(p1_options)
                        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_change')
                            p1_options = self.get_options_for_player(0)
                            self.player1_selection = (self.player1_selection + 1) % len(p1_options)
                        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                            p1_options = self.get_options_for_player(0)
                            stat_name = p1_options[self.player1_selection][0]
                            if stat_name == "extra_life":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                self.grant_extra_life(0, stat_name)
                                self.player1_confirmed = True
                            elif self.players[0].upgrades.can_upgrade(stat_name):
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                old_multiplier = self.players[0].upgrades.get_multiplier(stat_name)
                                self.players[0].upgrades.upgrade_stat(stat_name)
                                new_multiplier = self.players[0].upgrades.get_multiplier(stat_name)
                                self.create_upgrade_effect(0, stat_name, old_multiplier, new_multiplier)
                                self.player1_confirmed = True

                    # Player 2 controls (Right Ctrl for confirm, arrows for selection)
                    if not self.player2_confirmed:
                        if event.key == pygame.K_LEFT:
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_change')
                            p2_options = self.get_options_for_player(1)
                            self.player2_selection = (self.player2_selection - 1) % len(p2_options)
                        elif event.key == pygame.K_RIGHT:
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_change')
                            p2_options = self.get_options_for_player(1)
                            self.player2_selection = (self.player2_selection + 1) % len(p2_options)
                        elif event.key == pygame.K_RCTRL:
                            p2_options = self.get_options_for_player(1)
                            stat_name = p2_options[self.player2_selection][0]
                            if stat_name == "extra_life":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                self.grant_extra_life(1, stat_name)
                                self.player2_confirmed = True
                            elif self.players[1].upgrades.can_upgrade(stat_name):
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                old_multiplier = self.players[1].upgrades.get_multiplier(stat_name)
                                self.players[1].upgrades.upgrade_stat(stat_name)
                                new_multiplier = self.players[1].upgrades.get_multiplier(stat_name)
                                self.create_upgrade_effect(1, stat_name, old_multiplier, new_multiplier)
                                self.player2_confirmed = True
                    
                    # Check if both players confirmed - start countdown
                    if self.player1_confirmed and self.player2_confirmed and self.countdown_start is None:
                        self.countdown_start = pygame.time.get_ticks()
                        
            elif event.type == pygame.JOYBUTTONDOWN:
                if not self.is_coop:
                    # Single player controller
                    if event.button == 0:  # A button
                        options = self.get_options_for_player(0)
                        stat_name = options[self.current_selection][0]
                        if stat_name == "extra_life":
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_select')
                            self.grant_extra_life(0, stat_name)
                            self.countdown_start = pygame.time.get_ticks()
                            self.countdown_duration = 2000
                        elif self.players[0].upgrades.can_upgrade(stat_name):
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_select')
                            old_multiplier = self.players[0].upgrades.get_multiplier(stat_name)
                            self.players[0].upgrades.upgrade_stat(stat_name)
                            new_multiplier = self.players[0].upgrades.get_multiplier(stat_name)
                            self.create_upgrade_effect(0, stat_name, old_multiplier, new_multiplier)
                            # Start a brief countdown for single player too
                            self.countdown_start = pygame.time.get_ticks()
                            self.countdown_duration = 2000  # 2 seconds to see the effect
                else:
                    # Co-op controller handling
                    if len(self.controllers) > 0 and event.joy == 0 and not self.player1_confirmed:
                        if event.button == 0:  # A button
                            p1_options = self.get_options_for_player(0)
                            stat_name = p1_options[self.player1_selection][0]
                            if stat_name == "extra_life":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                self.grant_extra_life(0, stat_name)
                                self.player1_confirmed = True
                            elif self.players[0].upgrades.can_upgrade(stat_name):
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                old_multiplier = self.players[0].upgrades.get_multiplier(stat_name)
                                self.players[0].upgrades.upgrade_stat(stat_name)
                                new_multiplier = self.players[0].upgrades.get_multiplier(stat_name)
                                self.create_upgrade_effect(0, stat_name, old_multiplier, new_multiplier)
                                self.player1_confirmed = True

                    if len(self.controllers) > 1 and event.joy == 1 and not self.player2_confirmed:
                        if event.button == 0:  # A button
                            p2_options = self.get_options_for_player(1)
                            stat_name = p2_options[self.player2_selection][0]
                            if stat_name == "extra_life":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                self.grant_extra_life(1, stat_name)
                                self.player2_confirmed = True
                            elif self.players[1].upgrades.can_upgrade(stat_name):
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                old_multiplier = self.players[1].upgrades.get_multiplier(stat_name)
                                self.players[1].upgrades.upgrade_stat(stat_name)
                                new_multiplier = self.players[1].upgrades.get_multiplier(stat_name)
                                self.create_upgrade_effect(1, stat_name, old_multiplier, new_multiplier)
                                self.player2_confirmed = True
                    
                    # Check if both players confirmed - start countdown
                    if self.player1_confirmed and self.player2_confirmed and self.countdown_start is None:
                        self.countdown_start = pygame.time.get_ticks()
                        
            elif event.type == pygame.JOYHATMOTION:
                if not self.is_coop:
                    # Single player controller
                    if event.value[1] == 1:  # Up
                        if self.sound_manager:
                            self.sound_manager.play_sound('menu_change')
                        options = self.get_options_for_player(0)
                        self.current_selection = (self.current_selection - 1) % len(options)
                    elif event.value[1] == -1:  # Down
                        if self.sound_manager:
                            self.sound_manager.play_sound('menu_change')
                        options = self.get_options_for_player(0)
                        self.current_selection = (self.current_selection + 1) % len(options)
                else:
                    # Co-op controller handling
                    if len(self.controllers) > 0 and event.joy == 0 and not self.player1_confirmed:
                        if event.value[1] == 1:  # Up
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_change')
                            p1_options = self.get_options_for_player(0)
                            self.player1_selection = (self.player1_selection - 1) % len(p1_options)
                        elif event.value[1] == -1:  # Down
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_change')
                            p1_options = self.get_options_for_player(0)
                            self.player1_selection = (self.player1_selection + 1) % len(p1_options)

                    if len(self.controllers) > 1 and event.joy == 1 and not self.player2_confirmed:
                        if event.value[1] == 1:  # Up
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_change')
                            p2_options = self.get_options_for_player(1)
                            self.player2_selection = (self.player2_selection - 1) % len(p2_options)
                        elif event.value[1] == -1:  # Down
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_change')
                            p2_options = self.get_options_for_player(1)
                            self.player2_selection = (self.player2_selection + 1) % len(p2_options)
                            
        return None
        
    def create_upgrade_effect(self, player_index, stat_name, old_multiplier, new_multiplier):
        """Create floating upgrade indicator"""
        x, y = self.get_effect_position(player_index, stat_name)

        # Create floating text showing the upgrade
        old_percent = int((old_multiplier - 1) * 100)
        new_percent = int((new_multiplier - 1) * 100)
        text = f"+{old_percent}% → +{new_percent}%"
        
        effect = {
            'x': x,
            'y': y,
            'text': text,
            'color': GREEN if player_index == 0 else BLUE,
            'start_time': pygame.time.get_ticks(),
            'duration': 2000  # 2 seconds duration
        }
        self.upgrade_effects.append(effect)

    def grant_extra_life(self, player_index, stat_name):
        """Grant an extra life instead of a stat upgrade"""
        self.players[player_index].lives += 1
        x, y = self.get_effect_position(player_index, stat_name)

        effect = {
            'x': x,
            'y': y,
            'text': "+1 LIFE",
            'color': GOLD,
            'start_time': pygame.time.get_ticks(),
            'duration': 2000
        }
        self.upgrade_effects.append(effect)

    def get_effect_position(self, player_index, stat_name):
        """Calculate the effect position based on player and selected option"""
        stat_index = 0
        options = self.get_options_for_player(player_index)
        for i, entry in enumerate(options):
            stat, _, _ = entry
            if stat == stat_name:
                stat_index = i
                break

        if self.is_coop:
            x = 350 if player_index == 0 else 1250
        else:
            x = 600

        y = 240 + (stat_index * 80) + 40
        return x, y
        
    def draw(self):
        self.screen.fill(BLACK)
        
        # Update upgrade effects
        current_time = pygame.time.get_ticks()
        self.upgrade_effects = [effect for effect in self.upgrade_effects 
                               if current_time - effect['start_time'] < effect['duration']]
        
        # Title
        title_text = self.font_large.render("LEVEL UP!", True, GOLD)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Input delay indicator
        if pygame.time.get_ticks() - self.start_time < self.input_delay:
            remaining = (self.input_delay - (pygame.time.get_ticks() - self.start_time)) / 1000.0
            delay_text = self.font_medium.render(f"Input unlocks in {remaining:.1f}s", True, YELLOW)
            delay_rect = delay_text.get_rect(center=(SCREEN_WIDTH // 2, 140))
            self.screen.blit(delay_text, delay_rect)
            return  # Don't draw the rest during input delay
            
        if self.is_coop:
            # Table layout for co-op
            table_center = SCREEN_WIDTH // 2
            left_col_x = table_center - 420
            right_col_x = table_center + 420
            header_y = 170
            table_top = header_y + 50
            row_height = 80

            # Headers
            p1_header = self.font_medium.render("PLAYER 1", True, GREEN)
            desc_header = self.font_medium.render("UPGRADE", True, WHITE)
            p2_header = self.font_medium.render("PLAYER 2", True, BLUE)

            self.screen.blit(p1_header, p1_header.get_rect(center=(left_col_x, header_y)))
            self.screen.blit(desc_header, desc_header.get_rect(center=(table_center, header_y)))
            self.screen.blit(p2_header, p2_header.get_rect(center=(right_col_x, header_y)))

            # Table rows
            start_y = table_top

            max_rows = max((len(opts) for opts in self.player_options), default=0)
            table_height = max_rows * row_height

            # Background panel behind the table for readability
            panel_margin_x = 220
            panel_width = SCREEN_WIDTH - (panel_margin_x * 2)
            panel_height = table_height + 40
            panel_rect = pygame.Rect(panel_margin_x, start_y - 20, panel_width, panel_height)
            pygame.draw.rect(self.screen, (10, 10, 10), panel_rect, border_radius=12)
            pygame.draw.rect(self.screen, (40, 40, 40), panel_rect, 2, border_radius=12)

            for i in range(max_rows):
                y = start_y + i * row_height
                p1_option = self.get_option_at(0, i)
                p2_option = self.get_option_at(1, i) if len(self.players) > 1 else None
                display_option = p1_option or p2_option
                if not display_option:
                    continue
                stat_name, display_name, description = display_option

                # Row background (alternating)
                if i % 2 == 1:
                    pygame.draw.rect(self.screen, (20, 20, 20), (panel_margin_x + 10, y - 5, panel_width - 20, row_height - 10), border_radius=6)

                # Selection arrows (outside table)
                if p1_option and i == self.player1_selection and not self.player1_confirmed:
                    arrow_points = [(panel_margin_x - 25, y + 15), (panel_margin_x - 25, y + 35), (panel_margin_x + 5, y + 25)]
                    pygame.draw.polygon(self.screen, GREEN, arrow_points)

                if p2_option and i == self.player2_selection and not self.player2_confirmed:
                    arrow_points = [(panel_margin_x + panel_width + 25, y + 15), (panel_margin_x + panel_width + 25, y + 35), (panel_margin_x + panel_width - 5, y + 25)]
                    pygame.draw.polygon(self.screen, BLUE, arrow_points)

                # Middle column - Upgrade description
                name_text = self.tiny_font.render(display_name, True, WHITE)
                desc_text = self.tiny_font.render(description, True, GRAY)
                name_rect = name_text.get_rect(center=(table_center, y + 15))
                desc_rect = desc_text.get_rect(center=(table_center, y + 35))
                self.screen.blit(name_text, name_rect)
                self.screen.blit(desc_text, desc_rect)

                # Left column - Player 1 stats
                p1_stat_name = p1_option[0] if p1_option else None
                p1_display_name = p1_option[1] if p1_option else ""
                if p1_display_name:
                    name_surface = self.tiny_font.render(p1_display_name, True, WHITE)
                    self.screen.blit(name_surface, name_surface.get_rect(topleft=(left_col_x - 70, y)))

                if p1_stat_name == "extra_life":
                    p1_color = WHITE
                    if self.player1_confirmed and i == self.player1_selection:
                        confirm_text = self.tiny_font.render("✓ SELECTED", True, GREEN)
                        self.screen.blit(confirm_text, confirm_text.get_rect(topleft=(left_col_x - 70, y + 25)))
                    elif p1_option:
                        lives_text = self.tiny_font.render(f"Lives: {self.players[0].lives}", True, p1_color)
                        self.screen.blit(lives_text, lives_text.get_rect(topleft=(left_col_x - 70, y + 25)))
                elif p1_option:
                    p1_can_upgrade = self.players[0].upgrades.can_upgrade(p1_stat_name)
                    p1_level = getattr(self.players[0].upgrades, f"{p1_stat_name}_level")
                    p1_multiplier = self.players[0].upgrades.get_multiplier(p1_stat_name)
                    p1_color = WHITE if p1_can_upgrade else GRAY

                    if self.player1_confirmed and i == self.player1_selection:
                        confirm_text = self.tiny_font.render("✓ SELECTED", True, GREEN)
                        self.screen.blit(confirm_text, confirm_text.get_rect(topleft=(left_col_x - 70, y + 25)))
                    else:
                        p1_level_text = self.tiny_font.render(f"Lv {p1_level}", True, p1_color)
                        p1_bonus_text = self.tiny_font.render(f"+{int((p1_multiplier - 1) * 100)}%", True, YELLOW if p1_can_upgrade else GRAY)
                        self.screen.blit(p1_level_text, p1_level_text.get_rect(topleft=(left_col_x - 70, y + 15)))
                        self.screen.blit(p1_bonus_text, p1_bonus_text.get_rect(topleft=(left_col_x - 70, y + 35)))

                # Right column - Player 2 stats
                p2_stat_name = p2_option[0] if p2_option else None
                p2_display_name = p2_option[1] if p2_option else ""
                if p2_display_name:
                    name_surface = self.tiny_font.render(p2_display_name, True, WHITE)
                    name_rect = name_surface.get_rect()
                    name_rect.right = right_col_x + 70
                    name_rect.y = y
                    self.screen.blit(name_surface, name_rect)

                if p2_stat_name == "extra_life":
                    p2_color = WHITE
                    if self.player2_confirmed and i == self.player2_selection:
                        confirm_text = self.tiny_font.render("✓ SELECTED", True, BLUE)
                        confirm_rect = confirm_text.get_rect()
                        confirm_rect.topleft = (right_col_x - 70, y + 25)
                        self.screen.blit(confirm_text, confirm_rect)
                    elif p2_option:
                        lives_text = self.tiny_font.render(f"Lives: {self.players[1].lives}", True, p2_color)
                        self.screen.blit(lives_text, lives_text.get_rect(topleft=(right_col_x - 70, y + 25)))
                elif p2_option:
                    p2_can_upgrade = self.players[1].upgrades.can_upgrade(p2_stat_name)
                    p2_level = getattr(self.players[1].upgrades, f"{p2_stat_name}_level")
                    p2_multiplier = self.players[1].upgrades.get_multiplier(p2_stat_name)
                    p2_color = WHITE if p2_can_upgrade else GRAY

                    if self.player2_confirmed and i == self.player2_selection:
                        confirm_text = self.tiny_font.render("✓ SELECTED", True, BLUE)
                        confirm_rect = confirm_text.get_rect()
                        confirm_rect.topleft = (right_col_x - 70, y + 25)
                        self.screen.blit(confirm_text, confirm_rect)
                    else:
                        p2_level_text = self.tiny_font.render(f"Lv {p2_level}", True, p2_color)
                        p2_bonus_text = self.tiny_font.render(f"+{int((p2_multiplier - 1) * 100)}%", True, YELLOW if p2_can_upgrade else GRAY)
                        self.screen.blit(p2_level_text, p2_level_text.get_rect(topleft=(right_col_x - 70, y + 15)))
                        self.screen.blit(p2_bonus_text, p2_bonus_text.get_rect(topleft=(right_col_x - 70, y + 35)))

            # FIXED: Only show ONE countdown or instruction section
            instructions_y = min(SCREEN_HEIGHT - 60, start_y + table_height + 60)
            if self.countdown_start is not None:
                # Countdown when both players ready
                elapsed = pygame.time.get_ticks() - self.countdown_start
                remaining = max(0, (self.countdown_duration - elapsed) / 1000.0)
                countdown_text = self.font_large.render(f"Next level in {remaining:.1f}s", True, GOLD)
                countdown_rect = countdown_text.get_rect(center=(SCREEN_WIDTH // 2, instructions_y))
                self.screen.blit(countdown_text, countdown_rect)
            else:
                # Instructions (only show when NOT counting down)
                if not self.player1_confirmed or not self.player2_confirmed:
                    inst_text = self.tiny_font.render("P1: WASD + Enter  |  P2: Arrows + Right Ctrl  |  Controllers: D-pad + A", True, GRAY)
                    inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, instructions_y))
                    self.screen.blit(inst_text, inst_rect)
        
        else:
            # Single player layout
            desc_header = self.font_medium.render("UPGRADES", True, WHITE)
            self.screen.blit(desc_header, desc_header.get_rect(center=(SCREEN_WIDTH // 2, 170)))

            start_y = 230
            row_height = 80

            options = self.get_options_for_player(0)
            panel_margin_x = 300
            panel_width = SCREEN_WIDTH - (panel_margin_x * 2)
            panel_height = len(options) * row_height + 40
            panel_rect = pygame.Rect(panel_margin_x, start_y - 20, panel_width, panel_height)
            pygame.draw.rect(self.screen, (10, 10, 10), panel_rect, border_radius=12)
            pygame.draw.rect(self.screen, (40, 40, 40), panel_rect, 2, border_radius=12)

            for i, (stat_name, display_name, description) in enumerate(options):
                y = start_y + i * row_height

                if i % 2 == 1:
                    pygame.draw.rect(self.screen, (20, 20, 20), (panel_margin_x + 10, y - 5, panel_width - 20, row_height - 10), border_radius=6)

                # Selection arrow
                if i == self.current_selection:
                    arrow_points = [(panel_margin_x - 30, y + 15), (panel_margin_x - 30, y + 35), (panel_margin_x, y + 25)]
                    pygame.draw.polygon(self.screen, GREEN, arrow_points)

                # Upgrade info
                name_text = self.tiny_font.render(display_name, True, WHITE)
                desc_text = self.tiny_font.render(description, True, GRAY)
                self.screen.blit(name_text, name_text.get_rect(topleft=(panel_margin_x + 40, y + 10)))
                self.screen.blit(desc_text, desc_text.get_rect(topleft=(panel_margin_x + 40, y + 30)))

                # Stats
                if stat_name == "extra_life":
                    lives_text = self.tiny_font.render(f"Lives: {self.players[0].lives}", True, WHITE)
                    self.screen.blit(lives_text, lives_text.get_rect(topleft=(panel_margin_x + 40, y + 50)))
                else:
                    can_upgrade = self.players[0].upgrades.can_upgrade(stat_name)
                    level = getattr(self.players[0].upgrades, f"{stat_name}_level")
                    multiplier = self.players[0].upgrades.get_multiplier(stat_name)

                    level_text = self.tiny_font.render(f"Level {level} (+{int((multiplier - 1) * 100)}%)", True, WHITE if can_upgrade else GRAY)
                    self.screen.blit(level_text, level_text.get_rect(topleft=(panel_margin_x + 40, y + 50)))

            # FIXED: Only show ONE countdown or instruction section for single player
            instructions_y = min(SCREEN_HEIGHT - 60, start_y + len(options) * row_height + 60)
            if self.countdown_start is not None:
                # Countdown for single player after upgrade
                elapsed = pygame.time.get_ticks() - self.countdown_start
                remaining = max(0, (self.countdown_duration - elapsed) / 1000.0)
                countdown_text = self.font_large.render(f"Continuing in {remaining:.1f}s", True, GOLD)
                countdown_rect = countdown_text.get_rect(center=(SCREEN_WIDTH // 2, instructions_y))
                self.screen.blit(countdown_text, countdown_rect)
            else:
                # Instructions (only show when NOT counting down)
                inst_text = self.tiny_font.render("WASD/Arrows: Navigate  |  Enter/Space: Select  |  Controller: D-pad + A", True, GRAY)
                inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, instructions_y))
                self.screen.blit(inst_text, inst_rect)
        
        # Draw floating upgrade effects
        for effect in self.upgrade_effects:
            elapsed = current_time - effect['start_time']
            alpha = max(0, 255 - int((elapsed / effect['duration']) * 255))
            y_offset = -int(elapsed * 0.08)
            
            effect_surface = self.font_small.render(effect['text'], True, effect['color'])
            effect_surface.set_alpha(alpha)
            
            # Add background for better visibility
            text_rect = effect_surface.get_rect()
            bg_surface = pygame.Surface((text_rect.width + 20, text_rect.height + 10), pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, 128))
            
            self.screen.blit(bg_surface, (effect['x'] - 10, effect['y'] + y_offset - 5))
            self.screen.blit(effect_surface, (effect['x'], effect['y'] + y_offset))
        
        pygame.display.flip()

class TargetedBullet:
    def __init__(self, x, y, vel_x, vel_y):
        self.x = x
        self.y = y
        self.width = 8
        self.height = 8
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
    def move(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.rect.x = self.x
        self.rect.y = self.y
        
    def is_off_screen(self):
        return (self.x < -20 or self.x > SCREEN_WIDTH + 20 or 
                self.y < -20 or self.y > SCREEN_HEIGHT + 20)
        
    def draw(self, screen):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), 4)
        pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y)), 2)

class LargeBullet:
    def __init__(self, x, y, speed):
        self.x = x
        self.y = y
        self.width = 15
        self.height = 20
        self.speed = speed
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
    def move(self):
        self.y += self.speed
        self.rect.y = self.y
        
    def is_off_screen(self):
        return self.y < -30 or self.y > SCREEN_HEIGHT + 30
        
    def draw(self, screen):
        # Large glowing bullet
        pygame.draw.ellipse(screen, RED, (self.x - 7, self.y - 10, 15, 20))
        pygame.draw.ellipse(screen, ORANGE, (self.x - 4, self.y - 7, 9, 14))
        pygame.draw.ellipse(screen, YELLOW, (self.x - 2, self.y - 5, 5, 10))

class FireballProjectile:
    def __init__(self, x, y, target_x, target_y, speed):
        self.x = x
        self.y = y
        self.width = 26
        self.height = 26
        self.speed = speed
        dx = target_x - x
        dy = target_y - y
        distance = math.hypot(dx, dy) or 1
        self.vel_x = (dx / distance) * speed
        self.vel_y = (dy / distance) * speed
        self.rect = pygame.Rect(int(self.x - self.width // 2), int(self.y - self.height // 2), self.width, self.height)

    def move(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.rect.x = int(self.x - self.width // 2)
        self.rect.y = int(self.y - self.height // 2)

    def is_off_screen(self):
        return (self.x < -50 or self.x > SCREEN_WIDTH + 50 or
                self.y < -50 or self.y > SCREEN_HEIGHT + 50)

    def draw(self, screen):
        center = (int(self.x), int(self.y))
        pygame.draw.circle(screen, (255, 90, 0), center, 14)
        pygame.draw.circle(screen, (255, 140, 0), center, 10)
        pygame.draw.circle(screen, (255, 220, 120), center, 6)

class Boss:
    def __init__(self, level):
        # Boss configuration
        self.width = SCREEN_WIDTH // 3  # One third of screen width
        self.height = int(self.width * 0.6)  # Proportional height
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = 150
        
        # Health system
        self.max_health = BOSS_HEALTH_BASE + (level // 5 - 1) * BOSS_HEALTH_PER_LEVEL
        self.health = self.max_health
        self.turret_health_percentage = 0.20  # Configurable: 20% of main body health
        self.max_turret_health = int(self.max_health * self.turret_health_percentage)
        
        # Turret system
        self.turrets = [
            {'health': self.max_turret_health, 'max_health': self.max_turret_health, 'destroyed': False, 'last_shot': 0, 'cooldown': 1200},
            {'health': self.max_turret_health, 'max_health': self.max_turret_health, 'destroyed': False, 'last_shot': 400, 'cooldown': 1200},  # Staggered start
            {'health': self.max_turret_health, 'max_health': self.max_turret_health, 'destroyed': False, 'last_shot': 800, 'cooldown': 1200}   # Staggered start
        ]
        
        # Movement
        self.speed = BOSS_SPEED_BASE
        self.direction = random.choice([-1, 1])
        self.last_direction_change = pygame.time.get_ticks()
        self.direction_change_cooldown = random.randint(1000, 3000)
        
        # Main body shooting (when turrets destroyed)
        self.main_body_last_shot = 0
        self.main_body_cooldown = 800
        
        # Visual effects
        self.debris_effects = []
        self.explosion_effects = []
        self.destruction_complete = False
        self.destruction_start_time = 0
        
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
    def get_turret_positions(self):
        """Get the screen positions of the three turrets"""
        turret_spacing = self.width // 4
        base_y = self.y + int(self.height * 0.8)  # Near bottom of UFO
        
        return [
            (self.x + turret_spacing, base_y),           # Left turret
            (self.x + self.width // 2, base_y),         # Center turret  
            (self.x + self.width - turret_spacing, base_y)  # Right turret
        ]
        
    def get_nearest_player_position(self, turret_pos, players):
        """Find the nearest alive player to a turret"""
        alive_players = [p for p in players if p.is_alive]
        if not alive_players:
            return None
            
        nearest_player = None
        min_distance = float('inf')
        
        for player in alive_players:
            player_center = (player.x + player.width // 2, player.y + player.height // 2)
            distance = math.sqrt((turret_pos[0] - player_center[0])**2 + (turret_pos[1] - player_center[1])**2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_player = player_center
                
        return nearest_player
        
    def update(self, players=None, sound_manager=None):
        if self.destruction_complete:
            # Update explosion effects during destruction
            self.explosion_effects = [exp for exp in self.explosion_effects if exp['life'] > 0]
            for explosion in self.explosion_effects:
                explosion['radius'] += explosion['growth']
                explosion['life'] -= 1
                # Stop growing at max radius
                if 'max_radius' in explosion and explosion['radius'] >= explosion['max_radius']:
                    explosion['growth'] = 0
            return
            
        # Normal UFO movement (existing code)
        self.x += self.speed * self.direction
        
        if self.x <= 0 or self.x >= SCREEN_WIDTH - self.width:
            self.direction *= -1
        
        current_time = pygame.time.get_ticks()
        if current_time - self.last_direction_change > self.direction_change_cooldown:
            if random.randint(1, 100) <= 30:
                self.direction *= -1
                self.last_direction_change = current_time
                self.direction_change_cooldown = random.randint(1000, 3000)
        
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Update debris effects
        self.debris_effects = [debris for debris in self.debris_effects if debris['life'] > 0]
        for debris in self.debris_effects:
            debris['x'] += debris['vel_x']
            debris['y'] += debris['vel_y']
            debris['vel_y'] += 0.2
            debris['life'] -= 1
            
        # Update explosion effects  
        self.explosion_effects = [exp for exp in self.explosion_effects if exp['life'] > 0]
        for explosion in self.explosion_effects:
            explosion['radius'] += explosion['growth']
            explosion['life'] -= 1
        
    def shoot(self, players, sound_manager=None):
        """Boss shooting patterns"""
        if self.destruction_complete:
            return []
            
        bullets = []
        current_time = pygame.time.get_ticks()
        turret_positions = self.get_turret_positions()
        
        # Count active turrets for fire rate calculation
        active_turrets = sum(1 for turret in self.turrets if not turret['destroyed'])
        
        # Calculate fire rate increase (faster as turrets destroyed)
        fire_rate_multiplier = 1.0 + (3 - active_turrets) * 0.3  # 30% faster per destroyed turret
        
        # Turret shooting
        turret_shot_fired = False
        for i, (turret, pos) in enumerate(zip(self.turrets, turret_positions)):
            if turret['destroyed']:
                continue
                
            adjusted_cooldown = turret['cooldown'] / fire_rate_multiplier
            
            if current_time - turret['last_shot'] > adjusted_cooldown:
                target_pos = self.get_nearest_player_position(pos, players)
                if target_pos:
                    # Calculate angle to target
                    dx = target_pos[0] - pos[0]
                    dy = target_pos[1] - pos[1]
                    
                    # Create bullet with velocity toward target
                    speed = BASE_BULLET_SPEED * 0.8  # Slightly slower than player bullets
                    distance = math.sqrt(dx*dx + dy*dy)
                    if distance > 0:
                        vel_x = (dx / distance) * speed
                        vel_y = (dy / distance) * speed
                        bullet = TargetedBullet(pos[0], pos[1], vel_x, vel_y)
                        bullets.append(bullet)
                        turret_shot_fired = True
                        
                turret['last_shot'] = current_time
        
        # Play sound for turret shots
        if turret_shot_fired and sound_manager:
            sound_manager.play_sound('enemy_shoot', volume_override=0.4)
        
        # Main body shooting (when all turrets destroyed)
        if active_turrets == 0:
            if current_time - self.main_body_last_shot > self.main_body_cooldown:
                center_x = self.x + self.width // 2
                center_y = self.y + self.height
                
                # Fire larger, more powerful shots
                bullet = LargeBullet(center_x, center_y, BASE_BULLET_SPEED)
                bullets.append(bullet)
                self.main_body_last_shot = current_time
                
                # Play sound for main body shot
                if sound_manager:
                    sound_manager.play_sound('enemy_shoot', volume_override=0.5)
        
        return bullets
        
    def take_turret_damage(self, turret_index, damage=1):
        """Damage a specific turret"""
        if turret_index < 0 or turret_index >= len(self.turrets):
            return False
            
        turret = self.turrets[turret_index]
        if turret['destroyed']:
            return False
            
        turret['health'] -= damage
        
        if turret['health'] <= 0:
            turret['destroyed'] = True
            self.create_debris_effect(turret_index)
            return True  # Turret destroyed
            
        return False
        
    def take_main_damage(self, damage=1):
        """Damage the main body (only if all turrets destroyed)"""
        active_turrets = sum(1 for turret in self.turrets if not turret['destroyed'])
        if active_turrets > 0:
            return False  # Main body is protected
            
        self.health -= damage
        
        if self.health <= 0:
            self.start_destruction_sequence()
            return True  # Boss destroyed
            
        return False
        
    def create_debris_effect(self, turret_index):
        """Create debris when turret is destroyed"""
        turret_pos = self.get_turret_positions()[turret_index]
        
        for _ in range(8):
            debris = {
                'x': turret_pos[0] + random.randint(-20, 20),
                'y': turret_pos[1] + random.randint(-10, 10),
                'vel_x': random.uniform(-3, 3),
                'vel_y': random.uniform(-5, -1),
                'size': random.randint(3, 8),
                'color': random.choice([ORANGE, RED, YELLOW]),
                'life': random.randint(30, 60)
            }
            self.debris_effects.append(debris)
            
    def start_destruction_sequence(self):
        """Start the dramatic destruction sequence"""
        self.destruction_complete = True
        self.destruction_start_time = pygame.time.get_ticks()
        
        # Create multiple MASSIVE explosion effects 
        for _ in range(20):  # Even more explosions
            explosion = {
                'x': self.x + random.randint(-50, self.width + 50),  # Extend beyond UFO
                'y': self.y + random.randint(-30, self.height + 30),
                'radius': 0,
                'growth': random.uniform(6, 12),  # Much faster growth
                'color': random.choice([ORANGE, RED, YELLOW, WHITE, (255, 100, 0)]),
                'life': random.randint(80, 150),  # Longer lasting
                'max_radius': random.randint(60, 120)  # Different max sizes
            }
            self.explosion_effects.append(explosion)

    def create_final_explosion(self):
        """Create a massive particle explosion when boss is completely destroyed"""
        explosion_particles = []
        
        # Create TONS of particles across a huge area
        for _ in range(50):  # Way more particles
            particle = {
                'x': self.x + random.randint(-100, self.width + 100),  # Much wider spread
                'y': self.y + random.randint(-50, self.height + 50),
                'vel_x': random.uniform(-8, 8),  # Faster and wider spread
                'vel_y': random.uniform(-8, 3),
                'color': random.choice([
                    (255, 150, 0),   # Bright Orange
                    (255, 80, 80),   # Bright Red  
                    (255, 255, 100), # Bright Yellow
                    (255, 255, 255), # White
                    (100, 255, 255), # Bright Cyan
                    (255, 200, 0),   # Gold
                    (255, 0, 0),     # Pure Red
                ]),
                'size': random.randint(4, 12),  # Much bigger particles
                'life': random.randint(1000, 1800),  # Much longer lasting
                'gravity': random.uniform(0.1, 0.3)  # Variable gravity
            }
            explosion_particles.append(particle)
        
        return explosion_particles
            
    def is_destruction_complete(self):
        """Check if destruction sequence is finished"""
        if not self.destruction_complete:
            return False
        return pygame.time.get_ticks() - self.destruction_start_time > 2000  # 2 second sequence
        
    def get_turret_rects(self):
        """Get collision rectangles for each turret"""
        turret_positions = self.get_turret_positions()
        turret_size = 40
        rects = []
        
        for i, pos in enumerate(turret_positions):
            if not self.turrets[i]['destroyed']:
                rect = pygame.Rect(pos[0] - turret_size//2, pos[1] - turret_size//2, turret_size, turret_size)
                rects.append((rect, i))
            else:
                rects.append((None, i))
                
        return rects
        
    def get_main_body_rect(self):
        """Get collision rectangle for main body"""
        active_turrets = sum(1 for turret in self.turrets if not turret['destroyed'])
        if active_turrets > 0:
            return None  # Main body protected
        return self.rect
        
    def get_health_color(self):
        """Get UFO color based on health (white to red)"""
        if self.destruction_complete:
            return RED
            
        health_ratio = self.health / self.max_health
        # Interpolate from white (255,255,255) to red (255,0,0)
        red = 255
        green = int(255 * health_ratio)
        blue = int(255 * health_ratio)
        return (red, green, blue)
        
    def draw(self, screen):
        # DON'T draw the UFO if destruction is complete
        if self.destruction_complete:
            # Only draw explosion effects during destruction
            for explosion in self.explosion_effects:
                if explosion['radius'] > 0:
                    alpha = int(255 * (explosion['life'] / 150))
                    explosion_surface = pygame.Surface((explosion['radius']*2, explosion['radius']*2), pygame.SRCALPHA)
                    pygame.draw.circle(explosion_surface, explosion['color'], (explosion['radius'], explosion['radius']), explosion['radius'])
                    explosion_surface.set_alpha(alpha)
                    screen.blit(explosion_surface, (explosion['x'] - explosion['radius'], explosion['y'] - explosion['radius']))
            return  # Don't draw anything else
            
        if self.is_destruction_complete():
            return  # Don't draw if destruction is complete
            
        # Get UFO color based on health
        ufo_color = self.get_health_color()
        
        # IMPROVED PIXEL ART UFO DESIGN
        
        # 1. MAIN HULL - Detailed segmented design
        hull_segments = 8
        segment_width = self.width // hull_segments
        hull_y = self.y + int(self.height * 0.4)
        hull_height = int(self.height * 0.4)
        
        # Draw hull segments with alternating colors for detail
        for i in range(hull_segments):
            segment_x = self.x + i * segment_width
            # Alternate between main color and slightly darker
            if i % 2 == 0:
                color = ufo_color
            else:
                color = (max(0, ufo_color[0] - 30), max(0, ufo_color[1] - 30), max(0, ufo_color[2] - 30))
            
            pygame.draw.rect(screen, color, (segment_x, hull_y, segment_width, hull_height))
            
        # Hull outline
        pygame.draw.rect(screen, (100, 100, 100), (self.x, hull_y, self.width, hull_height), 3)
        
        # 2. UPPER DOME - Multi-layered with details
        dome_width = int(self.width * 0.6)
        dome_height = int(self.height * 0.5)
        dome_x = self.x + (self.width - dome_width) // 2
        dome_y = self.y
        
        # Outer dome layer
        pygame.draw.ellipse(screen, (80, 150, 200), (dome_x - 10, dome_y - 5, dome_width + 20, dome_height + 10))
        # Main dome
        pygame.draw.ellipse(screen, (120, 200, 255), (dome_x, dome_y, dome_width, dome_height))
        # Inner dome highlight
        pygame.draw.ellipse(screen, (180, 220, 255), (dome_x + 20, dome_y + 10, dome_width - 40, dome_height - 20))
        # Dome outline
        pygame.draw.ellipse(screen, WHITE, (dome_x, dome_y, dome_width, dome_height), 2)
        
        # 3. COMMAND BRIDGE/COCKPIT in center of dome
        bridge_width = dome_width // 3
        bridge_height = dome_height // 2
        bridge_x = dome_x + (dome_width - bridge_width) // 2
        bridge_y = dome_y + dome_height // 4
        
        pygame.draw.ellipse(screen, (50, 50, 50), (bridge_x, bridge_y, bridge_width, bridge_height))
        pygame.draw.ellipse(screen, (150, 150, 150), (bridge_x + 5, bridge_y + 3, bridge_width - 10, bridge_height - 6))
        pygame.draw.ellipse(screen, WHITE, (bridge_x, bridge_y, bridge_width, bridge_height), 2)
        
        # 4. DETAILED HULL PANELS
        panel_width = self.width // 6
        panel_height = hull_height // 2
        panel_y = hull_y + panel_height // 2
        
        for i in range(0, 6):
            panel_x = self.x + i * panel_width + panel_width // 4
            # Hull panels with rivets/details
            pygame.draw.rect(screen, (max(0, ufo_color[0] - 20), max(0, ufo_color[1] - 20), max(0, ufo_color[2] - 20)), 
                           (panel_x, panel_y, panel_width // 2, panel_height))
            pygame.draw.rect(screen, GRAY, (panel_x, panel_y, panel_width // 2, panel_height), 1)
            
            # Rivets/bolts on panels
            pygame.draw.circle(screen, (80, 80, 80), (panel_x + 8, panel_y + 8), 3)
            pygame.draw.circle(screen, (80, 80, 80), (panel_x + panel_width//2 - 8, panel_y + panel_height - 8), 3)
        
        # 5. ENHANCED LIGHTING SYSTEM
        light_count = 12
        for i in range(light_count):
            angle = (i / light_count) * 2 * math.pi
            light_x = self.x + self.width // 2 + int(math.cos(angle) * (self.width // 2 - 15))
            light_y = hull_y + hull_height // 2 + int(math.sin(angle) * 20)
            
            # Animated pulse based on time and position
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.008 + i * 0.5)) * 0.6 + 0.4
            
            # Different colored lights around the perimeter
            if i % 3 == 0:
                light_color = (int(255 * pulse), int(100 * pulse), 0)  # Orange
            elif i % 3 == 1:
                light_color = (0, int(255 * pulse), int(100 * pulse))  # Cyan
            else:
                light_color = (int(255 * pulse), int(255 * pulse), 0)  # Yellow
                
            pygame.draw.circle(screen, light_color, (light_x, light_y), 8)
            pygame.draw.circle(screen, WHITE, (light_x, light_y), 8, 2)
        
        # 6. IMPROVED TURRETS with more detail
        turret_positions = self.get_turret_positions()
        for i, (turret, pos) in enumerate(zip(self.turrets, turret_positions)):
            if not turret['destroyed']:
                # Turret base (larger)
                pygame.draw.circle(screen, (60, 60, 60), pos, 25)
                pygame.draw.circle(screen, DARK_GREEN, pos, 20)
                
                # Turret gun barrel
                barrel_length = 15
                barrel_angle = math.atan2(pos[1] - (self.y + self.height//2), pos[0] - (self.x + self.width//2))
                barrel_end_x = pos[0] + int(math.cos(barrel_angle) * barrel_length)
                barrel_end_y = pos[1] + int(math.sin(barrel_angle) * barrel_length)
                
                pygame.draw.line(screen, (40, 40, 40), pos, (barrel_end_x, barrel_end_y), 8)
                pygame.draw.line(screen, (80, 80, 80), pos, (barrel_end_x, barrel_end_y), 4)
                
                # Turret details
                pygame.draw.circle(screen, GREEN, pos, 15)
                pygame.draw.circle(screen, (0, 100, 0), pos, 10)
                pygame.draw.circle(screen, WHITE, pos, 20, 2)
                
                # Turret health indicator
                health_ratio = turret['health'] / turret['max_health']
                if health_ratio < 0.7:
                    damage_color = RED if health_ratio < 0.3 else ORANGE
                    pygame.draw.circle(screen, damage_color, pos, 22, 4)
                    
                    # Damage sparks/effects
                    if health_ratio < 0.5:
                        for _ in range(3):
                            spark_x = pos[0] + random.randint(-15, 15)
                            spark_y = pos[1] + random.randint(-15, 15)
                            pygame.draw.circle(screen, YELLOW, (spark_x, spark_y), 2)
        
        # 7. ENGINE GLOW/EXHAUST at bottom
        engine_count = 4
        engine_spacing = self.width // (engine_count + 1)
        engine_y = hull_y + hull_height
        
        for i in range(engine_count):
            engine_x = self.x + engine_spacing * (i + 1)
            
            # Engine glow effect
            glow_intensity = abs(math.sin(pygame.time.get_ticks() * 0.01 + i)) * 0.5 + 0.5
            engine_color = (int(100 * glow_intensity), int(150 * glow_intensity), int(255 * glow_intensity))
            
            # Multiple engine glow layers
            pygame.draw.circle(screen, engine_color, (engine_x, engine_y), 12)
            pygame.draw.circle(screen, (int(150 * glow_intensity), int(200 * glow_intensity), 255), (engine_x, engine_y), 8)
            pygame.draw.circle(screen, WHITE, (engine_x, engine_y), 4)
        
        # 8. ANTENNA/COMMUNICATION ARRAYS on dome
        antenna_count = 3
        for i in range(antenna_count):
            antenna_x = dome_x + (i + 1) * (dome_width // (antenna_count + 1))
            antenna_base_y = dome_y + dome_height // 3
            antenna_tip_y = dome_y - 10
            
            # Antenna structure
            pygame.draw.line(screen, GRAY, (antenna_x, antenna_base_y), (antenna_x, antenna_tip_y), 3)
            pygame.draw.circle(screen, RED, (antenna_x, antenna_tip_y), 4)  # Antenna tip
            pygame.draw.circle(screen, WHITE, (antenna_x, antenna_tip_y), 4, 1)
        
        # Draw debris effects
        for debris in self.debris_effects:
            alpha = int(255 * (debris['life'] / 60))
            debris_surface = pygame.Surface((debris['size']*2, debris['size']*2), pygame.SRCALPHA)
            color_with_alpha = (*debris['color'], alpha)
            pygame.draw.circle(debris_surface, color_with_alpha, (debris['size'], debris['size']), debris['size'])
            screen.blit(debris_surface, (debris['x'] - debris['size'], debris['y'] - debris['size']))
            
        # Draw explosion effects (for turret destruction)
        for explosion in self.explosion_effects:
            if explosion['radius'] > 0:
                alpha = int(255 * (explosion['life'] / 80))
                explosion_surface = pygame.Surface((explosion['radius']*2, explosion['radius']*2), pygame.SRCALPHA)
                pygame.draw.circle(explosion_surface, explosion['color'], (explosion['radius'], explosion['radius']), explosion['radius'])
                explosion_surface.set_alpha(alpha)
                screen.blit(explosion_surface, (explosion['x'] - explosion['radius'], explosion['y'] - explosion['radius']))
        
        # Health bars
        self.draw_health_bars(screen)
        
    def draw_health_bars(self, screen):
        """Draw health bars for turrets and main body"""
        # Main body health bar
        main_bar_width = self.width
        main_bar_height = 12
        main_bar_x = self.x
        main_bar_y = self.y - 30
        
        # Background
        pygame.draw.rect(screen, RED, (main_bar_x, main_bar_y, main_bar_width, main_bar_height))
        
        # Health
        health_ratio = self.health / self.max_health
        health_width = int(main_bar_width * health_ratio)
        health_color = self.get_health_color()
        pygame.draw.rect(screen, health_color, (main_bar_x, main_bar_y, health_width, main_bar_height))
        
        # Border
        pygame.draw.rect(screen, WHITE, (main_bar_x, main_bar_y, main_bar_width, main_bar_height), 2)
        
        # Health text
        font = pygame.font.Font(None, 36)
        health_text = font.render(f"UFO: {self.health}/{self.max_health}", True, WHITE)
        text_rect = health_text.get_rect(center=(self.x + self.width // 2, main_bar_y - 20))
        screen.blit(health_text, text_rect)
        
        # Turret health bars
        turret_positions = self.get_turret_positions()
        for i, (turret, pos) in enumerate(zip(self.turrets, turret_positions)):
            if not turret['destroyed']:
                bar_width = 60
                bar_height = 6
                bar_x = pos[0] - bar_width // 2
                bar_y = pos[1] - 35
                
                # Background
                pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
                
                # Health
                turret_health_ratio = turret['health'] / turret['max_health']
                turret_health_width = int(bar_width * turret_health_ratio)
                pygame.draw.rect(screen, GREEN, (bar_x, bar_y, turret_health_width, bar_height))
                
                # Border
                pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1) 
       
class HighScoreManager:
    def __init__(self):
        self.single_scores = self.load_scores(SINGLE_SCORES_FILE)
        self.coop_scores = self.load_scores(COOP_SCORES_FILE)
        
    def load_scores(self, filename):
        """Load high scores from file"""
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def save_scores(self, filename, scores):
        """Save high scores to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(scores, f, indent=2)
        except:
            pass
    
    def add_score(self, name, score, level, is_coop=False):
        """Add a new score to the appropriate list"""
        score_data = {
            'name': name,
            'score': score,
            'level': level,
            'date': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if is_coop:
            self.coop_scores.append(score_data)
            self.coop_scores.sort(key=lambda x: x['score'], reverse=True)
            self.coop_scores = self.coop_scores[:10]
            self.save_scores(COOP_SCORES_FILE, self.coop_scores)
        else:
            self.single_scores.append(score_data)
            self.single_scores.sort(key=lambda x: x['score'], reverse=True)
            self.single_scores = self.single_scores[:10]
            self.save_scores(SINGLE_SCORES_FILE, self.single_scores)
    
    def is_high_score(self, score, is_coop=False):
        """Check if score qualifies for high score list"""
        scores = self.coop_scores if is_coop else self.single_scores
        return len(scores) < 10 or score > scores[-1]['score']
    
    def get_best_score(self, is_coop=False):
        """Get the best score for display"""
        scores = self.coop_scores if is_coop else self.single_scores
        return scores[0] if scores else None

class NameInputScreen:
    def __init__(self, screen, score, level, is_coop=False):
        self.screen = screen
        self.score = score
        self.level = level
        self.is_coop = is_coop
        self.font_large = pygame.font.Font(None, 96)
        self.font_medium = pygame.font.Font(None, 64)
        self.font_small = pygame.font.Font(None, 48)
        
        # Name input system
        self.name = ["A", "A", "A"]
        self.current_position = 0
        self.alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
        self.current_letter_index = [0, 0, 0]
        self.input_mode = "controller"
        self.keyboard_name = ""
        self.finished = False
        self.ok_selected = False
        
        # Detect input method
        self.controllers = []
        for i in range(pygame.joystick.get_count()):
            controller = pygame.joystick.Joystick(i)
            controller.init()
            self.controllers.append(controller)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                self.input_mode = "keyboard"
                if event.key == pygame.K_RETURN:
                    if self.keyboard_name.strip():
                        return self.keyboard_name.strip()[:10]
                    return "PLAYER"
                elif event.key == pygame.K_BACKSPACE:
                    self.keyboard_name = self.keyboard_name[:-1]
                elif event.key == pygame.K_ESCAPE:
                    return "PLAYER"
                elif len(self.keyboard_name) < 10 and event.unicode.isprintable():
                    self.keyboard_name += event.unicode.upper()
            
            elif event.type == pygame.JOYBUTTONDOWN:
                self.input_mode = "controller"
                if event.button == 0:  # A button
                    if self.ok_selected:
                        return "".join(self.name)
                    else:
                        if self.current_position < 2:
                            self.current_position += 1
                        else:
                            self.ok_selected = True
                elif event.button == 1:  # B button
                    if self.ok_selected:
                        self.ok_selected = False
                        self.current_position = 2
                    elif self.current_position > 0:
                        self.current_position -= 1
            
            elif event.type == pygame.JOYHATMOTION:
                self.input_mode = "controller"
                if event.value[1] == 1:  # Up
                    if not self.ok_selected:
                        self.current_letter_index[self.current_position] = (
                            self.current_letter_index[self.current_position] - 1
                        ) % len(self.alphabet)
                        self.name[self.current_position] = self.alphabet[self.current_letter_index[self.current_position]]
                elif event.value[1] == -1:  # Down
                    if not self.ok_selected:
                        self.current_letter_index[self.current_position] = (
                            self.current_letter_index[self.current_position] + 1
                        ) % len(self.alphabet)
                        self.name[self.current_position] = self.alphabet[self.current_letter_index[self.current_position]]
                elif event.value[0] == -1:  # Left
                    if self.ok_selected:
                        self.ok_selected = False
                        self.current_position = 2
                    elif self.current_position > 0:
                        self.current_position -= 1
                elif event.value[0] == 1:  # Right
                    if self.current_position < 2:
                        self.current_position += 1
                    else:
                        self.ok_selected = True
                        
        return None
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Title
        title_text = self.font_large.render("NEW HIGH SCORE!", True, YELLOW)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title_text, title_rect)
        
        # Mode indicator
        mode_text = self.font_medium.render(f"{'CO-OP' if self.is_coop else 'SINGLE PLAYER'} MODE", True, CYAN)
        mode_rect = mode_text.get_rect(center=(SCREEN_WIDTH // 2, 270))
        self.screen.blit(mode_text, mode_rect)
        
        # Score info
        score_text = self.font_medium.render(f"Score: {self.score:,}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        self.screen.blit(score_text, score_rect)
        
        level_text = self.font_medium.render(f"Level: {self.level}", True, WHITE)
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, 410))
        self.screen.blit(level_text, level_rect)
        
        # Input method indicator
        if self.input_mode == "keyboard":
            prompt_text = self.font_medium.render("Enter your name:", True, WHITE)
            prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, 550))
            self.screen.blit(prompt_text, prompt_rect)
            
            name_display = self.keyboard_name + "_" if len(self.keyboard_name) < 10 else self.keyboard_name
            name_text = self.font_large.render(name_display, True, CYAN)
            name_rect = name_text.get_rect(center=(SCREEN_WIDTH // 2, 650))
            
            box_rect = name_rect.inflate(40, 20)
            pygame.draw.rect(self.screen, WHITE, box_rect, 3)
            self.screen.blit(name_text, name_rect)
            
            inst_text = self.font_small.render("Type your name and press ENTER", True, GRAY)
            inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, 770))
            self.screen.blit(inst_text, inst_rect)
            
        else:
            prompt_text = self.font_medium.render("Enter your name:", True, WHITE)
            prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, 550))
            self.screen.blit(prompt_text, prompt_rect)
            
            letter_spacing = 120
            start_x = SCREEN_WIDTH // 2 - letter_spacing
            
            for i, letter in enumerate(self.name):
                x = start_x + i * letter_spacing
                color = YELLOW if i == self.current_position and not self.ok_selected else WHITE
                
                if i == self.current_position and not self.ok_selected:
                    box_rect = pygame.Rect(x - 40, 630, 80, 80)
                    pygame.draw.rect(self.screen, YELLOW, box_rect, 3)
                
                letter_text = self.font_large.render(letter, True, color)
                letter_rect = letter_text.get_rect(center=(x, 670))
                self.screen.blit(letter_text, letter_rect)
            
            ok_color = YELLOW if self.ok_selected else WHITE
            ok_text = self.font_medium.render("OK", True, ok_color)
            ok_rect = ok_text.get_rect(center=(SCREEN_WIDTH // 2, 800))
            
            if self.ok_selected:
                box_rect = ok_rect.inflate(40, 20)
                pygame.draw.rect(self.screen, YELLOW, box_rect, 3)
            
            self.screen.blit(ok_text, ok_rect)
            
            instructions = [
                "D-pad Up/Down: Change letter",
                "D-pad Left/Right: Move cursor",
                "A button: Confirm/Next",
                "B button: Go back"
            ]
            
            for i, inst in enumerate(instructions):
                inst_text = self.font_small.render(inst, True, GRAY)
                inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, 900 + i * 30))
                self.screen.blit(inst_text, inst_rect)
        
        pygame.display.flip()

class HighScoreScreen:
    def __init__(self, screen, score_manager, sound_manager):
        self.screen = screen
        self.score_manager = score_manager
        self.sound_manager = sound_manager
        self.font_large = pygame.font.Font(None, 96)
        self.font_medium = pygame.font.Font(None, 64)
        self.font_small = pygame.font.Font(None, 48)
        self.viewing_coop = False
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    self.sound_manager.play_sound('menu_select')
                    return "back"
                elif event.key == pygame.K_TAB or event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    self.sound_manager.play_sound('menu_change')
                    self.viewing_coop = not self.viewing_coop
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0 or event.button == 1:  # A or B button
                    self.sound_manager.play_sound('menu_select')
                    return "back"
            elif event.type == pygame.JOYHATMOTION:
                if event.value[0] != 0:  # Left or Right
                    self.sound_manager.play_sound('menu_change')
                    self.viewing_coop = not self.viewing_coop
        return None
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Title
        mode_text = "CO-OP" if self.viewing_coop else "SINGLE PLAYER"
        title_text = self.font_large.render(f"{mode_text} HIGH SCORES", True, YELLOW)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title_text, title_rect)
        
        # Mode toggle instruction
        toggle_text = self.font_small.render("Press TAB or Left/Right to switch modes", True, CYAN)
        toggle_rect = toggle_text.get_rect(center=(SCREEN_WIDTH // 2, 180))
        self.screen.blit(toggle_text, toggle_rect)
        
        # Headers
        rank_header = self.font_medium.render("RANK", True, WHITE)
        name_header = self.font_medium.render("NAME", True, WHITE)
        score_header = self.font_medium.render("SCORE", True, WHITE)
        level_header = self.font_medium.render("LEVEL", True, WHITE)
        date_header = self.font_medium.render("DATE", True, WHITE)
        
        header_y = 250
        self.screen.blit(rank_header, (200, header_y))
        self.screen.blit(name_header, (400, header_y))
        self.screen.blit(score_header, (700, header_y))
        self.screen.blit(level_header, (1000, header_y))
        self.screen.blit(date_header, (1300, header_y))
        
        pygame.draw.line(self.screen, WHITE, (150, header_y + 60), (SCREEN_WIDTH - 150, header_y + 60), 2)
        
        # High scores list
        scores = self.score_manager.coop_scores if self.viewing_coop else self.score_manager.single_scores
        start_y = 350
        for i, score_entry in enumerate(scores):
            y = start_y + i * 60
            
            if i % 2 == 1:
                row_rect = pygame.Rect(150, y - 10, SCREEN_WIDTH - 300, 50)
                pygame.draw.rect(self.screen, (20, 20, 20), row_rect)
            
            rank_text = self.font_small.render(f"{i + 1}.", True, YELLOW if i < 3 else WHITE)
            self.screen.blit(rank_text, (200, y))
            
            name_text = self.font_small.render(score_entry['name'], True, WHITE)
            self.screen.blit(name_text, (400, y))
            
            score_text = self.font_small.render(f"{score_entry['score']:,}", True, WHITE)
            self.screen.blit(score_text, (700, y))
            
            level_text = self.font_small.render(f"{score_entry['level']}", True, WHITE)
            self.screen.blit(level_text, (1000, y))
            
            date_text = self.font_small.render(score_entry['date'][:10], True, GRAY)
            self.screen.blit(date_text, (1300, y))
        
        if not scores:
            no_scores_text = self.font_medium.render(f"No {mode_text.lower()} high scores yet!", True, GRAY)
            no_scores_rect = no_scores_text.get_rect(center=(SCREEN_WIDTH // 2, 500))
            self.screen.blit(no_scores_text, no_scores_rect)
        
        instruction_text = self.font_small.render("Press ESC, ENTER, or controller button to return", True, GRAY)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        self.screen.blit(instruction_text, instruction_rect)
        
        pygame.display.flip()
        
class Player:
    def __init__(self, x, y, player_id=1, controller=None, upgrades=None):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 45
        self.base_speed = BASE_PLAYER_SPEED
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.last_shot_time = 0
        self.invincible = False
        self.invincible_end_time = 0
        self.rapid_fire = False
        self.rapid_fire_ammo = 0
        self.has_laser = False
        self.has_multi_shot = False
        self.multi_shot_ammo = 0
        self.active_ammo_powerup = None
        self.ammo_powerup_queue = []
        self.afterimage_positions = []
        self.last_afterimage_time = 0
        self.player_id = player_id
        self.controller = controller
        self.color = GREEN if player_id == 1 else BLUE
        self.lives = 3
        self.respawn_immunity = False
        self.respawn_immunity_end_time = 0
        self.is_alive = True
        self.upgrades = upgrades or PlayerUpgrades()

        # Boss reward shield
        self.boss_shield_active = False
        self.boss_shield_flash_time = 0
        
        # ADDED: Level up indicator
        self.level_up_indicator = False
        self.level_up_indicator_time = 0
        
    def show_level_up_indicator(self):
        """Show level up indicator at player"""
        self.level_up_indicator = True
        self.level_up_indicator_time = pygame.time.get_ticks()

    def clear_ammo_power_ups(self):
        self.rapid_fire = False
        self.rapid_fire_ammo = 0
        self.has_multi_shot = False
        self.multi_shot_ammo = 0
        self.active_ammo_powerup = None
        self.ammo_powerup_queue = []

    def set_active_ammo_powerup(self, power_type, ammo_count):
        self.rapid_fire = False
        self.has_multi_shot = False
        self.active_ammo_powerup = {'type': power_type, 'ammo': ammo_count}

        if power_type == 'rapid_fire':
            self.rapid_fire = True
            self.rapid_fire_ammo = ammo_count
        elif power_type == 'multi_shot':
            self.has_multi_shot = True
            self.multi_shot_ammo = ammo_count

    def add_ammo_power_up(self, power_type, ammo_count):
        capacity = self.upgrades.get_ammo_powerup_capacity()
        if capacity <= 1:
            self.clear_ammo_power_ups()
            self.set_active_ammo_powerup(power_type, ammo_count)
            return

        if not self.active_ammo_powerup:
            self.set_active_ammo_powerup(power_type, ammo_count)
            return

        total_slots = 1 + len(self.ammo_powerup_queue)
        new_power = {'type': power_type, 'ammo': ammo_count}

        if total_slots >= capacity:
            if self.ammo_powerup_queue:
                self.ammo_powerup_queue[-1] = new_power
        else:
            self.ammo_powerup_queue.append(new_power)
        
    def get_speed(self):
        """Get current movement speed with upgrades"""
        return self.base_speed * self.upgrades.get_multiplier('movement_speed')
        
    def get_bullet_speed(self):
        """Get current bullet speed with upgrades"""
        return BASE_BULLET_SPEED * self.upgrades.get_multiplier('shot_speed')
        
    def get_shoot_cooldown(self):
        """Get current shoot cooldown with upgrades"""
        base_cooldown = RAPID_FIRE_COOLDOWN if self.rapid_fire else BASE_SHOOT_COOLDOWN
        return base_cooldown / self.upgrades.get_multiplier('fire_rate')
        
    def get_powerup_duration_multiplier(self):
        """Get power-up duration multiplier"""
        return self.upgrades.get_multiplier('powerup_duration')
        
    def reset_position(self):
        """Reset player to center of screen"""
        if self.player_id == 1:
            self.x = SCREEN_WIDTH // 2 - 90 if hasattr(self, 'coop_mode') and self.coop_mode else SCREEN_WIDTH // 2 - 30
        else:
            self.x = SCREEN_WIDTH // 2 + 30
        self.y = SCREEN_HEIGHT - 80
        self.rect.x = self.x
        self.rect.y = self.y
        
    def respawn(self):
        """Respawn player with immunity"""
        self.is_alive = True
        self.reset_position()
        self.respawn_immunity = True
        self.respawn_immunity_end_time = pygame.time.get_ticks() + RESPAWN_IMMUNITY_DURATION
        self.clear_all_power_ups()

    def activate_boss_shield(self):
        """Grant a one-hit shield after defeating a boss"""
        self.boss_shield_active = True
        self.boss_shield_flash_time = pygame.time.get_ticks()

    def clear_boss_shield(self):
        """Remove boss shield (e.g., at the start of a boss fight or when consumed)"""
        self.boss_shield_active = False
        
    def take_damage(self, sound_manager=None):
        """Player takes damage"""
        if self.respawn_immunity or self.invincible:
            return False

        if self.boss_shield_active:
            self.clear_boss_shield()
            if sound_manager:
                sound_manager.play_sound('explosion_small', volume_override=0.5)
            return True

        # Play player explosion sound
        if sound_manager:
            sound_manager.play_sound('player_explosion', volume_override=0.8)

        self.lives -= 1
        if self.lives <= 0:
            self.is_alive = False
        else:
            self.respawn()
        return True
        
    def move_left(self):
        if not self.is_alive:
            return
        if self.x > 0:
            self.x -= self.get_speed()
            self.rect.x = self.x
            self.update_afterimage()
            
    def move_right(self):
        if not self.is_alive:
            return
        if self.x < SCREEN_WIDTH - self.width:
            self.x += self.get_speed()
            self.rect.x = self.x
            self.update_afterimage()
            
    def update_afterimage(self):
        if self.invincible:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_afterimage_time >= AFTERIMAGE_INTERVAL:
                self.afterimage_positions.append((self.x, self.y, current_time))
                self.last_afterimage_time = current_time
                
            self.afterimage_positions = [(x, y, t) for x, y, t in self.afterimage_positions 
                                       if current_time - t < 500]
            
    def can_shoot(self):
        if not self.is_alive:
            return False
        current_time = pygame.time.get_ticks()
        cooldown = self.get_shoot_cooldown()
        return current_time - self.last_shot_time >= cooldown
        
    def shoot(self, sound_manager=None):
        if not self.can_shoot():
            return []

        self.last_shot_time = pygame.time.get_ticks()
        bullets = []
        bullet_speed = -self.get_bullet_speed()
        pierce_hits = self.upgrades.get_pierce_hits()
        length_multiplier = self.upgrades.get_bullet_length_multiplier()
        can_phase_barriers = self.upgrades.can_phase_barriers()
        boss_damage_multiplier = self.upgrades.get_boss_damage_multiplier()
        bullet_kwargs = {
            'owner_id': self.player_id,
            'pierce_hits': pierce_hits,
            'length_multiplier': length_multiplier,
            'can_phase_barriers': can_phase_barriers,
            'boss_damage_multiplier': boss_damage_multiplier
        }
        base_x = self.x + self.width // 2

        if self.has_laser:
            # Pass the duration multiplier to the laser
            laser = LaserBeam(self.x + self.width // 2, self.player_id, self.get_powerup_duration_multiplier())
            bullets.append(('laser', laser))
            self.has_laser = False
            # Play laser sound
            if sound_manager:
                sound_manager.play_sound('laser')
        elif self.has_multi_shot and self.multi_shot_ammo > 0:
            offsets = [-25, 0, 25]
            if self.upgrades.has_extra_bullet():
                offsets = [-25, -8, 8, 25]
            for offset in offsets:
                bullets.append(('bullet', Bullet(base_x + offset, self.y, bullet_speed, **bullet_kwargs)))
            self.multi_shot_ammo -= 1
            if self.multi_shot_ammo <= 0:
                self.has_multi_shot = False
            # Play shoot sound at lower volume for multi-shot to avoid amplification
            if sound_manager:
                sound_manager.play_shoot_sound(volume_override=0.4)
        elif self.rapid_fire and self.rapid_fire_ammo > 0:
            offsets = [0]
            if self.upgrades.has_extra_bullet():
                offsets = [-12, 12]
            for offset in offsets:
                bullets.append(('bullet', Bullet(base_x + offset, self.y, bullet_speed, **bullet_kwargs)))
            self.rapid_fire_ammo -= 1
            if self.rapid_fire_ammo <= 0:
                self.rapid_fire = False
            # Use smart sound management for rapid fire
            if sound_manager:
                sound_manager.play_shoot_sound(volume_override=0.6)
        else:
            offsets = [0]
            if self.upgrades.has_extra_bullet():
                offsets = [-12, 12]
            for offset in offsets:
                bullets.append(('bullet', Bullet(base_x + offset, self.y, bullet_speed, **bullet_kwargs)))
            # Play shoot sound for normal shot
            if sound_manager:
                sound_manager.play_sound('shoot', force_play=True)  # Always play normal shots
            
        return bullets
        
    def update_power_ups(self):
        current_time = pygame.time.get_ticks()
        
        # Update respawn immunity
        if self.respawn_immunity and current_time >= self.respawn_immunity_end_time:
            self.respawn_immunity = False
        
        if self.invincible and current_time >= self.invincible_end_time:
            self.invincible = False
            self.afterimage_positions = []
            
        # Ammo-based powerups
        if self.rapid_fire_ammo <= 0:
            self.rapid_fire = False
            
        if self.multi_shot_ammo <= 0:
            self.has_multi_shot = False

        if self.active_ammo_powerup:
            if self.active_ammo_powerup['type'] == 'rapid_fire' and self.rapid_fire_ammo <= 0:
                self.active_ammo_powerup = None
            elif self.active_ammo_powerup['type'] == 'multi_shot' and self.multi_shot_ammo <= 0:
                self.active_ammo_powerup = None

        if not self.active_ammo_powerup and self.ammo_powerup_queue:
            next_power = self.ammo_powerup_queue.pop(0)
            self.set_active_ammo_powerup(next_power['type'], next_power['ammo'])
            
    def clear_all_power_ups(self):
        self.clear_ammo_power_ups()
        self.has_laser = False
        
    def activate_invincibility(self):
        self.invincible = True
        duration = BASE_POWERUP_DURATION * self.get_powerup_duration_multiplier()
        self.invincible_end_time = pygame.time.get_ticks() + duration
        
    def activate_rapid_fire(self):
        # Apply powerup duration multiplier to ammo count
        base_ammo = 200
        ammo_count = int(base_ammo * self.get_powerup_duration_multiplier())
        self.add_ammo_power_up('rapid_fire', ammo_count)
        
    def activate_laser(self):
        self.clear_all_power_ups()
        self.has_laser = True
        # Note: Laser duration is handled in LaserBeam class, we need to pass the multiplier
        
    def activate_multi_shot(self):
        # Apply powerup duration multiplier to ammo count
        base_ammo = 100
        ammo_count = int(base_ammo * self.get_powerup_duration_multiplier())
        self.add_ammo_power_up('multi_shot', ammo_count)
        
    def handle_controller_input(self):
        if not self.is_alive:
            return
        if self.controller:
            hat = self.controller.get_hat(0) if self.controller.get_numhats() > 0 else (0, 0)
            axis_x = self.controller.get_axis(0) if self.controller.get_numaxes() > 0 else 0
            
            if hat[0] == -1 or axis_x < -0.3:
                self.move_left()
            elif hat[0] == 1 or axis_x > 0.3:
                self.move_right()
                
    def draw(self, screen):
        if not self.is_alive:
            return
            
        # Draw afterimages if invincible
        if self.invincible:
            current_time = pygame.time.get_ticks()
            for i, (x, y, timestamp) in enumerate(self.afterimage_positions):
                age = current_time - timestamp
                alpha = max(0, 255 - (age * 255 // 500))
                
                afterimage_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                points = [
                    (self.width // 2, 0),
                    (0, self.height),
                    (self.width // 4, self.height - 15),
                    (3 * self.width // 4, self.height - 15),
                    (self.width, self.height)
                ]
                pygame.draw.polygon(afterimage_surface, (*PURPLE, alpha), points)
                screen.blit(afterimage_surface, (x, y))
        
        # ADDED: Draw level up indicator
        if self.level_up_indicator:
            current_time = pygame.time.get_ticks()
            if current_time - self.level_up_indicator_time < 3000:  # Show for 3 seconds
                # Pulsing "LEVEL UP!" text above player
                pulse = abs(math.sin(current_time * 0.01)) * 50 + 50
                font = pygame.font.Font(None, 48)
                level_up_text = font.render("LEVEL UP!", True, (255, 255, int(pulse)))
                text_rect = level_up_text.get_rect(center=(self.x + self.width // 2, self.y - 30))
                screen.blit(level_up_text, text_rect)
                
                # Glowing ring around player
                ring_alpha = int(pulse)
                ring_surface = pygame.Surface((self.width + 40, self.height + 40), pygame.SRCALPHA)
                pygame.draw.circle(ring_surface, (255, 255, 0, ring_alpha), 
                                 (self.width // 2 + 20, self.height // 2 + 20), 
                                 self.width // 2 + 20, 3)
                screen.blit(ring_surface, (self.x - 20, self.y - 20))
            else:
                self.level_up_indicator = False

        # Boss shield visual
        if self.boss_shield_active:
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.01))
            ring_alpha = int(130 + 100 * pulse)
            steady_alpha = 140

            # Slightly larger surface and centered circle to avoid clipping at the top
            shield_surface = pygame.Surface((self.width + 70, self.height + 70), pygame.SRCALPHA)
            center = (shield_surface.get_width() // 2, shield_surface.get_height() // 2)
            radius = max(self.width, self.height) // 2 + 30

            # Steady outline
            pygame.draw.circle(shield_surface, (120, 200, 255, steady_alpha), center, radius, 2)
            # Flashing outline
            pygame.draw.circle(shield_surface, (80, 170, 255, ring_alpha), center, radius + 2, 6)
            screen.blit(shield_surface, (self.x - 35, self.y - 35))
        
        # Draw player
        points = [
            (self.x + self.width // 2, self.y),
            (self.x, self.y + self.height),
            (self.x + self.width // 4, self.y + self.height - 15),
            (self.x + 3 * self.width // 4, self.y + self.height - 15),
            (self.x + self.width, self.y + self.height)
        ]
        color = self.color
        
        # Flashing effects
        flash_interval = 100
        current_time = pygame.time.get_ticks()
        
        if self.invincible and (current_time // flash_interval) % 2:
            color = PURPLE
        elif self.respawn_immunity and (current_time // flash_interval) % 2:
            color = WHITE
            
        pygame.draw.polygon(screen, color, points)

class AlienOverlordBoss:
    def __init__(self, level):
        self.encounter = max(1, level // 5)
        self.width = SCREEN_WIDTH // 4
        self.height = int(self.width * 1.3)
        self.head_height = int(self.height * 0.55)
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = 120
        self.rect = pygame.Rect(self.x, self.y, self.width, self.head_height)

        self.max_health = ALIEN_BOSS_HEAD_HEALTH_BASE + (self.encounter - 1) * ALIEN_BOSS_HEAD_HEALTH_PER_LEVEL
        self.health = self.max_health
        self.max_hand_health = ALIEN_BOSS_HAND_HEALTH_BASE + (self.encounter - 1) * ALIEN_BOSS_HAND_HEALTH_PER_LEVEL

        self.hand_speed = ALIEN_BOSS_HAND_SPEED_BASE + (self.encounter - 1) * ALIEN_BOSS_HAND_SPEED_GROWTH
        self.hand_drop_cooldown = int(ALIEN_BOSS_DROP_COOLDOWN_BASE * (ALIEN_BOSS_DROP_COOLDOWN_SCALE ** (self.encounter - 1)))
        self.fireball_cooldown = int(ALIEN_BOSS_FIREBALL_COOLDOWN_BASE * (ALIEN_BOSS_FIREBALL_COOLDOWN_SCALE ** (self.encounter - 1)))
        self.fireball_speed = 6 + self.encounter

        self.last_fireball = pygame.time.get_ticks() - random.randint(0, 1000)

        self.direction = random.choice([-1, 1])
        self.head_speed = 1.5 + (self.encounter - 1) * 0.25

        self.destruction_complete = False
        self.destruction_start_time = 0
        self.explosion_effects = []

        hand_width = 90
        hand_height = 110
        offsets = [-self.width // 2 - 120, self.width // 2 + 120]
        base_y = self.y + self.head_height - hand_height // 2
        current_time = pygame.time.get_ticks()
        self.hands = []
        for offset in offsets:
            hand_x = self.x + self.width // 2 + offset - hand_width // 2
            hand = {
                'x': float(hand_x),
                'y': float(base_y),
                'width': hand_width,
                'height': hand_height,
                'health': self.max_hand_health,
                'max_health': self.max_hand_health,
                'state': 'idle',
                'target_x': hand_x,
                'last_drop': current_time + random.randint(-800, 0),
                'drop_cooldown': self.hand_drop_cooldown + random.randint(-600, 600),
                'rect': pygame.Rect(hand_x, base_y, hand_width, hand_height),
                'home_offset': offset,
                'destroyed': False
            }
            self.hands.append(hand)

    def is_destruction_complete(self):
        if not self.destruction_complete:
            return False
        return pygame.time.get_ticks() - self.destruction_start_time > 2000

    def create_final_explosion(self):
        explosion_particles = []
        for _ in range(60):
            particle = {
                'x': self.x + random.randint(-100, self.width + 100),
                'y': self.y + random.randint(-50, self.height + 50),
                'vel_x': random.uniform(-8, 8),
                'vel_y': random.uniform(-8, 3),
                'color': random.choice([(255, 150, 0), (255, 80, 80), (255, 255, 100), (255, 255, 255)]),
                'size': random.randint(4, 12),
                'life': random.randint(1000, 1800),
                'gravity': random.uniform(0.1, 0.3)
            }
            explosion_particles.append(particle)
        return explosion_particles

    def get_turret_rects(self):
        rects = []
        for index, hand in enumerate(self.hands):
            if hand['destroyed']:
                rects.append((None, index))
            else:
                rects.append((hand['rect'], index))
        return rects

    def get_main_body_rect(self):
        if any(not hand['destroyed'] for hand in self.hands):
            return None
        return self.rect

    def take_turret_damage(self, hand_index, damage=1):
        if hand_index < 0 or hand_index >= len(self.hands):
            return False
        hand = self.hands[hand_index]
        if hand['destroyed']:
            return False
        hand['health'] -= damage
        if hand['health'] <= 0:
            hand['health'] = 0
            hand['destroyed'] = True
            hand['state'] = 'destroyed'
            hand['rect'] = None
            return True
        return False

    def take_main_damage(self, damage=1):
        if any(not hand['destroyed'] for hand in self.hands):
            return False
        self.health -= damage
        if self.health <= 0 and not self.destruction_complete:
            self.health = 0
            self.destruction_complete = True
            self.destruction_start_time = pygame.time.get_ticks()
            for _ in range(8):
                explosion = {
                    'x': self.x + random.randint(0, self.width),
                    'y': self.y + random.randint(0, self.head_height),
                    'radius': 10,
                    'growth': random.uniform(4, 8),
                    'color': random.choice([ORANGE, RED, YELLOW, WHITE]),
                    'life': random.randint(80, 150)
                }
                self.explosion_effects.append(explosion)
        return self.destruction_complete

    def _get_hand_home_position(self, hand):
        center_x = self.x + self.width // 2
        home_x = center_x + hand['home_offset'] - hand['width'] // 2
        home_y = self.y + self.head_height - hand['height'] // 2
        return home_x, home_y

    def _start_hand_attack(self, hand, players):
        alive_players = [p for p in players if p and p.is_alive]
        if not alive_players:
            return
        target_player = random.choice(alive_players)
        hand['target_x'] = target_player.x + target_player.width // 2 - hand['width'] // 2
        hand['state'] = 'seeking'
        hand['target_player'] = target_player
        player_mid_y = target_player.y + target_player.height // 2
        desired_drop_y = player_mid_y - hand['height']
        max_drop_y = SCREEN_HEIGHT - hand['height'] - 40
        min_drop_y = self.y + self.head_height // 2
        hand['drop_target_y'] = max(min(desired_drop_y, max_drop_y), min_drop_y)

    def _move_hand_toward(self, hand, target_x, target_y):
        dx = target_x - hand['x']
        dy = target_y - hand['y']
        distance = math.hypot(dx, dy)
        if distance < self.hand_speed or distance == 0:
            hand['x'] = target_x
            hand['y'] = target_y
            return True
        hand['x'] += (dx / distance) * self.hand_speed
        hand['y'] += (dy / distance) * self.hand_speed
        return False

    def _check_hand_player_collision(self, hand, players, sound_manager):
        if not players or hand['rect'] is None:
            return
        for player in players:
            if player and player.is_alive and hand['rect'].colliderect(player.rect):
                player.take_damage(sound_manager)
                hand['state'] = 'returning'
                break

    def update(self, players=None, sound_manager=None):
        if self.destruction_complete:
            self.explosion_effects = [exp for exp in self.explosion_effects if exp['life'] > 0]
            for explosion in self.explosion_effects:
                explosion['radius'] += explosion['growth']
                explosion['life'] -= 1
            return

        self.x += self.head_speed * self.direction
        if self.x <= 100 or self.x + self.width >= SCREEN_WIDTH - 100:
            self.direction *= -1
        self.rect.x = int(self.x)
        self.rect.y = self.y

        alive_players = [p for p in players if p and p.is_alive] if players else []
        current_time = pygame.time.get_ticks()

        for hand in self.hands:
            home_x, home_y = self._get_hand_home_position(hand)
            if hand['destroyed']:
                continue
            if hand['state'] == 'idle':
                self._move_hand_toward(hand, home_x, home_y)
                if alive_players and current_time - hand['last_drop'] >= hand['drop_cooldown']:
                    self._start_hand_attack(hand, alive_players)
            elif hand['state'] == 'seeking':
                target_x = max(0, min(SCREEN_WIDTH - hand['width'], hand['target_x']))
                self._move_hand_toward(hand, target_x, home_y)
                if abs(hand['x'] - target_x) < 2:
                    hand['state'] = 'dropping'
            elif hand['state'] == 'dropping':
                drop_target_y = hand.get('drop_target_y', SCREEN_HEIGHT - hand['height'] - 40)
                hand['y'] += self.hand_speed * 1.8
                if hand['y'] >= drop_target_y:
                    hand['y'] = drop_target_y
                    hand['state'] = 'returning'
                self._update_hand_rect(hand)
                self._check_hand_player_collision(hand, alive_players, sound_manager)
            elif hand['state'] == 'returning':
                reached = self._move_hand_toward(hand, home_x, home_y)
                if reached:
                    hand['state'] = 'idle'
                    hand['last_drop'] = current_time
            self._update_hand_rect(hand)

        for explosion in self.explosion_effects:
            explosion['radius'] += explosion['growth']
            explosion['life'] -= 1

    def _update_hand_rect(self, hand):
        if hand['destroyed']:
            hand['rect'] = None
        else:
            hand['rect'] = pygame.Rect(int(hand['x']), int(hand['y']), hand['width'], hand['height'])

    def shoot(self, players, sound_manager=None):
        if self.destruction_complete:
            return []
        alive_players = [p for p in players if p and p.is_alive]
        if not alive_players:
            return []
        current_time = pygame.time.get_ticks()
        if current_time - self.last_fireball < self.fireball_cooldown:
            return []
        head_center_x = self.x + self.width // 2
        head_center_y = self.y + self.head_height // 2
        closest_player = min(alive_players, key=lambda p: abs(p.x - head_center_x))
        target_x = closest_player.x + closest_player.width // 2
        target_y = closest_player.y
        self.last_fireball = current_time
        return [FireballProjectile(head_center_x, head_center_y, target_x, target_y, self.fireball_speed)]

    def draw(self, screen):
        if self.destruction_complete:
            for explosion in self.explosion_effects:
                if explosion['radius'] > 0:
                    alpha = int(255 * (explosion['life'] / 150))
                    explosion_surface = pygame.Surface((explosion['radius']*2, explosion['radius']*2), pygame.SRCALPHA)
                    pygame.draw.circle(explosion_surface, explosion['color'], (explosion['radius'], explosion['radius']), explosion['radius'])
                    explosion_surface.set_alpha(alpha)
                    screen.blit(explosion_surface, (explosion['x'] - explosion['radius'], explosion['y'] - explosion['radius']))
            return

        shield_active = any(not hand['destroyed'] for hand in self.hands)
        head_color = (200, max(50, int(200 * (self.health / self.max_health))), max(50, int(200 * (self.health / self.max_health))))
        head_rect = pygame.Rect(self.x, self.y, self.width, self.head_height)
        pygame.draw.ellipse(screen, head_color, head_rect)
        pygame.draw.ellipse(screen, WHITE, head_rect, 3)

        eye_width = self.width // 5
        eye_height = self.head_height // 4
        eye_y = self.y + self.head_height // 3
        left_eye = pygame.Rect(self.x + self.width // 4 - eye_width // 2, eye_y, eye_width, eye_height)
        right_eye = pygame.Rect(self.x + 3 * self.width // 4 - eye_width // 2, eye_y, eye_width, eye_height)
        pygame.draw.ellipse(screen, BLACK, left_eye)
        pygame.draw.ellipse(screen, BLACK, right_eye)
        pygame.draw.ellipse(screen, CYAN, left_eye.inflate(-10, -10))
        pygame.draw.ellipse(screen, CYAN, right_eye.inflate(-10, -10))

        mouth_rect = pygame.Rect(self.x + self.width // 3, self.y + int(self.head_height * 0.7), self.width // 3, self.head_height // 6)
        pygame.draw.rect(screen, BLACK, mouth_rect, border_radius=10)

        if shield_active:
            shield_surface = pygame.Surface((self.width + 80, self.head_height + 80), pygame.SRCALPHA)
            pygame.draw.ellipse(shield_surface, (0, 200, 255, 90), shield_surface.get_rect(), 8)
            screen.blit(shield_surface, (self.x - 40, self.y - 40))

        for hand in self.hands:
            if hand['destroyed']:
                continue
            rect = pygame.Rect(int(hand['x']), int(hand['y']), hand['width'], hand['height'])
            pygame.draw.rect(screen, DARK_GREEN, rect, border_radius=25)
            pygame.draw.rect(screen, GREEN, rect.inflate(-15, -15), border_radius=20)
            pygame.draw.circle(screen, BLACK, (rect.centerx, rect.centery), 12)
            self._draw_health_bar(screen, rect.centerx - 50, rect.top - 15, 100, 8, hand['health'] / hand['max_health'])

        self._draw_health_bar(screen, self.x, self.y - 30, self.width, 12, self.health / self.max_health, label='ALIEN CORE')

    def _draw_health_bar(self, screen, x, y, width, height, ratio, label=None):
        pygame.draw.rect(screen, RED, (x, y, width, height))
        pygame.draw.rect(screen, GREEN, (x, y, int(width * ratio), height))
        pygame.draw.rect(screen, WHITE, (x, y, width, height), 2)
        if label:
            font = pygame.font.Font(None, 32)
            text = font.render(f"{label}: {int(ratio * 100)}%", True, WHITE)
            text_rect = text.get_rect(center=(x + width // 2, y - 18))
            screen.blit(text, text_rect)


class Enemy:
    def __init__(self, x, y, enemy_type=0):
        self.x = x
        self.y = y
        self.width = 45
        self.height = 30
        self.base_speed = BASE_ENEMY_SPEED
        self.speed = BASE_ENEMY_SPEED
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.direction = 1
        self.enemy_type = enemy_type  # 0-4 for different rows
        
    def move(self):
        self.x += self.speed * self.direction
        self.rect.x = self.x
        
    def drop_down(self):
        self.y += ENEMY_DROP_SPEED
        self.rect.y = self.y
        self.direction *= -1
        
    def shoot(self, sound_manager=None):
        if random.randint(1, 1500) < 3:
            if sound_manager:
                sound_manager.play_sound('enemy_shoot', volume_override=0.3)  # Quieter than player
            return Bullet(self.x + self.width // 2, self.y + self.height, BASE_BULLET_SPEED)
        return None
    
    def draw_squid_enemy(self, screen):
        """Top row - Green squid-like alien (most points) - EVEN BIGGER VERSION"""
        # Main body (green) - expanded further
        body_color = (0, 200, 0)
        dark_green = (0, 150, 0)
        
        # Body outline - made bigger
        pygame.draw.rect(screen, body_color, (self.x + 3, self.y + 2, 39, 26))
        
        # Head bumps - bigger
        pygame.draw.rect(screen, body_color, (self.x - 2, self.y + 5, 12, 12))
        pygame.draw.rect(screen, body_color, (self.x + 35, self.y + 5, 12, 12))
        
        # Eyes (white with black pupils) - bigger
        pygame.draw.rect(screen, WHITE, (self.x + 8, self.y + 6, 10, 10))
        pygame.draw.rect(screen, WHITE, (self.x + 27, self.y + 6, 10, 10))
        pygame.draw.rect(screen, BLACK, (self.x + 10, self.y + 8, 6, 6))
        pygame.draw.rect(screen, BLACK, (self.x + 29, self.y + 8, 6, 6))
        
        # Tentacles - bigger and more
        pygame.draw.rect(screen, dark_green, (self.x + 3, self.y + 24, 5, 10))
        pygame.draw.rect(screen, dark_green, (self.x + 10, self.y + 26, 5, 8))
        pygame.draw.rect(screen, dark_green, (self.x + 17, self.y + 24, 5, 10))
        pygame.draw.rect(screen, dark_green, (self.x + 24, self.y + 26, 5, 8))
        pygame.draw.rect(screen, dark_green, (self.x + 31, self.y + 24, 5, 10))
        pygame.draw.rect(screen, dark_green, (self.x + 38, self.y + 26, 5, 8))
        
    def draw_crab_enemy(self, screen):
        """Second row - Red crab-like alien - EVEN BIGGER VERSION"""
        # Main body (red) - expanded further
        body_color = (220, 20, 20)
        dark_red = (180, 0, 0)
        
        # Main body - bigger
        pygame.draw.rect(screen, body_color, (self.x + 2, self.y + 6, 41, 18))
        
        # Claws - bigger
        pygame.draw.rect(screen, dark_red, (self.x - 3, self.y + 3, 12, 10))
        pygame.draw.rect(screen, dark_red, (self.x + 36, self.y + 3, 12, 10))
        
        # Claw details - bigger
        pygame.draw.rect(screen, body_color, (self.x - 5, self.y, 8, 8))
        pygame.draw.rect(screen, body_color, (self.x + 42, self.y, 8, 8))
        
        # Eyes - bigger
        pygame.draw.rect(screen, WHITE, (self.x + 9, self.y + 8, 8, 8))
        pygame.draw.rect(screen, WHITE, (self.x + 28, self.y + 8, 8, 8))
        pygame.draw.rect(screen, BLACK, (self.x + 11, self.y + 10, 4, 4))
        pygame.draw.rect(screen, BLACK, (self.x + 30, self.y + 10, 4, 4))
        
        # Legs - more and bigger
        pygame.draw.rect(screen, dark_red, (self.x + 6, self.y + 24, 4, 6))
        pygame.draw.rect(screen, dark_red, (self.x + 13, self.y + 24, 4, 6))
        pygame.draw.rect(screen, dark_red, (self.x + 20, self.y + 24, 4, 6))
        pygame.draw.rect(screen, dark_red, (self.x + 27, self.y + 24, 4, 6))
        pygame.draw.rect(screen, dark_red, (self.x + 34, self.y + 24, 4, 6))
        pygame.draw.rect(screen, dark_red, (self.x + 41, self.y + 24, 4, 6))
        
    def draw_octopus_enemy(self, screen):
        """Middle rows - Blue octopus-like alien - EVEN BIGGER VERSION"""
        # Main body (blue) - expanded further
        body_color = (20, 100, 220)
        dark_blue = (0, 60, 180)
        
        # Round head - bigger
        pygame.draw.rect(screen, body_color, (self.x + 5, self.y, 35, 24))
        pygame.draw.rect(screen, body_color, (self.x + 1, self.y + 6, 43, 14))
        
        # Eyes - bigger
        pygame.draw.rect(screen, WHITE, (self.x + 10, self.y + 6, 9, 10))
        pygame.draw.rect(screen, WHITE, (self.x + 26, self.y + 6, 9, 10))
        pygame.draw.rect(screen, BLACK, (self.x + 12, self.y + 8, 5, 6))
        pygame.draw.rect(screen, BLACK, (self.x + 28, self.y + 8, 5, 6))
        
        # Wavy tentacles - bigger and more
        pygame.draw.rect(screen, dark_blue, (self.x + 1, self.y + 18, 4, 10))
        pygame.draw.rect(screen, dark_blue, (self.x + 7, self.y + 20, 4, 8))
        pygame.draw.rect(screen, dark_blue, (self.x + 13, self.y + 18, 4, 10))
        pygame.draw.rect(screen, dark_blue, (self.x + 19, self.y + 20, 4, 8))
        pygame.draw.rect(screen, dark_blue, (self.x + 25, self.y + 18, 4, 10))
        pygame.draw.rect(screen, dark_blue, (self.x + 31, self.y + 20, 4, 8))
        pygame.draw.rect(screen, dark_blue, (self.x + 37, self.y + 18, 4, 10))
        pygame.draw.rect(screen, dark_blue, (self.x + 43, self.y + 20, 4, 8))
        
        # Tentacle curves - bigger
        pygame.draw.rect(screen, dark_blue, (self.x - 1, self.y + 26, 4, 4))
        pygame.draw.rect(screen, dark_blue, (self.x + 42, self.y + 26, 4, 4))
        
    def draw_basic_enemy(self, screen):
        """Bottom rows - Simple geometric alien - EVEN BIGGER VERSION"""
        # Main body (mixed colors) - expanded further
        if self.enemy_type == 3:
            body_color = (200, 100, 0)  # Orange
            accent_color = (255, 150, 0)
        else:
            body_color = (150, 0, 150)  # Purple
            accent_color = (200, 0, 200)
        
        # Simple rectangular body - bigger
        pygame.draw.rect(screen, body_color, (self.x + 2, self.y + 4, 41, 22))
        
        # Top details - bigger
        pygame.draw.rect(screen, accent_color, (self.x - 2, self.y, 12, 12))
        pygame.draw.rect(screen, accent_color, (self.x + 35, self.y, 12, 12))
        
        # Eyes - bigger
        pygame.draw.rect(screen, WHITE, (self.x + 8, self.y + 6, 10, 10))
        pygame.draw.rect(screen, WHITE, (self.x + 27, self.y + 6, 10, 10))
        pygame.draw.rect(screen, BLACK, (self.x + 10, self.y + 8, 6, 6))
        pygame.draw.rect(screen, BLACK, (self.x + 29, self.y + 8, 6, 6))
        
        # Bottom spikes - bigger and more
        pygame.draw.rect(screen, accent_color, (self.x + 5, self.y + 26, 5, 6))
        pygame.draw.rect(screen, accent_color, (self.x + 11, self.y + 26, 5, 6))
        pygame.draw.rect(screen, accent_color, (self.x + 17, self.y + 26, 5, 6))
        pygame.draw.rect(screen, accent_color, (self.x + 23, self.y + 26, 5, 6))
        pygame.draw.rect(screen, accent_color, (self.x + 29, self.y + 26, 5, 6))
        pygame.draw.rect(screen, accent_color, (self.x + 35, self.y + 26, 5, 6))
        pygame.draw.rect(screen, accent_color, (self.x + 41, self.y + 26, 5, 6))
        
    def draw(self, screen):
        """Draw the enemy based on its type"""
        if self.enemy_type == 0:  # Top row
            self.draw_squid_enemy(screen)
        elif self.enemy_type == 1:  # Second row
            self.draw_crab_enemy(screen)
        elif self.enemy_type == 2:  # Middle row
            self.draw_octopus_enemy(screen)
        else:  # Bottom rows (3 and 4)
            self.draw_basic_enemy(screen)

class EnemyExplosion:
    """Simple explosion effect when enemy is destroyed"""
    def __init__(self, x, y, enemy_type):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        self.particles = []
        self.start_time = pygame.time.get_ticks()
        self.duration = 500  # 0.5 seconds
        
        # Create explosion particles based on enemy type
        colors = [
            [(0, 255, 0), (0, 200, 0), (255, 255, 0)],  # Green squid
            [(255, 50, 50), (200, 0, 0), (255, 150, 0)],  # Red crab
            [(50, 150, 255), (0, 100, 200), (255, 255, 255)],  # Blue octopus
            [(255, 150, 0), (200, 100, 0), (255, 255, 0)],  # Orange
            [(200, 50, 200), (150, 0, 150), (255, 100, 255)]   # Purple
        ]
        
        explosion_colors = colors[enemy_type] if enemy_type < len(colors) else colors[0]
        
        # Create 8-12 particles
        for _ in range(random.randint(8, 12)):
            particle = {
                'x': x + random.randint(-10, 10),
                'y': y + random.randint(-10, 10),
                'vel_x': random.uniform(-3, 3),
                'vel_y': random.uniform(-3, 3),
                'color': random.choice(explosion_colors),
                'size': random.randint(2, 5),
                'life': random.randint(300, 500)
            }
            self.particles.append(particle)
    
    def update(self):
        """Update explosion animation"""
        current_time = pygame.time.get_ticks()
        
        # Update particles
        for particle in self.particles[:]:
            particle['x'] += particle['vel_x']
            particle['y'] += particle['vel_y']
            particle['vel_y'] += 0.1  # Gravity
            particle['life'] -= 16  # Assuming 60 FPS
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
        
        # Check if explosion is done
        return current_time - self.start_time < self.duration and len(self.particles) > 0
    
    def draw(self, screen):
        """Draw explosion particles"""
        for particle in self.particles:
            if particle['life'] > 0:
                alpha = max(0, min(255, particle['life']))
                # Create a surface for alpha blending
                particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
                color_with_alpha = (*particle['color'], alpha)
                pygame.draw.circle(particle_surface, color_with_alpha, 
                                 (particle['size'], particle['size']), particle['size'])
                screen.blit(particle_surface, (int(particle['x'] - particle['size']), 
                                             int(particle['y'] - particle['size'])))

class Bullet:
    def __init__(self, x, y, speed, owner_id=None, pierce_hits=0, length_multiplier=1.0,
                 can_phase_barriers=False, boss_damage_multiplier=1.0):
        self.x = x
        self.y = y
        self.width = 5
        self.height = int(15 * length_multiplier)
        self.speed = speed
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.owner_id = owner_id
        self.pierce_hits = pierce_hits
        self.can_phase_barriers = can_phase_barriers
        self.boss_damage_multiplier = boss_damage_multiplier

    def move(self):
        self.y += self.speed
        self.rect.y = self.y
        
    def is_off_screen(self):
        return self.y < -20 or self.y > SCREEN_HEIGHT + 20
        
    def draw(self, screen):
        color = YELLOW if self.speed < 0 else WHITE
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))

class PowerUp:
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.power_type = power_type
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.speed = 3
        self.spawn_time = pygame.time.get_ticks()
        
    def move(self):
        self.y += self.speed
        self.rect.y = self.y
        
    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT
        
    def is_expired(self):
        return pygame.time.get_ticks() - self.spawn_time > 15000
        
    def draw(self, screen):
        colors = {
            'rapid_fire': ORANGE,
            'invincibility': PURPLE,
            'laser': CYAN,
            'multi_shot': YELLOW
        }
        color = colors.get(self.power_type, WHITE)
        
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.01)) * 8
        pygame.draw.circle(screen, color, 
                         (self.x + self.width // 2, self.y + self.height // 2), 
                         self.width // 2 + pulse)
        
        font = pygame.font.Font(None, 32)
        symbols = {
            'rapid_fire': 'R',
            'invincibility': 'I', 
            'laser': 'L',
            'multi_shot': 'M'
        }
        symbol = symbols.get(self.power_type, '?')
        text = font.render(symbol, True, BLACK)
        text_rect = text.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text, text_rect)

class LaserBeam:
    def __init__(self, x, owner_player_id=1, duration_multiplier=1.0):
        self.x = x
        self.width = 15
        self.height = SCREEN_HEIGHT
        # Apply duration multiplier to base duration
        base_duration = 1000  # 1 second base
        self.duration = int(base_duration * duration_multiplier)
        self.start_time = pygame.time.get_ticks()
        self.rect = pygame.Rect(x - self.width // 2, 0, self.width, self.height)
        self.owner_player_id = owner_player_id
        
    def update_position(self, new_x):
        self.x = new_x
        self.rect.x = new_x - self.width // 2
        
    def is_active(self):
        return pygame.time.get_ticks() - self.start_time < self.duration
        
    def draw(self, screen):
        if self.is_active():
            alpha = 150 + abs(math.sin(pygame.time.get_ticks() * 0.02)) * 105
            laser_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(laser_surface, (*CYAN, int(alpha)), (0, 0, self.width, self.height))
            screen.blit(laser_surface, (self.x - self.width // 2, 0))

class Barrier:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 90
        self.height = 60
        self.blocks = []
        self.create_barrier()
        
    def create_barrier(self):
        for row in range(5):
            for col in range(8):
                if not (row == 0 and (col == 0 or col == 7)) and not (row == 1 and (col <= 1 or col >= 6)):
                    block_x = self.x + col * 11
                    block_y = self.y + row * 12
                    self.blocks.append(pygame.Rect(block_x, block_y, 11, 12))
                    
    def check_collision(self, bullet_rect):
        for block in self.blocks[:]:
            if block.colliderect(bullet_rect):
                self.blocks.remove(block)
                return True
        return False
        
    def draw(self, screen):
        for block in self.blocks:
            pygame.draw.rect(screen, GREEN, block)

class TitleScreen:
    def __init__(self, screen, score_manager, sound_manager):
        self.screen = screen
        self.score_manager = score_manager
        self.sound_manager = sound_manager
        self.font_large = pygame.font.Font(None, 128)
        self.font_medium = pygame.font.Font(None, 72)
        self.font_small = pygame.font.Font(None, 48)
        self.selected_option = 0
        self.options = ["Single Player", "Co-op", "High Scores", "Quit"]
        self.controllers = []
        self.scan_controllers()

        # Debug code detection (up, down, left, right, right, left, down, up)
        self.debug_sequence = ["up", "down", "left", "right", "right", "left", "down", "up"]
        self.debug_index = 0
        
    def scan_controllers(self):
        self.controllers = []
        for i in range(pygame.joystick.get_count()):
            controller = pygame.joystick.Joystick(i)
            controller.init()
            self.controllers.append(controller)

    def _register_debug_input(self, direction):
        expected = self.debug_sequence[self.debug_index]
        if direction == expected:
            self.debug_index += 1
            if self.debug_index == len(self.debug_sequence):
                self.debug_index = 0
                return True
        else:
            self.debug_index = 1 if direction == self.debug_sequence[0] else 0
        return False
            
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    if self._register_debug_input("up"):
                        return "debug_menu"
                    self.sound_manager.play_sound('menu_change')
                    self.selected_option = (self.selected_option - 1) % len(self.options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    if self._register_debug_input("down"):
                        return "debug_menu"
                    self.sound_manager.play_sound('menu_change')
                    self.selected_option = (self.selected_option + 1) % len(self.options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.sound_manager.play_sound('menu_select')
                    if self.selected_option == 0:
                        return "single"
                    elif self.selected_option == 1:
                        return "coop"
                    elif self.selected_option == 2:
                        return "highscores"
                    elif self.selected_option == 3:
                        return "quit"
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    if self._register_debug_input("left"):
                        return "debug_menu"
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    if self._register_debug_input("right"):
                        return "debug_menu"
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:
                    self.sound_manager.play_sound('menu_select')
                    if self.selected_option == 0:
                        return "single"
                    elif self.selected_option == 1:
                        return "coop"
                    elif self.selected_option == 2:
                        return "highscores"
                    elif self.selected_option == 3:
                        return "quit"
            elif event.type == pygame.JOYHATMOTION:
                if event.value[1] == 1:
                    if self._register_debug_input("up"):
                        return "debug_menu"
                    self.sound_manager.play_sound('menu_change')
                    self.selected_option = (self.selected_option - 1) % len(self.options)
                elif event.value[1] == -1:
                    if self._register_debug_input("down"):
                        return "debug_menu"
                    self.sound_manager.play_sound('menu_change')
                    self.selected_option = (self.selected_option + 1) % len(self.options)
                elif event.value[0] == -1:
                    if self._register_debug_input("left"):
                        return "debug_menu"
                elif event.value[0] == 1:
                    if self._register_debug_input("right"):
                        return "debug_menu"
                    
        return None
        
    def draw(self):
        self.screen.fill(BLACK)
        
        # Title
        title_text = self.font_large.render("PLACE INVADERS", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle_text = self.font_medium.render("Enhanced Edition", True, CYAN)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 280))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Menu options
        for i, option in enumerate(self.options):
            color = YELLOW if i == self.selected_option else WHITE
            option_text = self.font_medium.render(option, True, color)
            option_rect = option_text.get_rect(center=(SCREEN_WIDTH // 2, 400 + i * 80))
            self.screen.blit(option_text, option_rect)
            
        # High score previews
        single_best = self.score_manager.get_best_score(False)
        coop_best = self.score_manager.get_best_score(True)
        
        preview_y = 750
        if single_best:
            single_text = self.font_small.render(f"Best Single: {single_best['score']:,} by {single_best['name']}", True, GRAY)
            single_rect = single_text.get_rect(center=(SCREEN_WIDTH // 2, preview_y))
            self.screen.blit(single_text, single_rect)
            preview_y += 40
            
        if coop_best:
            coop_text = self.font_small.render(f"Best Co-op: {coop_best['score']:,} by {coop_best['name']}", True, GRAY)
            coop_rect = coop_text.get_rect(center=(SCREEN_WIDTH // 2, preview_y))
            self.screen.blit(coop_text, coop_rect)
        
        # Controls info
        controls_info = [
            "Controls:",
            "Keyboard: Arrow Keys/WASD + Space",
            "Controller: D-pad/Stick + A button",
            f"Controllers detected: {len(self.controllers)}"
        ]
        
        for i, info in enumerate(controls_info):
            color = WHITE if i == 0 else CYAN
            info_text = self.font_small.render(info, True, color)
            self.screen.blit(info_text, (50, 850 + i * 35))

        pygame.display.flip()

class DebugMenu:
    def __init__(self, screen, sound_manager):
        self.screen = screen
        self.sound_manager = sound_manager
        self.font_large = pygame.font.Font(None, 96)
        self.font_medium = pygame.font.Font(None, 64)
        self.font_small = pygame.font.Font(None, 40)
        self.selected_index = 0
        self.scroll_offset = 0

        self.upgrade_limits = {
            'shot_speed_level': 20,
            'fire_rate_level': 20,
            'movement_speed_level': 20,
            'powerup_duration_level': 20,
            'pierce_level': 5,
            'bullet_length_level': 50,
            'barrier_phase_level': 1,
            'powerup_spawn_level': 5,
            'boss_damage_level': 5,
            'ammo_capacity_level': 5,
            'extra_bullet_level': 1,
        }

        self.config = {
            'mode': 'single',
            'start_level': 1,
            'start_score': 0,
            'xp_level': 1,
            'xp_current': 0,
            'players': [self._default_player_config(), self._default_player_config(player_id=2)],
        }

        self.menu_items = []
        self._build_menu_items()
        self._move_selection(0)  # Ensure first selectable item is highlighted

    def _default_player_config(self, player_id=1):
        upgrades = {key: 0 for key in self.upgrade_limits.keys()}
        return {
            'player_id': player_id,
            'lives': 3,
            'invincible': False,
            'boss_shield': False,
            'rapid_fire_ammo': 0,
            'multi_shot_ammo': 0,
            'laser': False,
            'upgrades': upgrades,
        }

    def _build_menu_items(self):
        self.menu_items = [
            {'type': 'label', 'label': 'Debug Mode'},
            {'type': 'choice', 'label': 'Mode', 'choices': ['single', 'coop'], 'path': ('mode',)},
            {'type': 'int', 'label': 'Start Level', 'path': ('start_level',), 'min': 1, 'max': 99, 'step': 1},
            {'type': 'int', 'label': 'Start Score', 'path': ('start_score',), 'min': 0, 'max': 9999999, 'step': 250},
            {'type': 'int', 'label': 'XP Level', 'path': ('xp_level',), 'min': 1, 'max': 99, 'step': 1},
            {'type': 'int', 'label': 'XP Current', 'path': ('xp_current',), 'min': 0, 'max': 50000, 'step': 250},
        ]

        for idx in range(2):
            player_label = f"Player {idx + 1} Overrides"
            self.menu_items.append({'type': 'label', 'label': player_label})
            self.menu_items.extend([
                {'type': 'int', 'label': f'P{idx + 1} Lives', 'path': ('players', idx, 'lives'), 'min': 1, 'max': 99, 'step': 1},
                {'type': 'bool', 'label': f'P{idx + 1} Invincible', 'path': ('players', idx, 'invincible')},
                {'type': 'bool', 'label': f'P{idx + 1} Boss Shield', 'path': ('players', idx, 'boss_shield')},
                {'type': 'int', 'label': f'P{idx + 1} Rapid Fire Ammo', 'path': ('players', idx, 'rapid_fire_ammo'), 'min': 0, 'max': 1000, 'step': 25},
                {'type': 'int', 'label': f'P{idx + 1} Multi-Shot Ammo', 'path': ('players', idx, 'multi_shot_ammo'), 'min': 0, 'max': 1000, 'step': 25},
                {'type': 'bool', 'label': f'P{idx + 1} Laser', 'path': ('players', idx, 'laser')},
            ])

            for upgrade_key, max_level in self.upgrade_limits.items():
                pretty_name = upgrade_key.replace('_', ' ').title()
                self.menu_items.append(
                    {
                        'type': 'int',
                        'label': f'P{idx + 1} {pretty_name}',
                        'path': ('players', idx, 'upgrades', upgrade_key),
                        'min': 0,
                        'max': max_level,
                        'step': 1,
                    }
                )

        self.menu_items.extend([
            {'type': 'action', 'label': 'Start Debug Game', 'action': 'start'},
            {'type': 'action', 'label': 'Back to Title', 'action': 'back'},
        ])

    def _get_value(self, path):
        ref = self.config
        for key in path[:-1]:
            ref = ref[key]
        return ref[path[-1]]

    def _set_value(self, path, value):
        ref = self.config
        for key in path[:-1]:
            ref = ref[key]
        ref[path[-1]] = value

    def _move_selection(self, direction):
        selectable_indices = [i for i, item in enumerate(self.menu_items) if item['type'] != 'label']
        if not selectable_indices:
            return

        if self.selected_index not in selectable_indices:
            self.selected_index = selectable_indices[0]
            return

        current_pos = selectable_indices.index(self.selected_index)
        new_pos = (current_pos + direction) % len(selectable_indices)
        self.selected_index = selectable_indices[new_pos]

        visible_count = max(1, (SCREEN_HEIGHT - 160 - 220) // 40)
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + visible_count:
            self.scroll_offset = self.selected_index - visible_count + 1

    def _format_value(self, item):
        if item['type'] == 'bool':
            return 'ON' if self._get_value(item['path']) else 'OFF'
        if item['type'] == 'choice':
            return self._get_value(item['path'])
        if item['type'] == 'int':
            return str(self._get_value(item['path']))
        return ''

    def _adjust_value(self, item, delta):
        if item['type'] == 'bool':
            self._set_value(item['path'], not self._get_value(item['path']))
        elif item['type'] == 'choice':
            choices = item['choices']
            current = self._get_value(item['path'])
            idx = choices.index(current)
            new_idx = (idx + delta) % len(choices)
            self._set_value(item['path'], choices[new_idx])
        elif item['type'] == 'int':
            value = self._get_value(item['path']) + (item.get('step', 1) * delta)
            value = max(item.get('min', value), min(item.get('max', value), value))
            self._set_value(item['path'], value)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit', None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'back', None
                if event.key in (pygame.K_UP, pygame.K_w):
                    self._move_selection(-1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._move_selection(1)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self._adjust_value(self.menu_items[self.selected_index], -1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._adjust_value(self.menu_items[self.selected_index], 1)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    selected_item = self.menu_items[self.selected_index]
                    if selected_item['type'] == 'action':
                        return selected_item['action'], self.config
            elif event.type == pygame.JOYHATMOTION:
                if event.value[1] == 1:
                    self._move_selection(-1)
                elif event.value[1] == -1:
                    self._move_selection(1)
                elif event.value[0] == -1:
                    self._adjust_value(self.menu_items[self.selected_index], -1)
                elif event.value[0] == 1:
                    self._adjust_value(self.menu_items[self.selected_index], 1)
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 1:  # B button - back
                    return 'back', None
                elif event.button == 0:  # A button - select
                    selected_item = self.menu_items[self.selected_index]
                    if selected_item['type'] == 'action':
                        return selected_item['action'], self.config
        return None, None

    def draw(self):
        self.screen.fill((10, 10, 20))

        title_text = self.font_large.render('Debug Menu', True, CYAN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title_text, title_rect)

        start_y = 160
        line_height = 40
        visible_count = max(1, (SCREEN_HEIGHT - start_y - 220) // line_height)
        start_index = self.scroll_offset
        end_index = min(len(self.menu_items), start_index + visible_count)

        for draw_idx, idx in enumerate(range(start_index, end_index)):
            item = self.menu_items[idx]
            y_pos = start_y + draw_idx * line_height
            if item['type'] == 'label':
                label_text = self.font_medium.render(item['label'], True, ORANGE)
                self.screen.blit(label_text, (80, y_pos))
                continue

            value_text = self._format_value(item)
            color = YELLOW if idx == self.selected_index else WHITE
            label_surface = self.font_small.render(item['label'], True, color)
            value_surface = self.font_small.render(value_text, True, color)

            self.screen.blit(label_surface, (80, y_pos))
            self.screen.blit(value_surface, (SCREEN_WIDTH - 300, y_pos))

        instructions = [
            'Arrows/D-pad: Navigate',
            'Left/Right: Adjust values',
            'Enter/A: Activate action',
            'Esc/B: Back to title',
        ]

        for i, text in enumerate(instructions):
            info = self.font_small.render(text, True, GRAY)
            self.screen.blit(info, (80, SCREEN_HEIGHT - 180 + i * 35))

        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        while True:
            action, config = self.handle_events()
            if action in ['start', 'back', 'quit']:
                return action, config
            self.draw()
            clock.tick(60)

class UFOWarningScreen:
    def __init__(self, screen, level):
        self.screen = screen
        self.level = level
        self.font_huge = pygame.font.Font(None, 144)
        self.font_large = pygame.font.Font(None, 96)
        self.font_medium = pygame.font.Font(None, 64)
        self.start_time = pygame.time.get_ticks()
        self.duration = 3000  # 3 seconds
        
    def is_finished(self):
        return pygame.time.get_ticks() - self.start_time >= self.duration
        
    def draw(self):
        self.screen.fill(BLACK)
        
        # Flashing red background
        flash_intensity = abs(math.sin(pygame.time.get_ticks() * 0.01)) * 0.3
        flash_color = (int(50 * flash_intensity), 0, 0)
        self.screen.fill(flash_color)
        
        # Main warning text
        warning_text = self.font_huge.render("WARNING!", True, RED)
        warning_rect = warning_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(warning_text, warning_rect)
        
        # UFO approaching text
        ufo_text = self.font_large.render("UFO APPROACHING!", True, YELLOW)
        ufo_rect = ufo_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(ufo_text, ufo_rect)
        
        # Level indicator
        level_text = self.font_medium.render(f"BOSS LEVEL {self.level}", True, WHITE)
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        self.screen.blit(level_text, level_rect)
        
        # Countdown
        remaining = (self.duration - (pygame.time.get_ticks() - self.start_time)) / 1000.0
        countdown_text = self.font_medium.render(f"Prepare! {remaining:.1f}s", True, CYAN)
        countdown_rect = countdown_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
        self.screen.blit(countdown_text, countdown_rect)
        
        pygame.display.flip()

class Game:
    def __init__(self, score_manager, sound_manager):
        try:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        except:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            
        pygame.display.set_caption("Space Invaders Enhanced")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        self.score = 0
        self.level = 1
        self.total_enemies_killed = 0
        self.coop_mode = False
        self.score_manager = score_manager
        self.sound_manager = sound_manager
        self.awaiting_name_input = False
        self.awaiting_level_up = False
        self.pending_level_up = False  # Track if player leveled up during current level
        self.player_xp_level = 1  # Track player's XP level separately from game level
        self.showing_ufo_warning = False
        self.ufo_warning_screen = None
        
        # ADDED: Game over timing and input delay
        self.game_over_time = 0
        self.input_delay_duration = 1000  # 1 second delay
        
        # XP and upgrade system
        self.xp_system = XPSystem()
        
        # Visual feedback
        self.floating_texts = []
        
        # Boss system
        self.current_boss = None
        self.is_boss_level = False
        self.boss_shield_granted = False
        
        self.controllers = []
        self.scan_controllers()
        
        self.players = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.barriers = []
        self.power_ups = []
        self.laser_beams = []
        self.enemy_explosions = []
        self.boss_explosion_particles = []
        self.boss_explosion_particles = []
        self.screen_shake_intensity = 0
        self.screen_shake_duration = 0
        self.screen_flash_intensity = 0
        self.screen_flash_duration = 0
        self.boss_explosion_waves = []
        self.available_bosses = [Boss, AlienOverlordBoss]

        self.font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 48)
        self.tiny_font = pygame.font.Font(None, 36)
        
    def scan_controllers(self):
        self.controllers = []
        for i in range(pygame.joystick.get_count()):
            controller = pygame.joystick.Joystick(i)
            controller.init()
            self.controllers.append(controller)
            
    def setup_game(self, mode, debug_config=None):
        self.coop_mode = (mode == "coop")
        self.players = []
        
        if self.coop_mode:
            controller1 = self.controllers[0] if len(self.controllers) > 0 else None
            # Create individual upgrades for each player
            player1_upgrades = PlayerUpgrades()
            player1 = Player(SCREEN_WIDTH // 2 - 90, SCREEN_HEIGHT - 80, 1, controller1, player1_upgrades)
            player1.coop_mode = True
            self.players.append(player1)
            
            controller2 = self.controllers[1] if len(self.controllers) > 1 else None
            player2_upgrades = PlayerUpgrades()
            player2 = Player(SCREEN_WIDTH // 2 + 30, SCREEN_HEIGHT - 80, 2, controller2, player2_upgrades)
            player2.coop_mode = True
            self.players.append(player2)
        else:
            controller = self.controllers[0] if len(self.controllers) > 0 else None
            player_upgrades = PlayerUpgrades()
            self.players.append(Player(SCREEN_WIDTH // 2 - 30, SCREEN_HEIGHT - 80, 1, controller, player_upgrades))
            
        if debug_config:
            self.apply_debug_config(debug_config)

        self.create_barriers()
        self.setup_level()

    def apply_debug_config(self, debug_config):
        self.level = max(1, debug_config.get('start_level', self.level))
        self.score = max(0, debug_config.get('start_score', self.score))

        xp_level = max(1, debug_config.get('xp_level', self.xp_system.level))
        self.xp_system.level = xp_level
        self.xp_system.current_xp = max(0, debug_config.get('xp_current', 0))
        self.xp_system.xp_for_next_level = int(
            XP_BASE_REQUIREMENT * (1 + XP_INCREASE_RATE) ** (self.xp_system.level - 1)
        )

        player_configs = debug_config.get('players', [])
        for idx, player in enumerate(self.players):
            if idx >= len(player_configs):
                continue

            config = player_configs[idx]
            player.lives = max(1, config.get('lives', player.lives))
            player.is_alive = True

            player.invincible = config.get('invincible', False)
            player.invincible_end_time = pygame.time.get_ticks() + 10_000_000 if player.invincible else 0

            if config.get('boss_shield', False):
                player.activate_boss_shield()
            else:
                player.clear_boss_shield()

            upgrades = config.get('upgrades', {})
            for key, value in upgrades.items():
                setattr(player.upgrades, key, max(0, value))

            player.clear_all_power_ups()

            rapid_ammo = config.get('rapid_fire_ammo', 0)
            if rapid_ammo > 0:
                player.add_ammo_power_up('rapid_fire', rapid_ammo)

            multi_ammo = config.get('multi_shot_ammo', 0)
            if multi_ammo > 0:
                player.add_ammo_power_up('multi_shot', multi_ammo)

            if config.get('laser'):
                player.activate_laser()

            player.reset_position()
        
    def calculate_enemy_speed_for_level(self, level):
        # Enemy speed only increases every 5 levels now
        speed_level = ((level - 1) // 5) + 1
        speed_increase = (speed_level - 1) * ENEMY_SPEED_PROGRESSION
        return BASE_ENEMY_SPEED + speed_increase
        
    def setup_level(self):
        """Setup current level - either boss or regular enemies"""
        self.is_boss_level = (self.level % 5 == 0)
        self.boss_shield_granted = False

        if self.is_boss_level:
            # ADDED: Show UFO warning before boss level
            self.showing_ufo_warning = True
            self.ufo_warning_screen = UFOWarningScreen(self.screen, self.level)
            self.current_boss = None  # Don't create boss until warning is done
            self.enemies = []
            for player in self.players:
                player.clear_boss_shield()
        else:
            self.showing_ufo_warning = False
            self.ufo_warning_screen = None
            self.current_boss = None
            self.create_enemy_grid()

    def create_boss_instance(self):
        boss_class = random.choice(self.available_bosses)
        return boss_class(self.level)
        
    def create_barriers(self):
        self.barriers = []
        barrier_count = 5
        barrier_spacing = SCREEN_WIDTH // (barrier_count + 1)
        for i in range(barrier_count):
            barrier_x = barrier_spacing * (i + 1) - 45
            barrier_y = SCREEN_HEIGHT - 300
            self.barriers.append(Barrier(barrier_x, barrier_y))
            
    def create_enemy_grid(self):
        self.enemies = []
        rows = 5
        cols = 12
        enemy_spacing_x = 90
        enemy_spacing_y = 75
        start_x = (SCREEN_WIDTH - (cols - 1) * enemy_spacing_x) // 2
        start_y = 100
        
        level_speed = self.calculate_enemy_speed_for_level(self.level)
        
        for row in range(rows):
            for col in range(cols):
                enemy_x = start_x + col * enemy_spacing_x
                enemy_y = start_y + row * enemy_spacing_y
                enemy = Enemy(enemy_x, enemy_y, row)  # Pass row as enemy_type
                enemy.base_speed = level_speed
                enemy.speed = level_speed
                self.enemies.append(enemy)
                
        self.update_enemy_speed()
        
    def update_enemy_speed(self):
        # More aggressive speed increase as enemies are eliminated
        total_enemies = 60
        remaining_enemies = len(self.enemies)
        if remaining_enemies > 0:
            destroyed_ratio = (total_enemies - remaining_enemies) / total_enemies
            speed_multiplier = 1 + destroyed_ratio * 14
            
            if remaining_enemies <= 5:
                extra_multiplier = (5 - remaining_enemies + 1) * 2
                speed_multiplier += extra_multiplier
                
            for enemy in self.enemies:
                enemy.speed = enemy.base_speed * speed_multiplier

    def grant_post_boss_shield(self):
        """Give each player a one-hit shield after defeating a boss"""
        if self.boss_shield_granted:
            return

        for player in self.players:
            player.activate_boss_shield()

        self.boss_shield_granted = True
        self.floating_texts.append(FloatingText(
            "Shield Ready!",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
            color=CYAN,
            lifetime=1500
        ))

    def add_xp(self, amount, source_x=None, source_y=None):
        """Add XP and handle level up"""
        old_level = self.xp_system.level
        leveled_up = self.xp_system.add_xp(amount)
        
        # Visual feedback
        if source_x and source_y:
            self.floating_texts.append(FloatingText(source_x, source_y, f"+{amount} XP", GOLD))
        
        # Check if XP level increased
        if self.xp_system.level > old_level:
            self.pending_level_up = True
            print(f"Player leveled up! XP Level: {self.xp_system.level}, Game Level: {self.level}")  # Debug

            # PLAY LEVEL UP SOUND
            if self.sound_manager:
                self.sound_manager.play_sound('levelup')

            # ADDED: Show visual indicator on all alive players
            for player in self.players:
                if player.is_alive:
                    player.show_level_up_indicator()
        
        return leveled_up
            
    def spawn_power_up(self, player=None):
        bonus_chance = player.upgrades.get_powerup_spawn_bonus() if player else 0
        drop_chance = 5 + bonus_chance
        if random.randint(1, 100) <= drop_chance:
            power_types = ['rapid_fire', 'invincibility', 'laser', 'multi_shot']
            power_type = random.choice(power_types)
            x = random.randint(100, SCREEN_WIDTH - 100)
            y = 100
            self.power_ups.append(PowerUp(x, y, power_type))
        
    def handle_events(self):
        if self.awaiting_name_input:
            return self.handle_name_input_events()
        elif self.awaiting_level_up:
            return self.handle_level_up_events()
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.game_over:
                    if len(self.players) > 0 and self.players[0].is_alive:
                        shots = self.players[0].shoot(self.sound_manager)
                        for shot_type, shot in shots:
                            if shot_type == 'bullet':
                                self.sound_manager.play_sound('shoot')
                                self.player_bullets.append(shot)
                            elif shot_type == 'laser':
                                self.sound_manager.play_sound('laser')
                                self.laser_beams.append(shot)
                elif event.key == pygame.K_RCTRL and not self.game_over and self.coop_mode:
                    if len(self.players) > 1 and self.players[1].is_alive:
                        shots = self.players[1].shoot(self.sound_manager)
                        for shot_type, shot in shots:
                            if shot_type == 'bullet':
                                self.sound_manager.play_sound('shoot')
                                self.player_bullets.append(shot)
                            elif shot_type == 'laser':
                                self.sound_manager.play_sound('laser')
                                self.laser_beams.append(shot)
                elif event.key == pygame.K_r and self.game_over and not self.awaiting_name_input:
                    # FIXED: Check input delay before allowing restart
                    if pygame.time.get_ticks() - self.game_over_time >= self.input_delay_duration:
                        return "restart"
                elif event.key == pygame.K_ESCAPE:
                    if self.game_over and not self.awaiting_name_input:
                        # FIXED: Check input delay before allowing title screen
                        if pygame.time.get_ticks() - self.game_over_time >= self.input_delay_duration:
                            return "title"
                    elif not self.game_over:
                        return "title"
            elif event.type == pygame.JOYBUTTONDOWN:
                # FIXED: Add controller support for game over screen
                if self.game_over and not self.awaiting_name_input:
                    if pygame.time.get_ticks() - self.game_over_time >= self.input_delay_duration:
                        if event.button == 0:  # A button - restart
                            return "restart"
                        elif event.button == 1:  # B button - title screen
                            return "title"
                else:
                    # Normal controller shooting
                    for i, player in enumerate(self.players):
                        if player.controller and event.joy == player.controller.get_instance_id() and player.is_alive:
                            if event.button == 0:
                                shots = player.shoot(self.sound_manager)
                                for shot_type, shot in shots:
                                    if shot_type == 'bullet':
                                        self.sound_manager.play_sound('shoot')
                                        self.player_bullets.append(shot)
                                    elif shot_type == 'laser':
                                        self.sound_manager.play_sound('laser')
                                        self.laser_beams.append(shot)
                                        
        return None
    
    def handle_name_input_events(self):
        """Handle events during name input"""
        # ADDED: Input delay after game over
        if pygame.time.get_ticks() - self.game_over_time < self.input_delay_duration:
            return None
            
        if hasattr(self, 'name_input_screen'):
            name = self.name_input_screen.handle_events()
            if name == "quit":
                self.running = False
                return None
            elif name:
                self.score_manager.add_score(name, self.score, self.level, self.coop_mode)
                self.awaiting_name_input = False
                del self.name_input_screen
                return "title"
        return None
    
    def handle_level_up_events(self):
        """Handle events during level up screen"""
        if hasattr(self, 'level_up_screen'):
            result = self.level_up_screen.handle_events()
            if result == "quit":
                self.running = False
                return None
            elif result == "continue":
                print("Level up complete, continuing...")  # Debug
                self.awaiting_level_up = False
                self.pending_level_up = False  # Clear the flag
                del self.level_up_screen
                
                # Now advance the game level
                self.level += 1
                print(f"Advanced to game level {self.level} after level up")  # Debug
                
                # Respawn dead players with 1 life if their partner survived
                if self.coop_mode and len(self.players) == 2:
                    if not self.players[0].is_alive and self.players[1].is_alive:
                        self.players[0].lives = 1
                        self.players[0].respawn()
                    elif not self.players[1].is_alive and self.players[0].is_alive:
                        self.players[1].lives = 1
                        self.players[1].respawn()
                
                self.setup_level()
                self.create_barriers()
        return None
                    
    def handle_input(self):
        if not self.game_over and not self.awaiting_level_up:
            keys = pygame.key.get_pressed()
            
            if len(self.players) > 0:
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.players[0].move_left()
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.players[0].move_right()
                    
                self.players[0].handle_controller_input()
                    
            if self.coop_mode and len(self.players) > 1:
                if not self.players[1].controller:
                    if keys[pygame.K_LEFT]:
                        self.players[1].move_left()
                    if keys[pygame.K_RIGHT]:
                        self.players[1].move_right()
                else:
                    self.players[1].handle_controller_input()
    
    def activate_power_up(self, player, power_type):
        if power_type == 'rapid_fire':
            player.activate_rapid_fire()
        elif power_type == 'invincibility':
            player.activate_invincibility()
        elif power_type == 'laser':
            player.activate_laser()
        elif power_type == 'multi_shot':
            player.activate_multi_shot()
            
    def check_level_complete(self):
        """Check if level is complete and handle progression"""
        level_complete = False
        
        if self.is_boss_level:
            if self.current_boss and self.current_boss.is_destruction_complete():
                # Boss destruction sequence finished
                self.current_boss = None
                level_complete = True
            elif not self.current_boss:  # Boss was destroyed instantly (shouldn't happen with new system)
                level_complete = True
        else:
            if not self.enemies:  # All regular enemies defeated
                level_complete = True
        
        if level_complete:
            print(f"Level complete! pending_level_up: {self.pending_level_up}")  # Debug
            # Check if player leveled up during this level - show level up screen first
            if self.pending_level_up:
                print("Showing level up screen...")  # Debug
                self.awaiting_level_up = True
                return False  # Don't advance game level yet, wait for upgrade selection
            
            # No level up pending, advance to next level
            self.level += 1
            print(f"Advanced to game level {self.level}")  # Debug
            
            # Respawn dead players with 1 life if their partner survived
            if self.coop_mode and len(self.players) == 2:
                if not self.players[0].is_alive and self.players[1].is_alive:
                    self.players[0].lives = 1
                    self.players[0].respawn()
                elif not self.players[1].is_alive and self.players[0].is_alive:
                    self.players[1].lives = 1
                    self.players[1].respawn()
            
            self.setup_level()
            self.create_barriers()
            return True
        return False
        
    def check_game_over(self):
        """Check if game is over based on player lives"""
        if self.coop_mode:
            game_over = all(not player.is_alive for player in self.players)
        else:
            game_over = not self.players[0].is_alive if self.players else True
            
        if game_over and not self.game_over:
            self.game_over = True
            self.game_over_time = pygame.time.get_ticks()  # ADDED: Record when game over occurred
            if self.score_manager.is_high_score(self.score, self.coop_mode):
                self.awaiting_name_input = True
                self.name_input_screen = NameInputScreen(self.screen, self.score, self.level, self.coop_mode)
                
        return game_over 
    
    def update(self):
        # ADDED: Handle UFO warning screen
        if self.showing_ufo_warning:
            if self.ufo_warning_screen.is_finished():
                self.showing_ufo_warning = False
                self.current_boss = self.create_boss_instance()
                self.ufo_warning_screen = None
            return  # Don't update game during warning
            
        if self.game_over or self.awaiting_level_up:
            return
        
        # Update floating texts
        self.floating_texts = [text for text in self.floating_texts if text.update()]

        # Update enemy explosions
        self.enemy_explosions = [explosion for explosion in self.enemy_explosions if explosion.update()]

        # Update screen effects
        if self.screen_shake_duration > 0:
            self.screen_shake_duration -= 16  # Assuming 60 FPS
            if self.screen_shake_duration <= 0:
                self.screen_shake_intensity = 0

        if self.screen_flash_duration > 0:
            self.screen_flash_duration -= 16
            self.screen_flash_intensity = max(0, int(255 * (self.screen_flash_duration / 1500)))

        # Update explosion waves
        for wave in self.boss_explosion_waves[:]:
            wave['radius'] += wave['growth_speed']
            wave['life'] -= 1
            
            if wave['life'] <= 0 or wave['radius'] >= wave['max_radius']:
                self.boss_explosion_waves.remove(wave)

        # Update boss explosion particles
        for particle in self.boss_explosion_particles[:]:
            particle['x'] += particle['vel_x']
            particle['y'] += particle['vel_y']
            particle['vel_y'] += 0.2  # Gravity
            particle['life'] -= 16  # Assuming 60 FPS
            
            if particle['life'] <= 0:
                self.boss_explosion_particles.remove(particle)
            
        for player in self.players:
            player.update_power_ups()
            
        for bullet in self.player_bullets[:]:
            bullet.move()
            if bullet.is_off_screen():
                self.player_bullets.remove(bullet)
                
        for bullet in self.enemy_bullets[:]:
            bullet.move()
            if bullet.is_off_screen():
                self.enemy_bullets.remove(bullet)
                
        for power_up in self.power_ups[:]:
            power_up.move()
            if power_up.is_off_screen() or power_up.is_expired():
                self.power_ups.remove(power_up)
                
        # Update laser beams
        for laser in self.laser_beams[:]:
            if laser.is_active():
                owner = next((p for p in self.players if p.player_id == laser.owner_player_id and p.is_alive), None)
                if owner:
                    laser.update_position(owner.x + owner.width // 2)
                else:
                    self.laser_beams.remove(laser)
                    continue
            else:
                self.laser_beams.remove(laser)
        
        # Update boss or regular enemies
        if self.is_boss_level and self.current_boss:
            self.current_boss.update(self.players, self.sound_manager)
            # Boss shooting
            boss_bullets = self.current_boss.shoot(self.players, self.sound_manager)
            self.enemy_bullets.extend(boss_bullets)
        else:
            # Regular enemy movement
            edge_hit = False
            for enemy in self.enemies:
                enemy.move()
                if enemy.x <= 0 or enemy.x >= SCREEN_WIDTH - enemy.width:
                    edge_hit = True
                    
            if edge_hit:
                for enemy in self.enemies:
                    enemy.drop_down()
                    
            for enemy in self.enemies:
                bullet = enemy.shoot(self.sound_manager)
                if bullet:
                    self.enemy_bullets.append(bullet)
                
        self.check_collisions()
        
        # Check level completion first
        if self.check_level_complete():
            pass
            
        # Then check game over
        self.check_game_over()
            
        # CHANGED: Check if enemies reached bottom - kill player and reset aliens
        if not self.is_boss_level:
            aliens_reached_bottom = False
            for enemy in self.enemies:
                if enemy.y + enemy.height >= SCREEN_HEIGHT - 200:  # Near bottom
                    aliens_reached_bottom = True
                    break
            
            if aliens_reached_bottom:
                # Kill all alive players
                for player in self.players:
                    if player.is_alive:
                        if player.take_damage(self.sound_manager):
                            pass  # Player took damage/died
                
                # Reset alien positions but keep their speed
                current_speeds = [enemy.speed for enemy in self.enemies]
                self.create_enemy_grid()
                # Restore the progressed speeds
                for i, enemy in enumerate(self.enemies):
                    if i < len(current_speeds):
                        enemy.speed = current_speeds[i]
        elif self.current_boss:
            # Check if boss reached player
            for player in self.players:
                if player.is_alive and self.current_boss.y + self.current_boss.height >= player.y:
                    # Kill the player first with sound
                    player.take_damage(self.sound_manager)
                    self.game_over = True
                    self.game_over_time = pygame.time.get_ticks()
                    if self.score_manager.is_high_score(self.score, self.coop_mode):
                        self.awaiting_name_input = True
                        self.name_input_screen = NameInputScreen(self.screen, self.score, self.level, self.coop_mode)
                    
    def check_collisions(self):
        # Player bullets vs enemies
        for bullet in self.player_bullets[:]:
            owner = next((p for p in self.players if p.player_id == bullet.owner_id), None)
            if self.is_boss_level and self.current_boss and not self.current_boss.destruction_complete:
                # Check turret collisions first
                turret_rects = self.current_boss.get_turret_rects()
                hit_turret = False
                
                for turret_rect, turret_index in turret_rects:
                    if turret_rect and bullet.rect.colliderect(turret_rect):
                        damage = max(1, int(math.ceil(bullet.boss_damage_multiplier)))
                        if bullet.pierce_hits <= 0:
                            self.player_bullets.remove(bullet)
                        self.sound_manager.play_sound('ufo_hit', volume_override=0.6)
                        if self.current_boss.take_turret_damage(turret_index, damage):
                            # Turret destroyed
                            self.score += 100
                            self.add_xp(20, turret_rect.centerx, turret_rect.centery)
                            self.sound_manager.play_sound('explosion_small', volume_override=0.6)
                        else:
                            self.score += 5
                            self.add_xp(2, turret_rect.centerx, turret_rect.centery)
                        if bullet.pierce_hits > 0:
                            bullet.pierce_hits -= 1
                        hit_turret = True
                        break

                # Check main body collision if no turret hit
                if not hit_turret:
                    main_body_rect = self.current_boss.get_main_body_rect()
                    if main_body_rect and bullet.rect.colliderect(main_body_rect):
                        damage = max(1, int(math.ceil(bullet.boss_damage_multiplier)))
                        if bullet.pierce_hits <= 0:
                            self.player_bullets.remove(bullet)
                        self.sound_manager.play_sound('ufo_hit', volume_override=0.8)
                        if self.current_boss.take_main_damage(damage):
                            # Boss completely destroyed - EPIC EXPLOSION SEQUENCE
                            self.score += 1000
                            self.add_xp(200, self.current_boss.x + self.current_boss.width // 2, self.current_boss.y)

                            # PLAY LARGE EXPLOSION SOUND
                            self.sound_manager.play_sound('explosion_large')

                            # CREATE MASSIVE BOSS EXPLOSION
                            self.boss_explosion_particles.extend(self.current_boss.create_final_explosion())

                            # Grant post-boss shield reward
                            self.grant_post_boss_shield()
                            
                            # SCREEN EFFECTS
                            self.screen_shake_intensity = 25  # Strong shake
                            self.screen_shake_duration = 2000  # 2 seconds
                            self.screen_flash_intensity = 255  # Bright white flash
                            self.screen_flash_duration = 1500  # 1.5 seconds
                            
                            # CREATE EXPLOSION WAVES
                            boss_center_x = self.current_boss.x + self.current_boss.width // 2
                            boss_center_y = self.current_boss.y + self.current_boss.height // 2
                            
                            for i in range(5):  # 5 expanding shock waves
                                wave = {
                                    'x': boss_center_x,
                                    'y': boss_center_y,
                                    'radius': 0,
                                    'max_radius': 300 + i * 100,
                                    'growth_speed': 8 + i * 2,
                                    'color': random.choice([(255, 200, 0), (255, 100, 0), (255, 255, 255)]),
                                    'thickness': 8 - i,
                                    'life': 180 - i * 20
                                }
                                self.boss_explosion_waves.append(wave)
                        else:
                            self.score += 10
                            self.add_xp(5, main_body_rect.centerx, main_body_rect.centery)
                        if bullet.pierce_hits > 0:
                            bullet.pierce_hits -= 1
            else:
                for enemy in self.enemies[:]:
                    if bullet.rect.colliderect(enemy.rect):
                        if bullet.pierce_hits <= 0:
                            self.player_bullets.remove(bullet)
                        # PLAY SMALL EXPLOSION SOUND
                        self.sound_manager.play_sound('explosion_small', volume_override=0.4)

                        # CREATE EXPLOSION BEFORE REMOVING ENEMY
                        explosion = EnemyExplosion(enemy.x + enemy.width // 2, enemy.y + enemy.height // 2, enemy.enemy_type)
                        self.enemy_explosions.append(explosion)

                        self.enemies.remove(enemy)
                        self.score += 10
                        self.total_enemies_killed += 1
                        self.add_xp(5, enemy.x + enemy.width // 2, enemy.y)
                        self.update_enemy_speed()
                        self.spawn_power_up(owner)
                        if bullet.pierce_hits > 0:
                            bullet.pierce_hits -= 1
                        break
                        
        # Laser vs enemies
        for laser in self.laser_beams:
            owner = next((p for p in self.players if p.player_id == laser.owner_player_id), None)
            if laser.is_active():
                if self.is_boss_level and self.current_boss and not self.current_boss.destruction_complete:
                    # Laser vs turrets
                    turret_rects = self.current_boss.get_turret_rects()
                    for turret_rect, turret_index in turret_rects:
                        if turret_rect and laser.rect.colliderect(turret_rect):
                            # Play UFO hit sound for laser turret hits (but limit frequency)
                            if pygame.time.get_ticks() % 200 == 0:  # Only every 200ms to avoid spam
                                self.sound_manager.play_sound('ufo_hit', volume_override=0.4)
                            if self.current_boss.take_turret_damage(turret_index, 2):  # Laser does more damage
                                self.score += 100
                                self.add_xp(20, turret_rect.centerx, turret_rect.centery)
                            else:
                                self.score += 10
                                self.add_xp(4, turret_rect.centerx, turret_rect.centery)
                    
                    # Laser vs main body
                    main_body_rect = self.current_boss.get_main_body_rect()
                    if main_body_rect and laser.rect.colliderect(main_body_rect):
                        # Play UFO hit sound for laser main body hits (but limit frequency)
                        if pygame.time.get_ticks() % 200 == 0:  # Only every 200ms to avoid spam
                            self.sound_manager.play_sound('ufo_hit', volume_override=0.6)
                        if self.current_boss.take_main_damage(3):  # Laser does lots of damage to main body
                            self.score += 1000
                            self.add_xp(200, main_body_rect.centerx, main_body_rect.centery)
                            self.grant_post_boss_shield()
                        else:
                            self.score += 15
                            self.add_xp(8, main_body_rect.centerx, main_body_rect.centery)
                else:
                    for enemy in self.enemies[:]:
                        if laser.rect.colliderect(enemy.rect):
                            # PLAY SMALL EXPLOSION SOUND
                            self.sound_manager.play_sound('explosion_small', volume_override=0.4)
                            # CREATE EXPLOSION BEFORE REMOVING ENEMY
                            explosion = EnemyExplosion(enemy.x + enemy.width // 2, enemy.y + enemy.height // 2, enemy.enemy_type)
                            self.enemy_explosions.append(explosion)

                            self.enemies.remove(enemy)
                            self.score += 10
                            self.total_enemies_killed += 1
                            self.add_xp(5, enemy.x + enemy.width // 2, enemy.y)
                            self.spawn_power_up(owner)
                            
        self.update_enemy_speed()
                        
        # Player bullets vs barriers
        for bullet in self.player_bullets[:]:
            # Barrier phasing bullets should ignore barrier collisions entirely
            if getattr(bullet, 'can_phase_barriers', False):
                continue
            for barrier in self.barriers:
                if barrier.check_collision(bullet.rect) and not getattr(bullet, 'can_phase_barriers', False):
                    self.player_bullets.remove(bullet)
                    break
                    
        # Enemy bullets vs barriers
        for bullet in self.enemy_bullets[:]:
            for barrier in self.barriers:
                if barrier.check_collision(bullet.rect):
                    self.enemy_bullets.remove(bullet)
                    break
                    
        # Power-ups vs players
        for power_up in self.power_ups[:]:
            for player in self.players:
                if player.is_alive and power_up.rect.colliderect(player.rect):
                    self.power_ups.remove(power_up)
                    self.sound_manager.play_sound('powerup', volume_override=0.7)
                    self.activate_power_up(player, power_up.power_type)
                    self.score += 50
                    self.add_xp(10, power_up.x, power_up.y)
                    break
                    
        # Enemy bullets vs players
        for bullet in self.enemy_bullets[:]:
            for player in self.players:
                if player.is_alive and bullet.rect.colliderect(player.rect):
                    if player.take_damage(self.sound_manager):
                        self.enemy_bullets.remove(bullet)
                        break
                    
    def restart_game(self):
        self.game_over = False
        self.awaiting_name_input = False
        self.awaiting_level_up = False
        self.pending_level_up = False
        if hasattr(self, 'name_input_screen'):
            del self.name_input_screen
        if hasattr(self, 'level_up_screen'):
            del self.level_up_screen
            
        self.score = 0
        self.level = 1
        self.total_enemies_killed = 0
        self.current_boss = None
        self.is_boss_level = False
        self.boss_shield_granted = False
        
        # Reset XP system
        self.xp_system = XPSystem()
        
        self.player_bullets = []
        self.enemy_bullets = []
        self.power_ups = []
        self.laser_beams = []
        self.floating_texts = []
        self.enemy_explosions = []
        self.boss_explosion_particles = []
        self.boss_explosion_particles = []
        self.screen_shake_intensity = 0
        self.screen_shake_duration = 0
        self.screen_flash_intensity = 0
        self.screen_flash_duration = 0
        self.boss_explosion_waves = []
        self.available_bosses = [Boss, AlienOverlordBoss]
        
        # Reset all players with new individual upgrades
        for player in self.players:
            player.lives = 3
            player.is_alive = True
            player.upgrades = PlayerUpgrades()  # Each player gets their own upgrades
            player.reset_position()
            player.clear_all_power_ups()
            player.invincible = False
            player.respawn_immunity = False
            player.afterimage_positions = []
        
        self.create_barriers()
        self.setup_level()
        
    def draw(self):
        # ADDED: Show UFO warning screen if active
        if self.showing_ufo_warning and self.ufo_warning_screen:
            self.ufo_warning_screen.draw()
            return
            
        self.screen.fill(BLACK)
        # SCREEN FLASH EFFECT - Apply early for maximum impact
        if self.screen_flash_intensity > 0:
            # Fill screen with bright color based on flash intensity
            flash_color = (min(255, self.screen_flash_intensity), 
                          min(255, self.screen_flash_intensity), 
                          min(255, self.screen_flash_intensity))
            self.screen.fill(flash_color)
        
        # Handle level up screen
        if self.awaiting_level_up:
            if not hasattr(self, 'level_up_screen'):
                self.level_up_screen = LevelUpScreen(self.screen, self.players, self.coop_mode, self.sound_manager, self.xp_system.level)
            self.level_up_screen.draw()
            return
        
        # Handle name input screen
        if self.awaiting_name_input and hasattr(self, 'name_input_screen'):
            self.name_input_screen.draw()
            return
        
        if not self.game_over:
            # Simple screen shake - just use a random background color pulse
            if self.screen_shake_intensity > 0:
                # Make the background flash red/orange during shake
                shake_color = (min(255, self.screen_shake_intensity * 3), 
                              min(255, self.screen_shake_intensity), 0)
                self.screen.fill(shake_color)
    
            for laser in self.laser_beams:
                laser.draw(self.screen)
                
            for player in self.players:
                player.draw(self.screen)
            
            for bullet in self.player_bullets:
                bullet.draw(self.screen)
                
            for bullet in self.enemy_bullets:
                bullet.draw(self.screen)
                
            # Draw boss or regular enemies
            if self.is_boss_level and self.current_boss:
                self.current_boss.draw(self.screen)
            else:
                for enemy in self.enemies:
                    enemy.draw(self.screen)

            # Draw enemy explosions
            for explosion in self.enemy_explosions:
                explosion.draw(self.screen)

            # Draw boss explosion particles
            for particle in self.boss_explosion_particles:
                if particle['life'] > 0:
                    alpha = max(0, min(255, particle['life'] // 3))
                    particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
                    color_with_alpha = (*particle['color'], alpha)
                    pygame.draw.circle(particle_surface, color_with_alpha, 
                                     (particle['size'], particle['size']), particle['size'])
                    self.screen.blit(particle_surface, (int(particle['x'] - particle['size']), 
                                                     int(particle['y'] - particle['size'])))
                
            for barrier in self.barriers:
                barrier.draw(self.screen)
                
            for power_up in self.power_ups:
                power_up.draw(self.screen)
            
            # Draw floating texts
            for text in self.floating_texts:
                text.draw(self.screen)
                
        # UI
        score_text = self.small_font.render(f"Score: {self.score:,}", True, WHITE)
        level_text = self.small_font.render(f"Level: {self.level}", True, WHITE)
        
        self.screen.blit(score_text, (20, 20))
        self.screen.blit(level_text, (20, 70))
        
        # FIXED: XP Bar - simplified, no overlapping text
        bar_width = 300
        bar_height = 20
        bar_x = SCREEN_WIDTH - bar_width - 20
        bar_y = 20
        
        # Background
        pygame.draw.rect(self.screen, GRAY, (bar_x, bar_y, bar_width, bar_height))
        
        # Progress
        progress = self.xp_system.get_xp_progress()
        progress_width = int(bar_width * progress)
        pygame.draw.rect(self.screen, GOLD, (bar_x, bar_y, progress_width, bar_height))
        
        # Border
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Only show XP level number - clean and simple
        xp_level_text = self.small_font.render(f"XP Level: {self.xp_system.level}", True, WHITE)
        self.screen.blit(xp_level_text, (bar_x, bar_y + bar_height + 10))
        
        # Player lives display - keep it simple and compact
        if self.coop_mode:
            lives_text1 = self.small_font.render(f"P1: {self.players[0].lives} lives {'(DEAD)' if not self.players[0].is_alive else ''}", True, GREEN if self.players[0].is_alive else RED)
            lives_text2 = self.small_font.render(f"P2: {self.players[1].lives} lives {'(DEAD)' if not self.players[1].is_alive else ''}", True, BLUE if self.players[1].is_alive else RED)
            self.screen.blit(lives_text1, (20, 120))
            self.screen.blit(lives_text2, (20, 160))
        else:
            if self.players:
                lives_text = self.small_font.render(f"Lives: {self.players[0].lives}", True, WHITE)
                self.screen.blit(lives_text, (20, 120))
        
        # Power-up status - very compact, right side
        active_powerups = []
        for player in self.players:
            if not player.is_alive:
                continue
            prefix = f"P{player.player_id}:" if self.coop_mode else ""
            if player.rapid_fire and player.rapid_fire_ammo > 0:
                active_powerups.append(f"{prefix}Rapid({player.rapid_fire_ammo})")
            if player.has_laser:
                active_powerups.append(f"{prefix}Laser")
            if player.has_multi_shot and player.multi_shot_ammo > 0:
                active_powerups.append(f"{prefix}Multi({player.multi_shot_ammo})")
            if player.invincible:
                time_left = (player.invincible_end_time - pygame.time.get_ticks()) / 1000
                active_powerups.append(f"{prefix}Invincible({time_left:.1f}s)")
        
        if active_powerups:
            powerup_text = " | ".join(active_powerups)
            text = self.tiny_font.render(powerup_text, True, ORANGE)
            self.screen.blit(text, (20, 200))
        
        # Game over screen
        if self.game_over and not self.awaiting_name_input:
            game_over_text = self.font.render("GAME OVER", True, RED)
            final_score_text = self.small_font.render(f"Final Score: {self.score:,}", True, WHITE)
            level_reached_text = self.small_font.render(f"Level Reached: {self.level}", True, WHITE)
            xp_level_text = self.small_font.render(f"XP Level Reached: {self.xp_system.level}", True, GOLD)
            
            # FIXED: Show input delay message or controls
            if pygame.time.get_ticks() - self.game_over_time < self.input_delay_duration:
                remaining = (self.input_delay_duration - (pygame.time.get_ticks() - self.game_over_time)) / 1000.0
                controls_text = self.small_font.render(f"Controls unlocking in {remaining:.1f}s...", True, YELLOW)
            else:
                controls_text = self.small_font.render("R/A: Restart | ESC/B: Title Menu", True, WHITE)
            
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
            score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40))
            level_rect = level_reached_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            xp_rect = xp_level_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))
            controls_rect = controls_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100))
            
            self.screen.blit(game_over_text, text_rect)
            self.screen.blit(final_score_text, score_rect)
            self.screen.blit(level_reached_text, level_rect)
            self.screen.blit(xp_level_text, xp_rect)
            self.screen.blit(controls_text, controls_rect)
            
        # FIXED: Instructions moved below XP bar to avoid overlap
        if not self.game_over:
            instructions = [
                "P1: WASD/Arrows + Space",
                "ESC: Return to title"
            ]
            if self.coop_mode:
                instructions.insert(1, "P2: Right Ctrl (or controller)")
                
            # Add boss level indicator
            if self.is_boss_level:
                instructions.append("BOSS LEVEL!")
                
            # Position instructions below the XP bar instead of overlapping it
            start_y = bar_y + bar_height + 50  # Start below XP level text
            for i, instruction in enumerate(instructions):
                color = RED if instruction == "BOSS LEVEL!" else WHITE
                text = self.small_font.render(instruction, True, color)
                # Position on right side but below XP bar
                self.screen.blit(text, (SCREEN_WIDTH - 400, start_y + i * 35))
        

            # INTENSE WHITE FLASH OVERLAY - This goes over everything for maximum effect
            if self.screen_flash_intensity > 0:
                flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                flash_surface.fill((255, 255, 255))
                flash_surface.set_alpha(self.screen_flash_intensity)
                self.screen.blit(flash_surface, (0, 0))
        
        pygame.display.flip()
        
    def run(self):
        result = None
        while self.running and not result:
            action = self.handle_events()
            if action == "restart":
                self.restart_game()
            elif action == "title":
                result = "title"
            else:
                if not self.awaiting_name_input and not self.awaiting_level_up:
                    self.handle_input()
                    self.update()
                self.draw()
                self.clock.tick(60)
                
        return result

def main():
    score_manager = HighScoreManager()
    
    # Initialize sound manager
    sound_manager = SoundManager()
    
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    except:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
    clock = pygame.time.Clock()
    
    while True:
        title_screen = TitleScreen(screen, score_manager, sound_manager)
        
        while True:
            action = title_screen.handle_events()
            if action == "quit":
                pygame.quit()
                sys.exit()
            elif action == "highscores":
                high_score_screen = HighScoreScreen(screen, score_manager, sound_manager)
                while True:
                    hs_action = high_score_screen.handle_events()
                    if hs_action == "back":
                        break
                    elif hs_action == "quit":
                        pygame.quit()
                        sys.exit()
                    high_score_screen.draw()
                    clock.tick(60)
                break
            elif action == "debug_menu":
                debug_menu = DebugMenu(screen, sound_manager)
                debug_action, debug_config = debug_menu.run()

                if debug_action == "quit":
                    pygame.quit()
                    sys.exit()
                elif debug_action == "start":
                    game_mode = debug_config.get('mode', 'single')
                    game = Game(score_manager, sound_manager)
                    game.setup_game(game_mode, debug_config)
                    result = game.run()

                    if result == "title":
                        break  # Go back to title screen
                    elif not result:
                        pygame.quit()
                        sys.exit()
                else:
                    break
            elif action in ["single", "coop"]:
                game = Game(score_manager, sound_manager)
                game.setup_game(action)
                result = game.run()
                
                if result == "title":
                    break  # Go back to title screen
                elif not result:
                    pygame.quit()
                    sys.exit()
            
            title_screen.draw()
            clock.tick(60)

if __name__ == "__main__":
    main()
