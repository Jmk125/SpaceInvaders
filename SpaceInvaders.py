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
GRAY = (80, 80, 80)
GOLD = (255, 215, 0)

# Game settings
BASE_PLAYER_SPEED = 8
BASE_BULLET_SPEED = 10
BASE_ENEMY_SPEED = 0.15
BASE_SHOOT_COOLDOWN = 300
ENEMY_DROP_SPEED = 30
RAPID_FIRE_COOLDOWN = 100
AUTO_FIRE_COOLDOWN = 150  # Cooldown for auto-fire powerup (faster than normal, slower than rapid fire)
AFTERIMAGE_INTERVAL = 80
RESPAWN_IMMUNITY_DURATION = 3000
BASE_LUCKY_DROP_CHANCE = 5  # Base percentage chance for powerup drops (affected by upgrades and co-op mode)

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

# Enemy In-Combat Speed Progression (as enemies are destroyed)
ENEMY_GRID_TOTAL = 60  # Total enemies in a standard grid (5 rows × 12 columns)

# --- LEGACY LINEAR PROGRESSION (used when USE_THRESHOLD_PROGRESSION = False) ---
ENEMY_SPEED_MULTIPLIER_MAX = 10  # Max speed multiplier when most enemies destroyed - 14 default
ENEMY_SPEED_FINAL_THRESHOLD = 5  # Number of remaining enemies to trigger extra speed boost
ENEMY_SPEED_FINAL_MULTIPLIER = 2  # Per-enemy multiplier when below threshold
ENEMY_SPEED_PROGRESSION_EXPONENT = 1.0  # Exponent for progression curve (1.0=linear, 2.0=quadratic, 0.5=sqrt)

# --- THRESHOLD-BASED PROGRESSION (used when USE_THRESHOLD_PROGRESSION = True) ---
# Gives you precise control over speed at specific enemy counts
# Format: List of (remaining_enemies, speed_multiplier) tuples
# The system will use the highest applicable multiplier based on remaining enemies
USE_THRESHOLD_PROGRESSION = True  # Set to True to use threshold-based system instead of formula-based
ENEMY_SPEED_THRESHOLDS = [
    (55, 1.0),   # 55+ enemies remaining: 1.0x base speed (no boost)
    (45, 1.5),   # 45-54 enemies: 1.5x base speed
    (35, 2.5),   # 35-44 enemies: 2.5x base speed
    (25, 4.0),   # 25-34 enemies: 4.0x base speed
    (15, 6.5),   # 15-24 enemies: 6.5x base speed
    (10, 9.0),   # 10-14 enemies: 9.0x base speed
    (5, 12.0),   # 5-9 enemies: 12.0x base speed
    (3, 16.0),   # 3-4 enemies: 16.0x base speed
    (1, 22.0),   # 1-2 enemies: 22.0x base speed (intense!)
]

# Per-Level Progression Configuration
# --- Enemy Speed Progression Between Levels ---
ENEMY_SPEED_PROGRESSION = 0.08  # How much speed increases per interval (moved from line 53 for clarity) - default 0.10
USE_BOSS_BASED_SPEED_PROGRESSION = True  # True = speed increases after each boss, False = increases every N levels
ENEMY_SPEED_LEVEL_INTERVAL = 5  # Enemy speed increases every N levels (only used when USE_BOSS_BASED_SPEED_PROGRESSION = False)

# --- Boss Scheduling ---
BOSS_FIRST_LEVEL = 4  # Level where first boss appears
BOSS_INITIAL_GAP = 4  # Gap before first boss (level 4)
BOSS_GAP_INCREMENT = 1  # Each subsequent boss requires N more levels (gap increases by 1)

# Alien Overlord Boss Configuration
ALIEN_BOSS_HEAD_HEALTH_BASE = 65
ALIEN_BOSS_HEAD_HEALTH_PER_LEVEL = 15
ALIEN_BOSS_HAND_HEALTH_BASE = 35
ALIEN_BOSS_HAND_HEALTH_PER_LEVEL = 10
ALIEN_BOSS_HAND_SPEED_BASE = 4.0
ALIEN_BOSS_HAND_SPEED_GROWTH = 0.35
ALIEN_BOSS_DROP_COOLDOWN_BASE = 4200  # ms between hand drops
ALIEN_BOSS_DROP_COOLDOWN_SCALE = 0.9  # Multiplier applied each encounter
ALIEN_BOSS_FIREBALL_COOLDOWN_BASE = 3100  # ms between fireballs
ALIEN_BOSS_FIREBALL_COOLDOWN_SCALE = 0.88

# Bullet Hell Boss Configuration
BULLET_HELL_BOSS_HEALTH_BASE = 70  # Base health
BULLET_HELL_BOSS_HEALTH_PER_LEVEL = 12  # Health increase per encounter
BULLET_HELL_BOSS_SPEED_BASE = 6  # Base movement speed (fast!)
BULLET_HELL_BOSS_SPEED_GROWTH = 0.4  # Speed increase per encounter
BULLET_HELL_BOSS_SHOT_COOLDOWN_BASE = 350  # ms between shots (very rapid!)
BULLET_HELL_BOSS_SHOT_COOLDOWN_SCALE = 0.92  # Multiplier applied each encounter (gets faster)
BULLET_HELL_BOSS_BULLET_SPEED = 1.8  # Speed of falling bullets (slow)
BULLET_HELL_BOSS_MOVEMENT_ZONE_TOP = 100  # Top of movement zone
BULLET_HELL_BOSS_MOVEMENT_ZONE_BOTTOM = 540  # Bottom of movement zone (half screen at 1080p)

# Asteroid Field Boss Configuration
ASTEROID_BOSS_HEALTH_BASE = 100  # Base health (asteroids that need to reach bottom)
ASTEROID_BOSS_HEALTH_PER_LEVEL = 20  # Health increase per encounter
ASTEROID_BOSS_SPAWN_COOLDOWN_BASE = 700  # ms between asteroid spawns (rapid!)
ASTEROID_BOSS_SPAWN_COOLDOWN_SCALE = 0.88  # Multiplier per encounter (spawns faster)
ASTEROID_BOSS_SPEED_BASE = 5.0  # Base falling speed
ASTEROID_BOSS_SPEED_GROWTH = 0.5  # Speed increase per encounter
ASTEROID_BOSS_SIZE_MULTIPLIER = 4.0  # Global size scale for all asteroids (tweak this!)
ASTEROID_BOSS_SIZE_MIN = 30  # Minimum asteroid size (before multiplier)
ASTEROID_BOSS_SIZE_MAX = 80  # Maximum asteroid size (before multiplier)
ASTEROID_BOSS_HEALTH_LOSS_PER_ASTEROID = 1  # Health lost when asteroid reaches bottom

# Rubik's Cube Boss Configuration
RUBIKS_BOSS_SQUARE_SIZE = 50  # Size of each small square (pixels)
RUBIKS_BOSS_GRID_SIZE = 7  # 7x7 grid (49 squares total)
RUBIKS_BOSS_SQUARE_HEALTH_PERCENTAGE = 0.10  # Small squares have 5% of center health (adjustable)
RUBIKS_BOSS_CENTER_HEALTH_BASE = 25  # Base health for center cube (adjustable, much higher) - 50 default
RUBIKS_BOSS_CENTER_HEALTH_PER_LEVEL = 15  # Health increase per encounter for center
RUBIKS_BOSS_ROTATION_SPEED_BASE = 30  # Degrees per second (adjustable)
RUBIKS_BOSS_ROTATION_SPEED_GROWTH = 5  # Rotation speed increase per encounter (degrees/sec)
RUBIKS_BOSS_SPEED_BASE = 2.5  # Left/right movement speed (increased from 1.5)
RUBIKS_BOSS_MIXED_PHASE_DURATION = 5000  # Mixed colors phase duration (ms)
RUBIKS_BOSS_ATTACK_PHASE_DURATION = 10000  # Single color attack phase duration (ms)
RUBIKS_BOSS_RED_SHOOT_COOLDOWN = 1000  # Red spinning squares shoot interval (ms, adjustable)
RUBIKS_BOSS_BLUE_SHOOT_COOLDOWN = 250  # Blue rapid fire interval (ms)
RUBIKS_BOSS_YELLOW_SHOOT_COOLDOWN = 300  # Yellow slow balls interval (ms)
RUBIKS_BOSS_ORANGE_SHOOT_COOLDOWN = 50  # Orange rotating fireballs interval (ms, adjustable)
RUBIKS_BOSS_ORANGE_ROTATION_SPEED = 720  # Rotation speed during orange attack (degrees/sec, adjustable)
RUBIKS_BOSS_ORANGE_FIREBALL_RADIUS = 27  # Orange fireball radius (pixels, adjustable)
RUBIKS_BOSS_WHITE_SHOOT_COOLDOWN = 3000  # White bouncing ball interval (ms)

# High scores files
SINGLE_SCORES_FILE = "high_scores_single.json"
COOP_SCORES_FILE = "high_scores_coop.json"

# Starfield Configuration
STAR_COUNT_PER_LAYER = 100  # Number of stars per layer
STAR_SIZE_MIN = 1  # Minimum star size
STAR_SIZE_MAX = 3  # Maximum star size

# Layer 1 (Back/Darkest/Slowest)
STAR_LAYER1_BRIGHTNESS = 80  # Darkest (0-255)
STAR_LAYER1_SPEED = 0.6  # Slowest parallax speed

# Layer 2 (Middle)
STAR_LAYER2_BRIGHTNESS = 150  # Medium brightness
STAR_LAYER2_SPEED = 1.2  # Medium parallax speed

# Layer 3 (Front/Brightest/Fastest)
STAR_LAYER3_BRIGHTNESS = 255  # Brightest (closest)
STAR_LAYER3_SPEED = 2.0  # Fastest parallax speed

# Controller hat bindings
HAT_LEFT = "hat_left"
HAT_RIGHT = "hat_right"
HAT_UP = "hat_up"
HAT_DOWN = "hat_down"

# Controller axis bindings (for arcade joysticks and analog sticks)
AXIS_LEFT = "axis_left"
AXIS_RIGHT = "axis_right"
AXIS_UP = "axis_up"
AXIS_DOWN = "axis_down"


class ProfileManager:
    """Manages control profiles with save/load functionality"""
    def __init__(self, filename="control_profiles.json"):
        self.filename = filename
        self.profiles = {}
        self.last_profile = None
        self.load_profiles()

    def get_default_bindings(self):
        """Get default key bindings"""
        return {
            'player1_fire_key': pygame.K_SPACE,
            'player1_left_key': pygame.K_LEFT,
            'player1_right_key': pygame.K_RIGHT,
            'player2_fire_key': pygame.K_RCTRL,
            'player2_left_key': pygame.K_a,
            'player2_right_key': pygame.K_d,
            'player1_left_button': HAT_LEFT,
            'player1_right_button': HAT_RIGHT,
            'player1_up_button': HAT_UP,
            'player1_down_button': HAT_DOWN,
            'player1_fire_button': 0,  # A button
            'player2_left_button': HAT_LEFT,
            'player2_right_button': HAT_RIGHT,
            'player2_up_button': HAT_UP,
            'player2_down_button': HAT_DOWN,
            'player2_fire_button': 0  # A button
        }

    def load_profiles(self):
        """Load profiles from file"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    self.last_profile = data.get('last_profile', None)
                    # Load profiles and convert key codes back to integers
                    saved_profiles = data.get('profiles', {})
                    for profile_name, bindings in saved_profiles.items():
                        self.profiles[profile_name] = bindings
        except Exception as e:
            print(f"Error loading profiles: {e}")
            self.profiles = {}
            self.last_profile = None

    def save_profiles(self):
        """Save profiles to file"""
        try:
            data = {
                'last_profile': self.last_profile,
                'profiles': self.profiles
            }
            with open(self.filename, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving profiles: {e}")

    def save_profile(self, name, bindings):
        """Save a new profile"""
        self.profiles[name] = bindings.copy()
        self.last_profile = name
        self.save_profiles()

    def get_profile(self, name):
        """Get a profile by name"""
        profile = self.profiles.get(name, None)
        if profile:
            # Merge with defaults to ensure all keys exist (backward compatibility)
            defaults = self.get_default_bindings()
            defaults.update(profile)
            return defaults
        return None

    def delete_profile(self, name):
        """Delete a profile"""
        if name in self.profiles:
            del self.profiles[name]
            if self.last_profile == name:
                self.last_profile = None
            self.save_profiles()

    def get_profile_names(self):
        """Get list of all profile names"""
        return list(self.profiles.keys())

    def get_last_profile_bindings(self):
        """Get bindings from last used profile, or defaults"""
        if self.last_profile and self.last_profile in self.profiles:
            # Merge with defaults to ensure all keys exist (backward compatibility)
            defaults = self.get_default_bindings()
            defaults.update(self.profiles[self.last_profile])
            return defaults
        return self.get_default_bindings()


class StarField:
    """
    Three-layer starfield with parallax scrolling effect.
    Each layer has different brightness to create depth without size variation.
    Parallax scrolling is activated during specific boss levels (e.g., Asteroid Field).
    """
    def __init__(self, direction='vertical'):
        """
        Initialize starfield with a scrolling direction.

        Args:
            direction: 'vertical' for downward scrolling, 'horizontal' for right-to-left scrolling
        """
        self.direction = direction

        # Layer configuration: (brightness, speed, star_count)
        self.layers = [
            {
                'brightness': STAR_LAYER1_BRIGHTNESS,
                'speed': STAR_LAYER1_SPEED,
                'count': STAR_COUNT_PER_LAYER,
                'stars': []
            },
            {
                'brightness': STAR_LAYER2_BRIGHTNESS,
                'speed': STAR_LAYER2_SPEED,
                'count': STAR_COUNT_PER_LAYER,
                'stars': []
            },
            {
                'brightness': STAR_LAYER3_BRIGHTNESS,
                'speed': STAR_LAYER3_SPEED,
                'count': STAR_COUNT_PER_LAYER,
                'stars': []
            }
        ]

        # Generate stars for each layer
        for layer in self.layers:
            for _ in range(layer['count']):
                star = {
                    'x': random.randint(0, SCREEN_WIDTH),
                    'y': random.randint(0, SCREEN_HEIGHT),
                    'size': random.randint(STAR_SIZE_MIN, STAR_SIZE_MAX)
                }
                layer['stars'].append(star)

    def update(self, parallax_active=False):
        """
        Update star positions. If parallax_active is True, stars move based on direction
        at different speeds based on their layer (creating parallax effect).
        """
        if parallax_active:
            for layer in self.layers:
                for star in layer['stars']:
                    if self.direction == 'horizontal':
                        # Move star left (right to left) based on layer speed
                        star['x'] -= layer['speed']

                        # Wrap around when star goes off left side of screen
                        if star['x'] < 0:
                            star['x'] = SCREEN_WIDTH
                            star['y'] = random.randint(0, SCREEN_HEIGHT)
                    else:
                        # Move star downward based on layer speed
                        star['y'] += layer['speed']

                        # Wrap around when star goes off bottom of screen
                        if star['y'] > SCREEN_HEIGHT:
                            star['y'] = 0
                            star['x'] = random.randint(0, SCREEN_WIDTH)

    def draw(self, screen):
        """Draw all three layers of stars with their respective brightness levels."""
        for layer in self.layers:
            # Create color based on brightness (grayscale)
            brightness = layer['brightness']
            color = (brightness, brightness, brightness)

            # Draw each star in the layer
            for star in layer['stars']:
                pygame.draw.circle(screen, color,
                                 (int(star['x']), int(star['y'])),
                                 star['size'])


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
        self.boss_shield_level = 0
        self.reinforced_barriers_level = 0
        self.auto_fire_level = 0
        
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
        elif stat == "boss_shield":
            max_levels = 1
        elif stat == "reinforced_barriers":
            max_levels = 2  # Stackable twice (2 hits -> 3 hits)
        elif stat == "auto_fire":
            max_levels = 1  # One-time upgrade
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
        if stat == "boss_shield":
            return 1.0
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

    def get_barrier_reinforcement_level(self):
        """Returns the barrier reinforcement level (0-2), which adds extra hits needed to break barrier blocks"""
        return self.reinforced_barriers_level

    def has_auto_fire(self):
        """Check if auto-fire upgrade is active"""
        return self.auto_fire_level > 0


class PlayerStats:
    """Track detailed player statistics for game over screen"""
    def __init__(self, player_id=1):
        self.player_id = player_id

        # Combat stats
        self.enemies_killed = 0
        self.shots_fired_total = 0
        self.shots_fired_normal = 0
        self.shots_fired_rapid = 0
        self.shots_fired_laser = 0
        self.shots_fired_multi = 0

        # Power-up stats
        self.invincibility_time = 0  # Total time in milliseconds
        self.invincibility_start_time = None  # Track when invincibility started

        # Permanent upgrades used (list of upgrade names)
        self.permanent_upgrades_used = []

        # Survival stats
        self.deaths = 0

        # Boss stats
        self.boss_damage_dealt = 0
        self.bosses_fought_count = 0
        self.bosses_fought_names = []  # List of boss names

        # Score and XP
        self.final_score = 0
        self.final_xp_level = 0
        self.final_xp = 0

    def record_shot(self, shot_type='normal'):
        """Record a shot fired"""
        self.shots_fired_total += 1
        if shot_type == 'rapid':
            self.shots_fired_rapid += 1
        elif shot_type == 'laser':
            self.shots_fired_laser += 1
        elif shot_type == 'multi':
            self.shots_fired_multi += 1
        else:
            self.shots_fired_normal += 1

    def record_enemy_kill(self):
        """Record an enemy killed"""
        self.enemies_killed += 1

    def start_invincibility(self):
        """Start tracking invincibility time"""
        if self.invincibility_start_time is None:
            self.invincibility_start_time = pygame.time.get_ticks()

    def end_invincibility(self):
        """End tracking invincibility time"""
        if self.invincibility_start_time is not None:
            duration = pygame.time.get_ticks() - self.invincibility_start_time
            self.invincibility_time += duration
            self.invincibility_start_time = None

    def record_death(self):
        """Record a player death"""
        self.deaths += 1
        # If player dies while invincible, end the tracking
        if self.invincibility_start_time is not None:
            self.end_invincibility()

    def record_boss_damage(self, damage):
        """Record damage dealt to boss"""
        self.boss_damage_dealt += damage

    def record_boss_encounter(self, boss_name):
        """Record a boss encounter"""
        if boss_name not in self.bosses_fought_names:
            self.bosses_fought_names.append(boss_name)
            self.bosses_fought_count = len(self.bosses_fought_names)

    def add_permanent_upgrade(self, upgrade_name):
        """Add a permanent upgrade to the list"""
        if upgrade_name not in self.permanent_upgrades_used:
            self.permanent_upgrades_used.append(upgrade_name)

    def set_final_stats(self, score, xp_level, xp):
        """Set final score and XP stats"""
        self.final_score = score
        self.final_xp_level = xp_level
        self.final_xp = xp
        # End invincibility tracking if still active
        if self.invincibility_start_time is not None:
            self.end_invincibility()

    def get_invincibility_seconds(self):
        """Get total invincibility time in seconds"""
        total_time = self.invincibility_time
        # Add current invincibility session if active
        if self.invincibility_start_time is not None:
            total_time += pygame.time.get_ticks() - self.invincibility_start_time
        return total_time / 1000.0


class FloatingText:
    def __init__(self, x, y, text, color=YELLOW, duration=1000):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 16)
        
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
    def __init__(self, screen, players, is_coop=False, sound_manager=None, xp_level=1, game_level=1, score=0, key_bindings=None):
        self.screen = screen
        self.players = players
        self.is_coop = is_coop
        self.sound_manager = sound_manager
        self.key_bindings = key_bindings if key_bindings else {}
        self.xp_level = xp_level
        self.game_level = game_level
        self.score = score
        self.font_large = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 36)
        self.font_medium = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 24)
        self.font_small = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 20)
        self.tiny_font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 16)

        # Track last permanent powerup per player to prevent repeats
        self.last_permanent_powerup = {}

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
            ("extra_bullet", "Twin Shot", "Add +1 bullet to every shot (one time)"),
            ("boss_shield", "Boss Shield", "Regenerate a shield after each boss"),
            ("reinforced_barriers", "Reinforced Barriers", "Barriers take +1 hit before breaking (stacks to 2)"),
            ("auto_fire", "Auto Fire", "Hold fire button for continuous shooting")
        ]

        self.player_options = []
        for player in self.players:
            options = list(self.base_upgrade_options)
            if self.xp_level % 5 == 0:
                options.append(("extra_life", "Extra Life", "Gain +1 life instead of a stat upgrade"))
                permanent_choice = self.get_random_permanent_option(player)
                if permanent_choice:
                    options.append(permanent_choice)
            # Always add Save & Quit option
            options.append(("save_and_quit", "Save & Quit", "Save your progress and return to title screen"))
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

        # Filter out the last permanent powerup for this player to prevent consecutive repeats
        last_powerup = self.last_permanent_powerup.get(player.player_id)
        if last_powerup:
            filtered_options = [opt for opt in options if opt[0] != last_powerup]
            # If all options are filtered out (only one option available), use all
            if filtered_options:
                options = filtered_options

        choice = random.choice(options)
        # Track this choice for next time
        self.last_permanent_powerup[player.player_id] = choice[0]
        return choice

    def get_options_for_player(self, player_index):
        if 0 <= player_index < len(self.player_options):
            return self.player_options[player_index]
        return self.upgrade_options

    def get_option_at(self, player_index, row_index):
        options = self.get_options_for_player(player_index)
        if 0 <= row_index < len(options):
            return options[row_index]
        return None

    def all_options_maxed(self, player_index):
        """Check if all available options for a player are maxed out"""
        if player_index >= len(self.players):
            return False
        player = self.players[player_index]
        options = self.get_options_for_player(player_index)

        for stat_name, _, _ in options:
            # Extra life, boss_shield, and save_and_quit are always available when shown
            if stat_name in ["extra_life", "boss_shield", "save_and_quit"]:
                return False
            # If any stat can be upgraded, not all maxed
            if player.upgrades.can_upgrade(stat_name):
                return False
        # All stats are maxed
        return True

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
                        if stat_name == "save_and_quit":
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_select')
                            return "save_and_quit"
                        elif stat_name == "extra_life":
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_select')
                            self.grant_extra_life(0, stat_name)
                            self.countdown_start = pygame.time.get_ticks()
                            self.countdown_duration = 2000
                        elif stat_name == "boss_shield":
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_select')
                            self.grant_boss_shield_upgrade(0, stat_name)
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
                        elif self.all_options_maxed(0):
                            # All options are maxed - allow player to continue
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_select')
                            self.countdown_start = pygame.time.get_ticks()
                            self.countdown_duration = 2000
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
                            if stat_name == "save_and_quit":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                return "save_and_quit"
                            elif stat_name == "extra_life":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                self.grant_extra_life(0, stat_name)
                                self.player1_confirmed = True
                            elif stat_name == "boss_shield":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                self.grant_boss_shield_upgrade(0, stat_name)
                                self.player1_confirmed = True
                            elif self.players[0].upgrades.can_upgrade(stat_name):
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                old_multiplier = self.players[0].upgrades.get_multiplier(stat_name)
                                self.players[0].upgrades.upgrade_stat(stat_name)
                                new_multiplier = self.players[0].upgrades.get_multiplier(stat_name)
                                self.create_upgrade_effect(0, stat_name, old_multiplier, new_multiplier)
                                self.player1_confirmed = True
                            elif self.all_options_maxed(0):
                                # All options are maxed - allow player to continue
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
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
                            if stat_name == "save_and_quit":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                return "save_and_quit"
                            elif stat_name == "extra_life":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                self.grant_extra_life(1, stat_name)
                                self.player2_confirmed = True
                            elif stat_name == "boss_shield":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                self.grant_boss_shield_upgrade(1, stat_name)
                                self.player2_confirmed = True
                            elif self.players[1].upgrades.can_upgrade(stat_name):
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                old_multiplier = self.players[1].upgrades.get_multiplier(stat_name)
                                self.players[1].upgrades.upgrade_stat(stat_name)
                                new_multiplier = self.players[1].upgrades.get_multiplier(stat_name)
                                self.create_upgrade_effect(1, stat_name, old_multiplier, new_multiplier)
                                self.player2_confirmed = True
                            elif self.all_options_maxed(1):
                                # All options are maxed - allow player to continue
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                self.player2_confirmed = True
                    
                    # Check if both players confirmed - start countdown
                    if self.player1_confirmed and self.player2_confirmed and self.countdown_start is None:
                        self.countdown_start = pygame.time.get_ticks()
                        
            elif event.type == pygame.JOYBUTTONDOWN:
                if not self.is_coop:
                    # Single player controller
                    fire_button = self.key_bindings.get('player1_fire_button', 0)
                    if isinstance(fire_button, int) and event.button == fire_button:
                        options = self.get_options_for_player(0)
                        stat_name = options[self.current_selection][0]
                        if stat_name == "save_and_quit":
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_select')
                            return "save_and_quit"
                        elif stat_name == "extra_life":
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_select')
                            self.grant_extra_life(0, stat_name)
                            self.countdown_start = pygame.time.get_ticks()
                            self.countdown_duration = 2000
                        elif stat_name == "boss_shield":
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_select')
                            self.grant_boss_shield_upgrade(0, stat_name)
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
                        elif self.all_options_maxed(0):
                            # All options are maxed - allow player to continue
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_select')
                            self.countdown_start = pygame.time.get_ticks()
                            self.countdown_duration = 2000
                else:
                    # Co-op controller handling
                    if len(self.controllers) > 0 and event.joy == 0 and not self.player1_confirmed:
                        fire_button = self.key_bindings.get('player1_fire_button', 0)
                        if isinstance(fire_button, int) and event.button == fire_button:
                            p1_options = self.get_options_for_player(0)
                            stat_name = p1_options[self.player1_selection][0]
                            if stat_name == "save_and_quit":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                return "save_and_quit"
                            elif stat_name == "extra_life":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                self.grant_extra_life(0, stat_name)
                                self.player1_confirmed = True
                            elif stat_name == "boss_shield":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                self.grant_boss_shield_upgrade(0, stat_name)
                                self.player1_confirmed = True
                            elif self.players[0].upgrades.can_upgrade(stat_name):
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                old_multiplier = self.players[0].upgrades.get_multiplier(stat_name)
                                self.players[0].upgrades.upgrade_stat(stat_name)
                                new_multiplier = self.players[0].upgrades.get_multiplier(stat_name)
                                self.create_upgrade_effect(0, stat_name, old_multiplier, new_multiplier)
                                self.player1_confirmed = True
                            elif self.all_options_maxed(0):
                                # All options are maxed - allow player to continue
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                self.player1_confirmed = True

                    if len(self.controllers) > 1 and event.joy == 1 and not self.player2_confirmed:
                        fire_button = self.key_bindings.get('player2_fire_button', 0)
                        if isinstance(fire_button, int) and event.button == fire_button:
                            p2_options = self.get_options_for_player(1)
                            stat_name = p2_options[self.player2_selection][0]
                            if stat_name == "save_and_quit":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                return "save_and_quit"
                            elif stat_name == "extra_life":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                self.grant_extra_life(1, stat_name)
                                self.player2_confirmed = True
                            elif stat_name == "boss_shield":
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                self.grant_boss_shield_upgrade(1, stat_name)
                                self.player2_confirmed = True
                            elif self.players[1].upgrades.can_upgrade(stat_name):
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
                                old_multiplier = self.players[1].upgrades.get_multiplier(stat_name)
                                self.players[1].upgrades.upgrade_stat(stat_name)
                                new_multiplier = self.players[1].upgrades.get_multiplier(stat_name)
                                self.create_upgrade_effect(1, stat_name, old_multiplier, new_multiplier)
                                self.player2_confirmed = True
                            elif self.all_options_maxed(1):
                                # All options are maxed - allow player to continue
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_select')
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

            elif event.type == pygame.JOYAXISMOTION:
                # Support joystick axis for menu navigation
                threshold = 0.5
                if not self.is_coop:
                    # Single player controller
                    if event.axis == 1:  # Y-axis
                        if event.value < -threshold:  # Up
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_change')
                            options = self.get_options_for_player(0)
                            self.current_selection = (self.current_selection - 1) % len(options)
                        elif event.value > threshold:  # Down
                            if self.sound_manager:
                                self.sound_manager.play_sound('menu_change')
                            options = self.get_options_for_player(0)
                            self.current_selection = (self.current_selection + 1) % len(options)
                else:
                    # Co-op controller handling
                    if len(self.controllers) > 0 and event.joy == 0 and not self.player1_confirmed:
                        if event.axis == 1:  # Y-axis
                            if event.value < -threshold:  # Up
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_change')
                                p1_options = self.get_options_for_player(0)
                                self.player1_selection = (self.player1_selection - 1) % len(p1_options)
                            elif event.value > threshold:  # Down
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_change')
                                p1_options = self.get_options_for_player(0)
                                self.player1_selection = (self.player1_selection + 1) % len(p1_options)

                    if len(self.controllers) > 1 and event.joy == 1 and not self.player2_confirmed:
                        if event.axis == 1:  # Y-axis
                            if event.value < -threshold:  # Up
                                if self.sound_manager:
                                    self.sound_manager.play_sound('menu_change')
                                p2_options = self.get_options_for_player(1)
                                self.player2_selection = (self.player2_selection - 1) % len(p2_options)
                            elif event.value > threshold:  # Down
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

    def grant_boss_shield_upgrade(self, player_index, stat_name):
        """Unlock the post-boss shield reward"""
        player = self.players[player_index]
        player.unlock_boss_shield()
        player.upgrades.boss_shield_level = 1
        x, y = self.get_effect_position(player_index, stat_name)

        effect = {
            'x': x,
            'y': y,
            'text': "BOSS SHIELD",
            'color': CYAN,
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

        # Display stats (game level, player level, score)
        stats_y = 140
        game_level_text = self.tiny_font.render(f"Game Level: {self.game_level}", True, CYAN)
        player_level_text = self.tiny_font.render(f"Player Level: {self.xp_level}", True, CYAN)
        score_text = self.tiny_font.render(f"Score: {self.score:,}", True, CYAN)

        game_level_rect = game_level_text.get_rect(center=(SCREEN_WIDTH // 2 - 300, stats_y))
        player_level_rect = player_level_text.get_rect(center=(SCREEN_WIDTH // 2, stats_y))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2 + 300, stats_y))

        self.screen.blit(game_level_text, game_level_rect)
        self.screen.blit(player_level_text, player_level_rect)
        self.screen.blit(score_text, score_rect)

        # Input delay indicator
        if pygame.time.get_ticks() - self.start_time < self.input_delay:
            remaining = (self.input_delay - (pygame.time.get_ticks() - self.start_time)) / 1000.0
            delay_text = self.font_medium.render(f"Input unlocks in {remaining:.1f}s", True, YELLOW)
            delay_rect = delay_text.get_rect(center=(SCREEN_WIDTH // 2, 180))
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
                elif p1_stat_name == "save_and_quit":
                    # No stats needed for save and quit option
                    if self.player1_confirmed and i == self.player1_selection:
                        confirm_text = self.tiny_font.render("✓ SELECTED", True, GREEN)
                        self.screen.blit(confirm_text, confirm_text.get_rect(topleft=(left_col_x - 70, y + 25)))
                elif p1_option:
                    if p1_stat_name == "boss_shield":
                        p1_color = WHITE if self.players[0].upgrades.can_upgrade(p1_stat_name) else GRAY
                        p1_status = "Unlocked" if self.players[0].upgrades.boss_shield_level > 0 else "Locked"
                        if self.player1_confirmed and i == self.player1_selection:
                            confirm_text = self.tiny_font.render("✓ SELECTED", True, GREEN)
                            self.screen.blit(confirm_text, confirm_text.get_rect(topleft=(left_col_x - 70, y + 25)))
                        else:
                            p1_status_text = self.tiny_font.render(p1_status, True, p1_color)
                            self.screen.blit(p1_status_text, p1_status_text.get_rect(topleft=(left_col_x - 70, y + 25)))
                        continue
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
                elif p2_stat_name == "save_and_quit":
                    # No stats needed for save and quit option
                    if self.player2_confirmed and i == self.player2_selection:
                        confirm_text = self.tiny_font.render("✓ SELECTED", True, BLUE)
                        confirm_rect = confirm_text.get_rect()
                        confirm_rect.topleft = (right_col_x - 70, y + 25)
                        self.screen.blit(confirm_text, confirm_rect)
                elif p2_option:
                    if p2_stat_name == "boss_shield":
                        p2_color = WHITE if self.players[1].upgrades.can_upgrade(p2_stat_name) else GRAY
                        p2_status = "Unlocked" if self.players[1].upgrades.boss_shield_level > 0 else "Locked"
                        if self.player2_confirmed and i == self.player2_selection:
                            confirm_text = self.tiny_font.render("✓ SELECTED", True, BLUE)
                            confirm_rect = confirm_text.get_rect()
                            confirm_rect.topleft = (right_col_x - 70, y + 25)
                            self.screen.blit(confirm_text, confirm_rect)
                        else:
                            p2_status_text = self.tiny_font.render(p2_status, True, p2_color)
                            self.screen.blit(p2_status_text, p2_status_text.get_rect(topleft=(right_col_x - 70, y + 25)))
                        continue
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
                elif stat_name == "save_and_quit":
                    # No stats needed for save and quit option
                    pass
                else:
                    if stat_name == "boss_shield":
                        can_upgrade = self.players[0].upgrades.can_upgrade(stat_name)
                        status = "Unlocked" if self.players[0].upgrades.boss_shield_level > 0 else "Locked"
                        status_text = self.tiny_font.render(status, True, WHITE if can_upgrade else GRAY)
                        self.screen.blit(status_text, status_text.get_rect(topleft=(panel_margin_x + 40, y + 50)))
                        continue
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

class SlowFallingBullet:
    """Slow-falling bullet for the Bullet Hell Boss"""
    def __init__(self, x, y, speed):
        self.x = x
        self.y = y
        self.width = 12
        self.height = 16
        self.speed = speed  # Slow downward speed
        self.rect = pygame.Rect(int(self.x - self.width // 2), int(self.y - self.height // 2), self.width, self.height)

    def move(self):
        self.y += self.speed  # Only moves downward
        self.rect.x = int(self.x - self.width // 2)
        self.rect.y = int(self.y - self.height // 2)

    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT + 30

    def draw(self, screen):
        # Draw as a glowing cyan/purple bullet
        center = (int(self.x), int(self.y))
        # Outer glow
        pygame.draw.circle(screen, (150, 100, 255), center, 8)
        # Middle layer
        pygame.draw.circle(screen, (200, 150, 255), center, 6)
        # Inner core
        pygame.draw.circle(screen, (255, 200, 255), center, 4)
        # Bright center
        pygame.draw.circle(screen, WHITE, center, 2)

class SpinningRedSquare:
    """Spinning red square projectile for Rubik's Cube Boss red attack - same size as boss squares"""
    def __init__(self, x, y, target_x, target_y, speed):
        self.x = x
        self.y = y
        self.width = 50  # Same size as boss squares
        self.height = 50
        self.speed = speed
        self.rotation = 0  # Current rotation angle
        self.rotation_speed = 10  # Degrees per frame

        # Calculate velocity toward target
        dx = target_x - x
        dy = target_y - y
        distance = math.hypot(dx, dy) or 1
        self.vel_x = (dx / distance) * speed
        self.vel_y = (dy / distance) * speed
        self.rect = pygame.Rect(int(self.x - self.width // 2), int(self.y - self.height // 2), self.width, self.height)

        # Afterimage tracking
        self.afterimage_positions = []
        self.last_afterimage_time = pygame.time.get_ticks()

    def move(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.rotation = (self.rotation + self.rotation_speed) % 360
        self.rect.x = int(self.x - self.width // 2)
        self.rect.y = int(self.y - self.height // 2)

        # Record afterimage positions
        current_time = pygame.time.get_ticks()
        if current_time - self.last_afterimage_time >= AFTERIMAGE_INTERVAL:
            self.afterimage_positions.append((self.x, self.y, self.rotation, current_time))
            self.last_afterimage_time = current_time

        # Clean up old afterimages (keep only those less than 500ms old)
        self.afterimage_positions = [(x, y, rot, t) for x, y, rot, t in self.afterimage_positions
                                     if current_time - t < 500]

    def is_off_screen(self):
        return (self.x < -100 or self.x > SCREEN_WIDTH + 100 or
                self.y < -100 or self.y > SCREEN_HEIGHT + 100)

    def draw(self, screen):
        # Draw afterimages first (behind the main square)
        current_time = pygame.time.get_ticks()
        for x, y, rotation, timestamp in self.afterimage_positions:
            age = current_time - timestamp
            alpha = max(0, 255 - (age * 255 // 500))

            # Create afterimage surface with red color and alpha
            afterimage_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(afterimage_surface, (255, 0, 0, alpha), (0, 0, self.width, self.height))
            pygame.draw.rect(afterimage_surface, (180, 0, 0, alpha), (4, 4, self.width - 8, self.height - 8))

            # Rotate the afterimage
            rotated_afterimage = pygame.transform.rotate(afterimage_surface, rotation)
            afterimage_rect = rotated_afterimage.get_rect(center=(int(x), int(y)))
            screen.blit(rotated_afterimage, afterimage_rect.topleft)

        # Create a rotating red square (main projectile)
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(surface, (255, 0, 0), (0, 0, self.width, self.height))
        pygame.draw.rect(surface, (180, 0, 0), (4, 4, self.width - 8, self.height - 8))
        # Draw black border
        pygame.draw.rect(surface, (0, 0, 0), (0, 0, self.width, self.height), 2)

        # Rotate the surface
        rotated = pygame.transform.rotate(surface, self.rotation)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotated, rect.topleft)

class BlueBullet:
    """Blue rapid-fire bullet for Rubik's Cube Boss blue attack"""
    def __init__(self, x, y, target_x, target_y, speed):
        self.x = x
        self.y = y
        self.width = 10
        self.height = 10
        self.speed = speed

        # Calculate velocity toward target
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
        return (self.x < -30 or self.x > SCREEN_WIDTH + 30 or
                self.y < -30 or self.y > SCREEN_HEIGHT + 30)

    def draw(self, screen):
        center = (int(self.x), int(self.y))
        pygame.draw.circle(screen, (0, 100, 255), center, 5)
        pygame.draw.circle(screen, (100, 180, 255), center, 3)

class GreenLaser:
    """Green laser beam for Rubik's Cube Boss green attack"""
    def __init__(self, boss, duration):
        self.boss = boss  # Reference to boss to track movement
        self.width = 15  # Width of the laser beam
        self.duration = duration  # How long the laser stays active (ms)
        self.start_time = pygame.time.get_ticks()
        self.update_rect()

    def update_rect(self):
        """Update rect position based on boss center"""
        center_x = self.boss.center_x
        center_y = self.boss.center_y
        # Laser starts from center of boss and goes to bottom of screen
        laser_height = SCREEN_HEIGHT - center_y
        self.rect = pygame.Rect(int(center_x - self.width // 2), int(center_y), self.width, int(laser_height))

    def move(self):
        # Update position to follow boss
        self.update_rect()

    def is_off_screen(self):
        # Check if duration expired
        current_time = pygame.time.get_ticks()
        return (current_time - self.start_time) > self.duration

    def draw(self, screen):
        # Get current boss center position
        center_x = self.boss.center_x
        center_y = self.boss.center_y

        # Calculate laser height from center to bottom
        laser_height = SCREEN_HEIGHT - center_y

        # Flashing effect - alternate between bright and dim green
        current_time = pygame.time.get_ticks()
        flash_cycle = (current_time // 100) % 2  # Flash every 100ms

        if flash_cycle == 0:
            # Bright flash
            main_color = (0, 255, 0)
            core_color = (200, 255, 200)
            glow_alpha = 100
        else:
            # Dim
            main_color = (0, 180, 0)
            core_color = (100, 220, 100)
            glow_alpha = 50

        # Draw green laser beam from center cube downward
        laser_rect = pygame.Rect(int(center_x - self.width // 2), int(center_y), self.width, int(laser_height))

        # Outer glow
        glow_rect = pygame.Rect(int(center_x - self.width // 2 - 5), int(center_y), self.width + 10, int(laser_height))
        glow_surface = pygame.Surface((self.width + 10, int(laser_height)), pygame.SRCALPHA)
        glow_surface.fill((*main_color, glow_alpha))
        screen.blit(glow_surface, (int(center_x - self.width // 2 - 5), int(center_y)))

        # Main beam
        pygame.draw.rect(screen, main_color, laser_rect)

        # Inner bright core
        core_rect = pygame.Rect(int(center_x - self.width // 4), int(center_y), self.width // 2, int(laser_height))
        pygame.draw.rect(screen, core_color, core_rect)

        # Draw marker at top of laser (where it originates from center cube) for debugging
        pygame.draw.circle(screen, (255, 0, 0), (int(center_x), int(center_y)), 5)  # Red dot at laser origin

class YellowBall:
    """Slow-falling yellow ball for Rubik's Cube Boss yellow attack (bullet hell)"""
    def __init__(self, x, y, speed):
        self.x = x
        self.y = y
        self.width = 14
        self.height = 14
        self.speed = speed  # Very slow falling speed
        self.rect = pygame.Rect(int(self.x - self.width // 2), int(self.y - self.height // 2), self.width, self.height)

    def move(self):
        self.y += self.speed
        self.rect.x = int(self.x - self.width // 2)
        self.rect.y = int(self.y - self.height // 2)

    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT + 30

    def draw(self, screen):
        center = (int(self.x), int(self.y))
        # Outer glow
        pygame.draw.circle(screen, (255, 255, 0), center, 7)
        # Middle layer
        pygame.draw.circle(screen, (255, 255, 100), center, 5)
        # Inner core
        pygame.draw.circle(screen, (255, 255, 200), center, 3)

class WhiteBall:
    """Bouncing white ball for Rubik's Cube Boss white attack (screensaver style)"""
    def __init__(self, x, y, speed, duration=20000):
        self.x = x
        self.y = y
        self.radius = 25  # Large ball
        self.width = self.radius * 2
        self.height = self.radius * 2
        self.speed = speed

        # Duration tracking
        self.duration = duration  # 20 seconds by default
        self.start_time = pygame.time.get_ticks()

        # Random initial direction
        angle = random.uniform(0, 2 * math.pi)
        self.vel_x = math.cos(angle) * speed
        self.vel_y = math.sin(angle) * speed

        self.rect = pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.width, self.height)

    def move(self):
        self.x += self.vel_x
        self.y += self.vel_y

        # Bounce off screen edges
        if self.x - self.radius <= 0 or self.x + self.radius >= SCREEN_WIDTH:
            self.vel_x *= -1
            # Clamp position to prevent getting stuck
            self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))

        if self.y - self.radius <= 0 or self.y + self.radius >= SCREEN_HEIGHT:
            self.vel_y *= -1
            # Clamp position to prevent getting stuck
            self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))

        self.rect.x = int(self.x - self.radius)
        self.rect.y = int(self.y - self.radius)

    def is_off_screen(self):
        # Check if duration expired
        current_time = pygame.time.get_ticks()
        return (current_time - self.start_time) > self.duration

    def draw(self, screen):
        center = (int(self.x), int(self.y))
        # Large white ball with glow
        pygame.draw.circle(screen, (200, 200, 200), center, self.radius)
        pygame.draw.circle(screen, (255, 255, 255), center, self.radius - 3)
        # Shiny spot
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x - 8), int(self.y - 8)), 8)

class OrangeFireball:
    """Orange fireball for Rubik's Cube Boss orange attack - shoots from rotating barrel"""
    def __init__(self, x, y, angle_degrees, speed, radius=None):
        self.x = x
        self.y = y
        self.radius = radius if radius is not None else RUBIKS_BOSS_ORANGE_FIREBALL_RADIUS
        self.width = self.radius * 2
        self.height = self.radius * 2
        self.speed = speed

        # Calculate velocity based on angle
        angle_rad = math.radians(angle_degrees)
        self.vel_x = math.cos(angle_rad) * speed
        self.vel_y = math.sin(angle_rad) * speed
        self.rect = pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.width, self.height)

    def move(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.rect.x = int(self.x - self.radius)
        self.rect.y = int(self.y - self.radius)

    def is_off_screen(self):
        return (self.x < -100 or self.x > SCREEN_WIDTH + 100 or
                self.y < -100 or self.y > SCREEN_HEIGHT + 100)

    def draw(self, screen):
        center = (int(self.x), int(self.y))
        # Layered fireball - scaled to radius
        pygame.draw.circle(screen, (255, 100, 0), center, self.radius)  # Outer orange
        if self.radius > 7:
            pygame.draw.circle(screen, (255, 150, 0), center, max(1, self.radius - 7))  # Mid orange
        if self.radius > 10:
            pygame.draw.circle(screen, (255, 200, 50), center, max(1, self.radius - 10))  # Inner yellow
        if self.radius > 13:
            pygame.draw.circle(screen, (255, 255, 150), center, max(1, self.radius - 13))  # Core white-yellow

class Boss:
    def __init__(self, encounter):
        # Boss configuration
        self.width = SCREEN_WIDTH // 3  # One third of screen width
        self.height = int(self.width * 0.6)  # Proportional height
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = 150
        
        # Health system
        self.encounter = max(1, encounter)
        self.max_health = BOSS_HEALTH_BASE + (self.encounter - 1) * BOSS_HEALTH_PER_LEVEL
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
            return []
            
        # Normal UFO movement (existing code)
        self.x += self.speed * self.direction
        
        if self.x <= 0 or self.x >= SCREEN_WIDTH - self.width:
            self.direction *= -1
        
        current_time = pygame.time.get_ticks()
        if current_time - self.last_direction_change > self.direction_change_cooldown:
            if random.randint(1, 100) <= 15:  # Reduced from 30% to 15% chance
                self.direction *= -1
                self.last_direction_change = current_time
                self.direction_change_cooldown = random.randint(2000, 6000)  # Changed from (1000, 3000)
        
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

        return []

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
        font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 16)
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
    def __init__(self, screen, score, level, is_coop=False, key_bindings=None):
        self.screen = screen
        self.score = score
        self.level = level
        self.is_coop = is_coop
        self.key_bindings = key_bindings if key_bindings else {}
        self.font_large = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 36)
        self.font_medium = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 24)
        self.font_small = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 20)
        
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

        # Axis navigation cooldown
        self.last_axis_input_time = 0
        self.axis_cooldown = 200  # milliseconds between axis inputs

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
                # Use fire button (remappable) or default A button (0)
                fire_button = self.key_bindings.get('player1_fire_button', 0)
                if (isinstance(fire_button, int) and event.button == fire_button) or event.button == 0:
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
                else:
                    # Check for remappable direction buttons
                    up_button = self.key_bindings.get('player1_up_button')
                    down_button = self.key_bindings.get('player1_down_button')
                    left_button = self.key_bindings.get('player1_left_button')
                    right_button = self.key_bindings.get('player1_right_button')

                    if isinstance(up_button, int) and event.button == up_button:
                        # Up button pressed
                        if not self.ok_selected:
                            self.current_letter_index[self.current_position] = (
                                self.current_letter_index[self.current_position] - 1
                            ) % len(self.alphabet)
                            self.name[self.current_position] = self.alphabet[self.current_letter_index[self.current_position]]
                    elif isinstance(down_button, int) and event.button == down_button:
                        # Down button pressed
                        if not self.ok_selected:
                            self.current_letter_index[self.current_position] = (
                                self.current_letter_index[self.current_position] + 1
                            ) % len(self.alphabet)
                            self.name[self.current_position] = self.alphabet[self.current_letter_index[self.current_position]]
                    elif isinstance(left_button, int) and event.button == left_button:
                        # Left button pressed
                        if self.ok_selected:
                            self.ok_selected = False
                            self.current_position = 2
                        elif self.current_position > 0:
                            self.current_position -= 1
                    elif isinstance(right_button, int) and event.button == right_button:
                        # Right button pressed
                        if self.current_position < 2:
                            self.current_position += 1
                        else:
                            self.ok_selected = True
            
            elif event.type == pygame.JOYHATMOTION:
                self.input_mode = "controller"
                # Check both standard D-pad and remappable direction assignments
                up_button = self.key_bindings.get('player1_up_button')
                down_button = self.key_bindings.get('player1_down_button')
                left_button = self.key_bindings.get('player1_left_button')
                right_button = self.key_bindings.get('player1_right_button')

                # Up: check standard D-pad or HAT_UP assignment
                if event.value[1] == 1 or (event.value[1] == 1 and up_button == HAT_UP):
                    if not self.ok_selected:
                        self.current_letter_index[self.current_position] = (
                            self.current_letter_index[self.current_position] - 1
                        ) % len(self.alphabet)
                        self.name[self.current_position] = self.alphabet[self.current_letter_index[self.current_position]]
                # Down: check standard D-pad or HAT_DOWN assignment
                elif event.value[1] == -1 or (event.value[1] == -1 and down_button == HAT_DOWN):
                    if not self.ok_selected:
                        self.current_letter_index[self.current_position] = (
                            self.current_letter_index[self.current_position] + 1
                        ) % len(self.alphabet)
                        self.name[self.current_position] = self.alphabet[self.current_letter_index[self.current_position]]
                # Left: check standard D-pad or HAT_LEFT assignment
                elif event.value[0] == -1 or (event.value[0] == -1 and left_button == HAT_LEFT):
                    if self.ok_selected:
                        self.ok_selected = False
                        self.current_position = 2
                    elif self.current_position > 0:
                        self.current_position -= 1
                # Right: check standard D-pad or HAT_RIGHT assignment
                elif event.value[0] == 1 or (event.value[0] == 1 and right_button == HAT_RIGHT):
                    if self.current_position < 2:
                        self.current_position += 1
                    else:
                        self.ok_selected = True

            elif event.type == pygame.JOYAXISMOTION:
                self.input_mode = "controller"
                # Cooldown to prevent too rapid changes
                current_time = pygame.time.get_ticks()
                if current_time - self.last_axis_input_time < self.axis_cooldown:
                    continue

                threshold = 0.5
                up_button = self.key_bindings.get('player1_up_button')
                down_button = self.key_bindings.get('player1_down_button')
                left_button = self.key_bindings.get('player1_left_button')
                right_button = self.key_bindings.get('player1_right_button')

                if event.axis == 1:  # Y-axis (up/down)
                    if event.value < -threshold:  # Up
                        # Check if standard axis or assigned to AXIS_UP
                        if up_button == AXIS_UP or up_button is None or isinstance(up_button, str) and 'hat' in up_button:
                            if not self.ok_selected:
                                self.current_letter_index[self.current_position] = (
                                    self.current_letter_index[self.current_position] - 1
                                ) % len(self.alphabet)
                                self.name[self.current_position] = self.alphabet[self.current_letter_index[self.current_position]]
                                self.last_axis_input_time = current_time
                    elif event.value > threshold:  # Down
                        # Check if standard axis or assigned to AXIS_DOWN
                        if down_button == AXIS_DOWN or down_button is None or isinstance(down_button, str) and 'hat' in down_button:
                            if not self.ok_selected:
                                self.current_letter_index[self.current_position] = (
                                    self.current_letter_index[self.current_position] + 1
                                ) % len(self.alphabet)
                                self.name[self.current_position] = self.alphabet[self.current_letter_index[self.current_position]]
                                self.last_axis_input_time = current_time
                elif event.axis == 0:  # X-axis (left/right)
                    if event.value < -threshold:  # Left
                        # Check if standard axis or assigned to AXIS_LEFT
                        if left_button == AXIS_LEFT or left_button is None or isinstance(left_button, str) and 'hat' in left_button:
                            if self.ok_selected:
                                self.ok_selected = False
                                self.current_position = 2
                            elif self.current_position > 0:
                                self.current_position -= 1
                            self.last_axis_input_time = current_time
                    elif event.value > threshold:  # Right
                        # Check if standard axis or assigned to AXIS_RIGHT
                        if right_button == AXIS_RIGHT or right_button is None or isinstance(right_button, str) and 'hat' in right_button:
                            if self.current_position < 2:
                                self.current_position += 1
                            else:
                                self.ok_selected = True
                            self.last_axis_input_time = current_time

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
                "Controller Up/Down: Change letter",
                "Controller Left/Right: Move cursor",
                "Fire button: Confirm/Next",
                "B button: Go back"
            ]
            
            for i, inst in enumerate(instructions):
                inst_text = self.font_small.render(inst, True, GRAY)
                inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, 900 + i * 30))
                self.screen.blit(inst_text, inst_rect)
        
        pygame.display.flip()

class HighScoreScreen:
    def __init__(self, screen, score_manager, sound_manager, player_stats=None, players=None, key_bindings=None):
        self.screen = screen
        self.score_manager = score_manager
        self.sound_manager = sound_manager
        self.key_bindings = key_bindings if key_bindings else {}
        self.font_large = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 36)
        self.font_medium = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 24)
        self.font_small = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 20)
        self.viewing_coop = False
        self.player_stats = player_stats  # Optional stats to display
        self.players = players  # Optional player objects for colors
    
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
                # Use fire button or B button to go back
                fire_button = self.key_bindings.get('player1_fire_button', 0)
                if (isinstance(fire_button, int) and event.button == fire_button) or event.button == 1:
                    self.sound_manager.play_sound('menu_select')
                    return "back"
            elif event.type == pygame.JOYHATMOTION:
                if event.value[0] != 0:  # Left or Right
                    self.sound_manager.play_sound('menu_change')
                    self.viewing_coop = not self.viewing_coop
            elif event.type == pygame.JOYAXISMOTION:
                # Support joystick axis for switching modes
                threshold = 0.5
                if event.axis == 0 and abs(event.value) > threshold:  # X-axis
                    self.sound_manager.play_sound('menu_change')
                    self.viewing_coop = not self.viewing_coop
        return None

    def draw_player_stats(self, stats, x, y):
        """Draw comprehensive stats for a single player"""
        stats_font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 12)
        header_font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 16)

        # Player header
        player_color = GREEN if stats.player_id == 1 else BLUE
        header_text = header_font.render(f"PLAYER {stats.player_id} STATS", True, player_color)
        self.screen.blit(header_text, (x, y))
        y += 45

        # Stats list
        stat_lines = [
            f"Score: {stats.final_score:,}",
            f"XP Level: {stats.final_xp_level}",
            f"",
            f"Enemies Killed: {stats.enemies_killed}",
            f"",
            f"Shots Fired: {stats.shots_fired_total}",
            f"  Normal: {stats.shots_fired_normal}",
            f"  Rapid: {stats.shots_fired_rapid}",
            f"  Multi: {stats.shots_fired_multi}",
            f"  Laser: {stats.shots_fired_laser}",
            f"",
            f"Invincibility: {stats.get_invincibility_seconds():.1f}s",
            f"Deaths: {stats.deaths}",
            f"",
            f"Boss Damage: {stats.boss_damage_dealt}",
            f"Bosses Fought: {stats.bosses_fought_count}",
        ]

        # Add boss names if any
        if stats.bosses_fought_names:
            for boss_name in stats.bosses_fought_names:
                # Simplify boss names
                simple_name = boss_name.replace("Boss", "").replace("Alien", "").replace("Overlord", "Ovl.")
                stat_lines.append(f"  {simple_name}")

        # Draw all stats
        for line in stat_lines:
            if line:  # Skip empty lines
                text = stats_font.render(line, True, WHITE)
                self.screen.blit(text, (x, y))
            y += 25

    def draw(self):
        self.screen.fill(BLACK)

        # Check if we're showing stats along with high scores
        if self.player_stats:
            self.draw_with_stats()
        else:
            self.draw_normal()

        pygame.display.flip()

    def draw_normal(self):
        """Draw the normal high scores screen without player stats"""
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

    def draw_with_stats(self):
        """Draw the high scores screen with player stats displayed"""
        # Title (smaller)
        title_text = self.font_medium.render("NEW HIGH SCORE!", True, YELLOW)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 40))
        self.screen.blit(title_text, title_rect)

        # Draw player stats
        num_players = len(self.player_stats)
        if num_players == 1:
            # Single player - show stats on left, high scores on right
            self.draw_player_stats(self.player_stats[0], 50, 100)
            self.draw_compact_high_scores(1000, 100)
        else:
            # Co-op - show player 1 on left, player 2 on right, high scores in center
            self.draw_player_stats(self.player_stats[0], 50, 100)
            if num_players > 1:
                self.draw_player_stats(self.player_stats[1], 1400, 100)
            self.draw_compact_high_scores(640, 100)

        # Instructions at bottom
        instruction_text = self.font_small.render("Press ESC, ENTER, or controller button to return", True, GRAY)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        self.screen.blit(instruction_text, instruction_rect)

    def draw_compact_high_scores(self, x, y):
        """Draw a compact version of the high scores table"""
        header_font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 14)
        compact_font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 10)

        # Determine which scores to show based on game mode
        is_coop = len(self.player_stats) > 1 if self.player_stats else False
        scores = self.score_manager.coop_scores if is_coop else self.score_manager.single_scores

        # Header
        mode_text = "CO-OP" if is_coop else "SINGLE"
        header_text = header_font.render(f"{mode_text} HIGH SCORES", True, CYAN)
        header_rect = header_text.get_rect(centerx=x + 200)
        header_rect.y = y
        self.screen.blit(header_text, header_rect)
        y += 50

        # Column headers
        rank_text = compact_font.render("RANK", True, GRAY)
        name_text = compact_font.render("NAME", True, GRAY)
        score_text = compact_font.render("SCORE", True, GRAY)

        self.screen.blit(rank_text, (x, y))
        self.screen.blit(name_text, (x + 80, y))
        self.screen.blit(score_text, (x + 200, y))
        y += 35

        # Draw separator line
        pygame.draw.line(self.screen, WHITE, (x, y - 5), (x + 380, y - 5), 1)

        # Show top 10 scores
        for i, score_entry in enumerate(scores[:10]):
            color = YELLOW if i < 3 else WHITE

            rank_line = compact_font.render(f"{i + 1}.", True, color)
            name_line = compact_font.render(score_entry['name'], True, color)
            score_line = compact_font.render(f"{score_entry['score']:,}", True, color)

            self.screen.blit(rank_line, (x, y))
            self.screen.blit(name_line, (x + 80, y))
            self.screen.blit(score_line, (x + 200, y))
            y += 30

        if not scores:
            no_scores = compact_font.render("No scores yet!", True, GRAY)
            no_scores_rect = no_scores.get_rect(centerx=x + 200)
            no_scores_rect.y = y
            self.screen.blit(no_scores, no_scores_rect)
        
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
        self.has_boss_shield_upgrade = False
        
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
        # Rapid fire powerup has a fixed cooldown (doesn't benefit from fire_rate upgrades)
        # Auto-fire upgrade only enables holding button, doesn't change cooldown
        if self.rapid_fire:
            return RAPID_FIRE_COOLDOWN  # Fixed rate for rapid fire powerup
        else:
            return BASE_SHOOT_COOLDOWN / self.upgrades.get_multiplier('fire_rate')
        
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

    def unlock_boss_shield(self):
        """Permanently unlock boss shield rewards"""
        self.has_boss_shield_upgrade = True
        self.activate_boss_shield()
        
    def take_damage(self, sound_manager=None):
        """Player takes damage - returns (took_damage, explosion_particles)"""
        if self.respawn_immunity or self.invincible:
            return False, None

        if self.boss_shield_active:
            self.clear_boss_shield()
            if sound_manager:
                sound_manager.play_sound('explosion_small', volume_override=0.5)
            return True, None

        # Play player explosion sound
        if sound_manager:
            sound_manager.play_sound('player_explosion', volume_override=0.8)

        # Create death explosion particles on every death
        explosion_particles = self.create_death_explosion()

        self.lives -= 1
        if self.lives <= 0:
            self.is_alive = False
        else:
            self.respawn()
        return True, explosion_particles
        
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
            # Add muzzle flash for multi-shot
            particles, flashes = self.create_muzzle_flash(offsets)
            bullets.append(('muzzle_flash', particles))
            bullets.append(('muzzle_flash_flashes', flashes))
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
            # Add muzzle flash for rapid fire
            particles, flashes = self.create_muzzle_flash(offsets)
            bullets.append(('muzzle_flash', particles))
            bullets.append(('muzzle_flash_flashes', flashes))
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
            # Add muzzle flash for normal shot
            particles, flashes = self.create_muzzle_flash(offsets)
            bullets.append(('muzzle_flash', particles))
            bullets.append(('muzzle_flash_flashes', flashes))
            # Play shoot sound for normal shot
            if sound_manager:
                sound_manager.play_sound('shoot', force_play=True)  # Always play normal shots

        return bullets

    def create_muzzle_flash(self, offsets):
        """Create muzzle flash particles and bright flash circles for bullet firing"""
        particles = []
        flashes = []
        base_x = self.x + self.width // 2
        muzzle_y = self.y  # Top of the ship

        # Create particles for each firing offset (gun barrel position)
        for offset in offsets:
            gun_x = base_x + offset

            # Create 5-8 particles per gun barrel
            num_particles = random.randint(5, 8)
            for _ in range(num_particles):
                # Muzzle flash colors: bright white/yellow/orange
                color = random.choice([
                    (255, 255, 255),  # Bright white
                    (255, 255, 150),  # Yellow-white
                    (255, 200, 100),  # Yellow-orange
                    (255, 150, 0)     # Orange
                ])

                # Small, fast particles shooting upward and slightly outward
                particle = {
                    'x': gun_x + random.uniform(-3, 3),
                    'y': muzzle_y + random.uniform(-2, 2),
                    'vel_x': random.uniform(-1.5, 1.5),
                    'vel_y': random.uniform(-4, -1),  # Mostly upward
                    'color': color,
                    'size': random.randint(2, 4),
                    'life': random.randint(100, 250)  # Short-lived (100-250ms)
                }
                particles.append(particle)

            # Create bright expanding flash circle at each gun position
            flash = {
                'x': gun_x,
                'y': muzzle_y,
                'radius': 2,
                'max_radius': 15,
                'growth_speed': 1.2,
                'color': (255, 255, 255),  # Bright white
                'life': 120  # Short flash duration (120ms)
            }
            flashes.append(flash)

        return particles, flashes

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
        
    def handle_controller_input(self, shoot_callback=None, fire_button=0, left_button=None, right_button=None):
        if not self.is_alive:
            return
        if self.controller:
            hat = self.controller.get_hat(0) if self.controller.get_numhats() > 0 else (0, 0)
            axis_x = self.controller.get_axis(0) if self.controller.get_numaxes() > 0 else 0
            axis_y = self.controller.get_axis(1) if self.controller.get_numaxes() > 1 else 0

            # Check for left movement: button, hat, or axis
            left_pressed = False
            right_pressed = False

            def hat_matches(binding):
                if binding == HAT_LEFT:
                    return hat[0] == -1
                if binding == HAT_RIGHT:
                    return hat[0] == 1
                if binding == HAT_UP:
                    return hat[1] == 1
                if binding == HAT_DOWN:
                    return hat[1] == -1
                return False

            def axis_matches(binding):
                threshold = 0.3
                if binding == AXIS_LEFT:
                    return axis_x < -threshold
                if binding == AXIS_RIGHT:
                    return axis_x > threshold
                if binding == AXIS_UP:
                    return axis_y < -threshold
                if binding == AXIS_DOWN:
                    return axis_y > threshold
                return False

            if isinstance(left_button, str):
                left_pressed = hat_matches(left_button) or axis_matches(left_button)
            if isinstance(left_button, int) and self.controller.get_numbuttons() > left_button:
                left_pressed = self.controller.get_button(left_button)
            if isinstance(right_button, str):
                right_pressed = hat_matches(right_button) or axis_matches(right_button)
            if isinstance(right_button, int) and self.controller.get_numbuttons() > right_button:
                right_pressed = self.controller.get_button(right_button)

            # Also check hat and axis as fallback
            if left_pressed or hat[0] == -1 or axis_x < -0.3:
                self.move_left()
            elif right_pressed or hat[0] == 1 or axis_x > 0.3:
                self.move_right()

            # Auto-fire support for controller
            if self.upgrades.has_auto_fire() and shoot_callback:
                button_pressed = self.controller.get_button(fire_button) if self.controller.get_numbuttons() > fire_button else False
                if button_pressed:
                    shoot_callback()
                
    def draw(self, screen, font=None):
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
                font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 20)
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
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.006))
            ring_alpha = int(130 + 100 * pulse)
            steady_alpha = 140

            # Larger square surface with independent offsets to keep the outline fully visible
            surface_size = max(self.width, self.height) + 120
            shield_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
            center = (surface_size // 2, surface_size // 2)
            radius = max(self.width, self.height) // 2 + 24

            # Steady outline
            pygame.draw.circle(shield_surface, (120, 200, 255, steady_alpha), center, radius, 2)
            # Flashing outline
            pygame.draw.circle(shield_surface, (80, 170, 255, ring_alpha), center, radius + 2, 6)

            offset_x = (surface_size - self.width) // 2
            offset_y = (surface_size - self.height) // 2
            screen.blit(shield_surface, (self.x - offset_x, self.y - offset_y))
        
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
        elif self.has_laser and (current_time // flash_interval) % 2:
            # Flash blue when player has laser powerup
            color = (100, 150, 255)  # Light blue

        pygame.draw.polygon(screen, color, points)

        # Draw powerup indicators below the player ship
        if font:
            powerup_texts = []

            # Rapid fire ammo
            if self.rapid_fire and self.rapid_fire_ammo > 0:
                powerup_texts.append(f"R:{self.rapid_fire_ammo}")

            # Multi-shot ammo
            if self.has_multi_shot and self.multi_shot_ammo > 0:
                powerup_texts.append(f"M:{self.multi_shot_ammo}")

            # Invincibility timer (in seconds)
            if self.invincible:
                time_left = (self.invincible_end_time - pygame.time.get_ticks()) / 1000
                powerup_texts.append(f"I:{time_left:.0f}")

            # Combine all powerup texts
            if powerup_texts:
                combined_text = " ".join(powerup_texts)
                text_surface = font.render(combined_text, True, ORANGE)
                text_rect = text_surface.get_rect()

                # Position text below the ship, centered
                text_x = self.x + (self.width - text_rect.width) // 2
                text_y = self.y + self.height + 5

                screen.blit(text_surface, (text_x, text_y))

    def create_death_explosion(self):
        """Create a small-scale particle explosion when player dies (similar to boss explosions)"""
        explosion_particles = []

        # Create particles - smaller scale than boss explosions
        for _ in range(20):  # Fewer particles than boss (boss has 50-70)
            particle = {
                'x': self.x + random.randint(-20, self.width + 20),  # Smaller spread than boss
                'y': self.y + random.randint(-10, self.height + 10),
                'vel_x': random.uniform(-4, 4),  # Slower than boss particles
                'vel_y': random.uniform(-4, 2),
                'color': random.choice([
                    (255, 150, 0),   # Bright Orange
                    (255, 80, 80),   # Bright Red
                    (255, 255, 100), # Bright Yellow
                    (255, 255, 255), # White
                    (100, 255, 255), # Bright Cyan
                    (255, 200, 0),   # Gold
                ]),
                'size': random.randint(2, 6),  # Smaller particles than boss (boss is 4-12)
                'life': random.randint(500, 900),  # Shorter duration than boss (boss is 1000-1800)
                'gravity': random.uniform(0.1, 0.3)  # Same gravity as boss
            }
            explosion_particles.append(particle)

        return explosion_particles

class AlienOverlordBoss:
    def __init__(self, encounter):
        self.encounter = max(1, encounter)
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
            return None
        for player in players:
            if player and player.is_alive and hand['rect'].colliderect(player.rect):
                took_damage, explosion_particles = player.take_damage(sound_manager)
                hand['state'] = 'returning'
                return explosion_particles
        return None

    def update(self, players=None, sound_manager=None):
        if self.destruction_complete:
            self.explosion_effects = [exp for exp in self.explosion_effects if exp['life'] > 0]
            for explosion in self.explosion_effects:
                explosion['radius'] += explosion['growth']
                explosion['life'] -= 1
            return []

        self.x += self.head_speed * self.direction
        if self.x <= 100 or self.x + self.width >= SCREEN_WIDTH - 100:
            self.direction *= -1
        self.rect.x = int(self.x)
        self.rect.y = self.y

        alive_players = [p for p in players if p and p.is_alive] if players else []
        current_time = pygame.time.get_ticks()

        # Collect player explosion particles
        player_explosion_particles = []

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
                explosion_particles = self._check_hand_player_collision(hand, alive_players, sound_manager)
                if explosion_particles:
                    player_explosion_particles.extend(explosion_particles)
            elif hand['state'] == 'returning':
                reached = self._move_hand_toward(hand, home_x, home_y)
                if reached:
                    hand['state'] = 'idle'
                    hand['last_drop'] = current_time
            self._update_hand_rect(hand)

        for explosion in self.explosion_effects:
            explosion['radius'] += explosion['growth']
            explosion['life'] -= 1

        return player_explosion_particles

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
            font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 14)
            text = font.render(f"{label}: {int(ratio * 100)}%", True, WHITE)
            text_rect = text.get_rect(center=(x + width // 2, y - 18))
            screen.blit(text, text_rect)


class BulletHellBoss:
    """Third boss - Fast-moving bullet hell boss that creates a field of slow-falling projectiles"""
    def __init__(self, encounter):
        self.encounter = max(1, encounter)

        # Size - 5x the size of a normal alien
        self.base_width = 45 * 5
        self.base_height = 30 * 5
        self.width = self.base_width
        self.height = self.base_height

        # Starting position
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = BULLET_HELL_BOSS_MOVEMENT_ZONE_TOP + 50
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # Health system
        self.max_health = BULLET_HELL_BOSS_HEALTH_BASE + (self.encounter - 1) * BULLET_HELL_BOSS_HEALTH_PER_LEVEL
        self.health = self.max_health

        # Movement system - random patterns in top half of screen
        self.speed = BULLET_HELL_BOSS_SPEED_BASE + (self.encounter - 1) * BULLET_HELL_BOSS_SPEED_GROWTH
        self.movement_zone_top = BULLET_HELL_BOSS_MOVEMENT_ZONE_TOP
        self.movement_zone_bottom = BULLET_HELL_BOSS_MOVEMENT_ZONE_BOTTOM
        self.target_x = self.x
        self.target_y = self.y
        self.last_target_change = pygame.time.get_ticks()
        self.target_change_cooldown = random.randint(800, 1500)  # Change direction frequently

        # Shooting system - rapid fire, slow falling bullets
        self.shot_cooldown = int(BULLET_HELL_BOSS_SHOT_COOLDOWN_BASE * (BULLET_HELL_BOSS_SHOT_COOLDOWN_SCALE ** (self.encounter - 1)))
        self.last_shot = pygame.time.get_ticks() - random.randint(0, 200)
        self.bullet_speed = BULLET_HELL_BOSS_BULLET_SPEED

        # Visual effects
        self.destruction_complete = False
        self.destruction_start_time = 0
        self.explosion_effects = []

        # Choose initial random target
        self._pick_new_target()

    def _pick_new_target(self):
        """Pick a new random target position within the movement zone"""
        margin = 100  # Keep away from edges
        self.target_x = random.randint(margin, SCREEN_WIDTH - margin - self.width)
        self.target_y = random.randint(self.movement_zone_top, self.movement_zone_bottom - self.height)

    def update(self, players=None, sound_manager=None):
        """Update boss position and behavior"""
        if self.destruction_complete:
            # Update explosion effects during destruction
            self.explosion_effects = [exp for exp in self.explosion_effects if exp['life'] > 0]
            for explosion in self.explosion_effects:
                explosion['radius'] += explosion['growth']
                explosion['life'] -= 1
            return

        current_time = pygame.time.get_ticks()

        # Check if it's time to pick a new target
        if current_time - self.last_target_change > self.target_change_cooldown:
            self._pick_new_target()
            self.last_target_change = current_time
            self.target_change_cooldown = random.randint(800, 1500)

        # Move towards target with smooth movement
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)

        if distance > self.speed:
            # Normalize and apply speed
            self.x += (dx / distance) * self.speed
            self.y += (dy / distance) * self.speed
        else:
            # Reached target, pick a new one
            self.x = self.target_x
            self.y = self.target_y
            self._pick_new_target()
            self.last_target_change = current_time

        # Keep within bounds (safety check)
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        self.y = max(self.movement_zone_top, min(self.movement_zone_bottom - self.height, self.y))

        # Update rect
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        # Update explosion effects
        self.explosion_effects = [exp for exp in self.explosion_effects if exp['life'] > 0]
        for explosion in self.explosion_effects:
            explosion['radius'] += explosion['growth']
            explosion['life'] -= 1

        return []

    def shoot(self, players, sound_manager=None):
        """Rapid-fire shooting that creates a bullet hell effect"""
        if self.destruction_complete:
            return []

        bullets = []
        current_time = pygame.time.get_ticks()

        # Check if it's time to shoot
        if current_time - self.last_shot > self.shot_cooldown:
            # Fire from bottom center of boss
            center_x = self.x + self.width // 2
            bottom_y = self.y + self.height

            # Create a slow-falling bullet
            bullet = SlowFallingBullet(center_x, bottom_y, self.bullet_speed)
            bullets.append(bullet)

            self.last_shot = current_time

            # Play sound
            if sound_manager:
                sound_manager.play_sound('enemy_shoot', volume_override=0.35)

        return bullets

    def take_turret_damage(self, turret_index, damage=1):
        """This boss has no turrets, but we need this method for compatibility"""
        return False

    def take_main_damage(self, damage=1):
        """Take damage to the main body"""
        self.health -= damage

        if self.health <= 0:
            self.health = 0
            self.start_destruction_sequence()
            return True  # Boss destroyed

        return False

    def start_destruction_sequence(self):
        """Start the dramatic destruction sequence"""
        self.destruction_complete = True
        self.destruction_start_time = pygame.time.get_ticks()

        # Create massive explosions
        for _ in range(25):
            explosion = {
                'x': self.x + random.randint(-50, self.width + 50),
                'y': self.y + random.randint(-30, self.height + 30),
                'radius': 0,
                'growth': random.uniform(6, 12),
                'color': random.choice([ORANGE, RED, YELLOW, WHITE, (255, 100, 0), CYAN]),
                'life': random.randint(80, 150),
                'max_radius': random.randint(60, 120)
            }
            self.explosion_effects.append(explosion)

    def is_destruction_complete(self):
        """Check if destruction sequence is finished"""
        if not self.destruction_complete:
            return False
        return pygame.time.get_ticks() - self.destruction_start_time > 2000

    def create_final_explosion(self):
        """Create a massive particle explosion when boss is completely destroyed"""
        explosion_particles = []

        for _ in range(70):
            particle = {
                'x': self.x + random.randint(-100, self.width + 100),
                'y': self.y + random.randint(-50, self.height + 50),
                'vel_x': random.uniform(-8, 8),
                'vel_y': random.uniform(-8, 3),
                'color': random.choice([
                    (255, 150, 0),   # Bright Orange
                    (255, 80, 80),   # Bright Red
                    (255, 255, 100), # Bright Yellow
                    (255, 255, 255), # White
                    (100, 255, 255), # Bright Cyan
                    (255, 200, 0),   # Gold
                ]),
                'size': random.randint(4, 12),
                'life': random.randint(1000, 1800),
                'gravity': random.uniform(0.1, 0.3)
            }
            explosion_particles.append(particle)

        return explosion_particles

    def get_turret_rects(self):
        """This boss has no turrets, return empty list for compatibility"""
        return []

    def get_main_body_rect(self):
        """Get collision rectangle for the main body (always active)"""
        if self.destruction_complete:
            return None
        return self.rect

    def draw(self, screen):
        """Draw the boss - giant squid alien (5x scale)"""
        if self.destruction_complete:
            # Draw explosion effects during destruction
            for explosion in self.explosion_effects:
                if explosion['radius'] > 0:
                    alpha = int(255 * (explosion['life'] / 150))
                    explosion_surface = pygame.Surface((explosion['radius']*2, explosion['radius']*2), pygame.SRCALPHA)
                    pygame.draw.circle(explosion_surface, explosion['color'], (explosion['radius'], explosion['radius']), explosion['radius'])
                    explosion_surface.set_alpha(alpha)
                    screen.blit(explosion_surface, (explosion['x'] - explosion['radius'], explosion['y'] - explosion['radius']))
            return

        # Color changes based on health (green to red)
        health_ratio = self.health / self.max_health
        if health_ratio > 0.6:
            body_color = (0, 200, 0)
            dark_color = (0, 150, 0)
        elif health_ratio > 0.3:
            body_color = (200, 200, 0)  # Yellow
            dark_color = (150, 150, 0)
        else:
            body_color = (200, 50, 0)  # Orange-red
            dark_color = (150, 0, 0)

        # Scale factor is 5x
        scale = 5

        # Draw giant squid alien (based on draw_squid_enemy but 5x larger)
        x = int(self.x)
        y = int(self.y)

        # Main body outline - scaled
        pygame.draw.rect(screen, body_color, (x + 3*scale, y + 2*scale, 39*scale, 26*scale))

        # Head bumps - scaled
        pygame.draw.rect(screen, body_color, (x - 2*scale, y + 5*scale, 12*scale, 12*scale))
        pygame.draw.rect(screen, body_color, (x + 35*scale, y + 5*scale, 12*scale, 12*scale))

        # Eyes (white with black pupils) - scaled
        pygame.draw.rect(screen, WHITE, (x + 8*scale, y + 6*scale, 10*scale, 10*scale))
        pygame.draw.rect(screen, WHITE, (x + 27*scale, y + 6*scale, 10*scale, 10*scale))
        pygame.draw.rect(screen, BLACK, (x + 10*scale, y + 8*scale, 6*scale, 6*scale))
        pygame.draw.rect(screen, BLACK, (x + 29*scale, y + 8*scale, 6*scale, 6*scale))

        # Tentacles - scaled
        pygame.draw.rect(screen, dark_color, (x + 3*scale, y + 24*scale, 5*scale, 10*scale))
        pygame.draw.rect(screen, dark_color, (x + 10*scale, y + 26*scale, 5*scale, 8*scale))
        pygame.draw.rect(screen, dark_color, (x + 17*scale, y + 24*scale, 5*scale, 10*scale))
        pygame.draw.rect(screen, dark_color, (x + 24*scale, y + 26*scale, 5*scale, 8*scale))
        pygame.draw.rect(screen, dark_color, (x + 31*scale, y + 24*scale, 5*scale, 10*scale))
        pygame.draw.rect(screen, dark_color, (x + 38*scale, y + 26*scale, 5*scale, 8*scale))

        # Add glowing effect around the boss to make it more menacing
        glow_surface = pygame.Surface((self.width + 40, self.height + 40), pygame.SRCALPHA)
        glow_color = (*body_color, 60)  # Semi-transparent
        pygame.draw.rect(glow_surface, glow_color, glow_surface.get_rect(), border_radius=20)
        screen.blit(glow_surface, (x - 20, y - 20))

        # Draw health bar
        self._draw_health_bar(screen, x, y - 40, self.width, 15, health_ratio, label='ALIEN DESTROYER')

    def _draw_health_bar(self, screen, x, y, width, height, ratio, label=None):
        """Draw a health bar"""
        pygame.draw.rect(screen, RED, (x, y, width, height))
        pygame.draw.rect(screen, GREEN, (x, y, int(width * ratio), height))
        pygame.draw.rect(screen, WHITE, (x, y, width, height), 2)
        if label:
            font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 16)
            text = font.render(f"{label}: {int(ratio * 100)}%", True, WHITE)
            text_rect = text.get_rect(center=(x + width // 2, y - 20))
            screen.blit(text, text_rect)


class Asteroid:
    """Falling asteroid for the Asteroid Field Boss"""
    def __init__(self, x, speed, size_multiplier):
        # Random size within range, scaled by multiplier
        base_size = random.randint(ASTEROID_BOSS_SIZE_MIN, ASTEROID_BOSS_SIZE_MAX)
        self.size = int(base_size * size_multiplier)

        self.x = x
        self.y = -self.size  # Start above screen
        self.speed = speed
        self.width = self.size
        self.height = self.size
        self.rect = pygame.Rect(int(self.x - self.size // 2), int(self.y - self.size // 2), self.size, self.size)

        # Visual properties for variety
        self.color = random.choice([
            (120, 120, 120),  # Gray
            (100, 100, 100),  # Dark gray
            (140, 140, 140),  # Light gray
            (100, 80, 70),    # Brown-gray
        ])
        self.rotation = random.randint(0, 360)
        self.rotation_speed = random.uniform(-2, 2)

        # Near-miss XP tracking (one time per asteroid)
        self.near_miss_triggered = False

        # Randomized crater properties for visual variety
        self.num_craters = random.randint(2, 5)
        self.craters = []
        for i in range(self.num_craters):
            crater = {
                'angle_offset': random.uniform(0, 360),  # Random angle position
                'distance_factor': random.uniform(0.2, 0.5),  # How far from center (0-50% of radius)
                'size_factor': random.uniform(0.15, 0.35)  # Size relative to asteroid radius
            }
            self.craters.append(crater)

    def move(self):
        self.y += self.speed
        self.rotation += self.rotation_speed
        self.rect.x = int(self.x - self.size // 2)
        self.rect.y = int(self.y - self.size // 2)

    def is_off_screen(self):
        return self.y - self.size // 2 > SCREEN_HEIGHT

    def collides_with_circle(self, other_x, other_y, other_radius):
        """Check circular collision with another circular object"""
        radius = self.size // 2
        dx = self.x - other_x
        dy = self.y - other_y
        distance = math.sqrt(dx * dx + dy * dy)
        return distance < (radius + other_radius)

    def draw(self, screen):
        # Draw irregular asteroid shape
        center = (int(self.x), int(self.y))
        radius = self.size // 2

        # Draw main body
        pygame.draw.circle(screen, self.color, center, radius)

        # Add some irregular edges (simple approach - draw smaller circles around perimeter)
        num_bumps = 6
        for i in range(num_bumps):
            angle = (self.rotation + i * 60) * math.pi / 180
            bump_x = center[0] + int(math.cos(angle) * radius * 0.7)
            bump_y = center[1] + int(math.sin(angle) * radius * 0.7)
            bump_size = radius // 3
            pygame.draw.circle(screen, self.color, (bump_x, bump_y), bump_size)

        # Add randomized crater details (darker spots)
        darker_color = (max(0, self.color[0] - 30), max(0, self.color[1] - 30), max(0, self.color[2] - 30))
        for crater in self.craters:
            angle = (self.rotation + crater['angle_offset']) * math.pi / 180
            crater_x = center[0] + int(math.cos(angle) * radius * crater['distance_factor'])
            crater_y = center[1] + int(math.sin(angle) * radius * crater['distance_factor'])
            crater_size = int(radius * crater['size_factor'])
            pygame.draw.circle(screen, darker_color, (crater_x, crater_y), crater_size)

        # Outline
        pygame.draw.circle(screen, (80, 80, 80), center, radius, 2)


class AsteroidFieldBoss:
    """Fourth boss - Navigate through an asteroid field"""
    def __init__(self, encounter):
        self.encounter = max(1, encounter)

        # Health system - represents asteroids that need to reach bottom
        self.max_health = ASTEROID_BOSS_HEALTH_BASE + (self.encounter - 1) * ASTEROID_BOSS_HEALTH_PER_LEVEL
        self.health = self.max_health

        # Asteroid spawning system
        self.spawn_cooldown = int(ASTEROID_BOSS_SPAWN_COOLDOWN_BASE * (ASTEROID_BOSS_SPAWN_COOLDOWN_SCALE ** (self.encounter - 1)))
        self.last_spawn = pygame.time.get_ticks()

        # Asteroid speed
        self.asteroid_speed = ASTEROID_BOSS_SPEED_BASE + (self.encounter - 1) * ASTEROID_BOSS_SPEED_GROWTH

        # Size multiplier for all asteroids
        self.size_multiplier = ASTEROID_BOSS_SIZE_MULTIPLIER

        # Track active asteroids
        self.asteroids = []

        # Completion state
        self.destruction_complete = False
        self.destruction_start_time = 0
        self.completion_message_duration = 3000  # Show message for 3 seconds

        # For compatibility with other bosses
        self.x = SCREEN_WIDTH // 2
        self.y = 50
        self.width = 200
        self.height = 100
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.explosion_effects = []

    def update(self, players=None, sound_manager=None):
        """Update asteroid field"""
        if self.destruction_complete:
            return []

        current_time = pygame.time.get_ticks()

        # Spawn new asteroids
        if current_time - self.last_spawn > self.spawn_cooldown:
            # Random X position across screen
            x = random.randint(50, SCREEN_WIDTH - 50)
            # Add some speed variation
            speed_variation = random.uniform(0.8, 1.2)
            asteroid = Asteroid(x, self.asteroid_speed * speed_variation, self.size_multiplier)
            self.asteroids.append(asteroid)
            self.last_spawn = current_time

        # Update all asteroids
        asteroids_to_remove = []
        for asteroid in self.asteroids:
            asteroid.move()

            # Check if asteroid reached bottom (player missed it)
            if asteroid.is_off_screen():
                asteroids_to_remove.append(asteroid)
                # Boss loses health
                self.health -= ASTEROID_BOSS_HEALTH_LOSS_PER_ASTEROID
                if self.health <= 0:
                    self.health = 0
                    self.start_completion_sequence()
                    return []  # Exit early, asteroids already cleared

        # Remove asteroids that reached bottom
        for asteroid in asteroids_to_remove:
            if asteroid in self.asteroids:  # Safety check
                self.asteroids.remove(asteroid)

        return []

    def shoot(self, players, sound_manager=None):
        """This boss doesn't shoot bullets - asteroids are the hazard"""
        return []

    def start_completion_sequence(self):
        """Start completion sequence (no explosion, just message)"""
        self.destruction_complete = True
        self.destruction_start_time = pygame.time.get_ticks()
        # Clear remaining asteroids
        self.asteroids.clear()

    def is_destruction_complete(self):
        """Check if completion sequence is finished"""
        if not self.destruction_complete:
            return False
        return pygame.time.get_ticks() - self.destruction_start_time > self.completion_message_duration

    def create_final_explosion(self):
        """No explosion for asteroid field - return empty list"""
        return []

    def take_turret_damage(self, turret_index, damage=1):
        """Asteroids cannot be destroyed by shooting"""
        return False

    def take_main_damage(self, damage=1):
        """Player shooting asteroids doesn't damage the boss"""
        return False

    def get_turret_rects(self):
        """Return empty list - asteroids cannot be destroyed by shooting"""
        return []

    def get_main_body_rect(self):
        """No main body to hit"""
        return None

    def remove_asteroid(self, asteroid):
        """Remove an asteroid (when it collides with player)"""
        if asteroid in self.asteroids:
            self.asteroids.remove(asteroid)

    def draw(self, screen):
        """Draw the asteroid field"""
        if self.destruction_complete:
            # Show completion message
            font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 32)
            text = font.render("ASTEROID FIELD CLEARED!", True, GREEN)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

            # Draw background box for text
            padding = 40
            box_rect = text_rect.inflate(padding * 2, padding * 2)
            pygame.draw.rect(screen, BLACK, box_rect)
            pygame.draw.rect(screen, GREEN, box_rect, 4)

            screen.blit(text, text_rect)
            return

        # Draw all asteroids
        for asteroid in self.asteroids:
            asteroid.draw(screen)

        # Draw health bar at top of screen
        bar_width = 600
        bar_height = 30
        bar_x = SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = 60

        health_ratio = self.health / self.max_health

        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_width * health_ratio), bar_height))
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 3)

        # Label
        font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 14)
        label = f"ASTEROID FIELD: {int(health_ratio * 100)}%"
        text = font.render(label, True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, bar_y - 20))
        screen.blit(text, text_rect)


class RubiksCubeBoss:
    """Fifth boss - Rotating Rubik's Cube with color-based attacks"""
    def __init__(self, encounter):
        self.encounter = max(1, encounter)

        # Grid configuration
        self.grid_size = RUBIKS_BOSS_GRID_SIZE  # 7x7
        self.square_size = RUBIKS_BOSS_SQUARE_SIZE  # 50px per square
        self.total_size = self.grid_size * self.square_size  # 250px total

        # Position
        self.x = SCREEN_WIDTH // 2 - self.total_size // 2
        self.y = 150
        self.center_x = self.x + self.total_size // 2
        self.center_y = self.y + self.total_size // 2

        # Movement
        self.speed = RUBIKS_BOSS_SPEED_BASE
        self.direction = random.choice([-1, 1])
        self.last_direction_change = pygame.time.get_ticks()
        self.direction_change_cooldown = random.randint(2000, 6000)  # Changed from (1000, 3000) for less frequent changes

        # Rotation
        self.rotation_angle = 0
        self.rotation_speed = RUBIKS_BOSS_ROTATION_SPEED_BASE + (self.encounter - 1) * RUBIKS_BOSS_ROTATION_SPEED_GROWTH

        # Initialize 7x7 grid of squares
        # Grid positions: [row][col] where (3, 3) is center
        self.squares = []

        # Rubik's cube colors (6 colors)
        self.rubiks_colors = [
            (255, 0, 0),      # Red
            (0, 0, 255),      # Blue
            (0, 255, 0),      # Green
            (255, 255, 0),    # Yellow
            (255, 255, 255),  # White
            (255, 140, 0)     # Orange
        ]

        # Center square is special (light blue)
        self.center_color = (135, 206, 250)  # Light blue

        # Calculate center health first
        center_max_health = RUBIKS_BOSS_CENTER_HEALTH_BASE + (self.encounter - 1) * RUBIKS_BOSS_CENTER_HEALTH_PER_LEVEL
        # Regular squares have percentage of center health (configurable)
        square_max_health = int(center_max_health * RUBIKS_BOSS_SQUARE_HEALTH_PERCENTAGE)

        # Create grid
        center_pos = self.grid_size // 2  # Center position (3 for 7x7 grid)
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                is_center = (row == center_pos and col == center_pos)  # Center square

                if is_center:
                    max_health = center_max_health
                    color = self.center_color
                else:
                    max_health = square_max_health
                    color = random.choice(self.rubiks_colors)

                square = {
                    'row': row,
                    'col': col,
                    'health': max_health,
                    'max_health': max_health,
                    'color': color,
                    'destroyed': False,
                    'is_center': is_center
                }
                self.squares.append(square)

        # Attack phase system
        self.current_phase = 'mixed'  # 'mixed' or 'attack'
        self.current_attack_color = None
        self.phase_start_time = pygame.time.get_ticks()
        self.mixed_phase_duration = RUBIKS_BOSS_MIXED_PHASE_DURATION
        self.attack_phase_duration = RUBIKS_BOSS_ATTACK_PHASE_DURATION

        # Attack cooldowns
        self.last_attack_time = pygame.time.get_ticks()
        self.red_cooldown = RUBIKS_BOSS_RED_SHOOT_COOLDOWN
        self.blue_cooldown = RUBIKS_BOSS_BLUE_SHOOT_COOLDOWN
        self.yellow_cooldown = RUBIKS_BOSS_YELLOW_SHOOT_COOLDOWN
        self.orange_cooldown = RUBIKS_BOSS_ORANGE_SHOOT_COOLDOWN
        self.white_cooldown = RUBIKS_BOSS_WHITE_SHOOT_COOLDOWN

        # Special attack objects
        self.green_laser = None  # Active laser beam
        self.last_white_ball_time = 0  # Track white ball shooting cooldown

        # Green laser warning system
        self.green_laser_warning = False
        self.green_laser_warning_start_time = 0
        self.green_warning_duration = 3000  # 3 seconds warning

        # Orange attack state (stops movement, spins fast)
        self.orange_attack_active = False
        self.normal_rotation_speed = self.rotation_speed  # Store normal speed

        # Debug mode forced attack color (set externally by debug menu)
        self.debug_forced_attack_color = None

        # Destruction state
        self.destruction_complete = False
        self.destruction_start_time = 0
        self.explosion_effects = []

        # Rect for compatibility
        self.rect = pygame.Rect(self.x, self.y, self.total_size, self.total_size)
        self.width = self.total_size
        self.height = self.total_size

    def update(self, players=None, sound_manager=None):
        """Update boss movement, rotation, and attack phases"""
        if self.destruction_complete:
            # Update explosion effects
            self.explosion_effects = [exp for exp in self.explosion_effects if exp['life'] > 0]
            for explosion in self.explosion_effects:
                # Update radius if particle has one (expanding explosions)
                if 'radius' in explosion and 'growth' in explosion:
                    explosion['radius'] += explosion['growth']
                explosion['life'] -= 1
            return []

        # Check if only center square remains (final phase)
        only_center_remains = all(sq['destroyed'] for sq in self.squares if not sq['is_center'])

        current_time = pygame.time.get_ticks()

        # Movement (left/right like UFO boss)
        # Stop movement during orange attack, double speed when only center remains
        if self.orange_attack_active:
            # Don't move during orange attack
            pass
        else:
            current_speed = self.speed * 2 if only_center_remains else self.speed
            self.x += current_speed * self.direction

            if self.x <= 0 or self.x >= SCREEN_WIDTH - self.total_size:
                self.direction *= -1

            if current_time - self.last_direction_change > self.direction_change_cooldown:
                if random.randint(1, 100) <= 15:  # Reduced from 30% to 15% chance
                    self.direction *= -1
                    self.last_direction_change = current_time
                    self.direction_change_cooldown = random.randint(2000, 6000)  # Changed from (1000, 3000)

        # Update center position
        self.center_x = self.x + self.total_size // 2
        self.center_y = self.y + self.total_size // 2

        # Rotation - faster during orange attack
        if self.orange_attack_active:
            self.rotation_angle = (self.rotation_angle + RUBIKS_BOSS_ORANGE_ROTATION_SPEED / 60) % 360
        else:
            self.rotation_angle = (self.rotation_angle + self.normal_rotation_speed / 60) % 360

        # Update rect
        self.rect.x = self.x
        self.rect.y = self.y

        # Attack phase management
        time_in_phase = current_time - self.phase_start_time

        if self.current_phase == 'mixed':
            # Mixed colors, no attack
            if time_in_phase >= self.mixed_phase_duration:
                # Switch to attack phase with color (debug forced or random)
                self.current_phase = 'attack'

                # Check for debug forced attack color
                if self.debug_forced_attack_color:
                    color_map = {
                        'Red': (255, 0, 0),
                        'Blue': (0, 0, 255),
                        'Green': (0, 255, 0),
                        'Yellow': (255, 255, 0),
                        'White': (255, 255, 255),
                        'Orange': (255, 140, 0)
                    }
                    self.current_attack_color = color_map.get(self.debug_forced_attack_color, random.choice(self.rubiks_colors))
                else:
                    self.current_attack_color = random.choice(self.rubiks_colors)

                self.phase_start_time = current_time
                self.last_attack_time = current_time
                self.last_white_ball_time = current_time - self.white_cooldown  # Allow immediate white ball shot

                # Enable orange attack mode if orange color selected
                if self.current_attack_color == (255, 140, 0):  # Orange
                    self.orange_attack_active = True

                # Apply color to all non-destroyed, non-center squares
                for square in self.squares:
                    if not square['destroyed'] and not square['is_center']:
                        square['color'] = self.current_attack_color
        else:  # attack phase
            if time_in_phase >= self.attack_phase_duration:
                # Switch back to mixed phase
                self.current_phase = 'mixed'
                self.current_attack_color = None
                self.phase_start_time = current_time
                self.orange_attack_active = False  # Disable orange attack mode

                # Randomize colors for non-destroyed, non-center squares
                for square in self.squares:
                    if not square['destroyed'] and not square['is_center']:
                        square['color'] = random.choice(self.rubiks_colors)

                # Clear special attacks
                self.green_laser = None
                self.green_laser_warning = False  # Reset warning state
                self.last_white_ball_time = 0  # Reset white ball cooldown

        return []

    def shoot(self, players, sound_manager=None):
        """Generate attacks based on current color"""
        if self.destruction_complete or self.current_phase != 'attack':
            return []

        bullets = []
        current_time = pygame.time.get_ticks()

        # Get closest alive player
        alive_players = [p for p in players if p.is_alive]
        if not alive_players:
            return []

        closest_player = min(alive_players, key=lambda p: math.hypot(
            p.x + p.width // 2 - self.center_x,
            p.y + p.height // 2 - self.center_y
        ))
        target_x = closest_player.x + closest_player.width // 2
        target_y = closest_player.y + closest_player.height // 2

        # Attack based on current color
        if self.current_attack_color == (255, 0, 0):  # Red - spinning squares
            if current_time - self.last_attack_time >= self.red_cooldown:
                bullet = SpinningRedSquare(self.center_x, self.center_y, target_x, target_y, 4.0)
                bullets.append(bullet)
                self.last_attack_time = current_time

                if sound_manager:
                    sound_manager.play_sound('enemy_shoot', volume_override=0.4)

        elif self.current_attack_color == (0, 0, 255):  # Blue - rapid fire bullets
            if current_time - self.last_attack_time >= self.blue_cooldown:
                bullet = BlueBullet(self.center_x, self.center_y, target_x, target_y, 5.0)
                bullets.append(bullet)
                self.last_attack_time = current_time

                if sound_manager:
                    sound_manager.play_sound('enemy_shoot', volume_override=0.3)

        elif self.current_attack_color == (0, 255, 0):  # Green - laser beam
            if self.green_laser is None and not self.green_laser_warning:
                # Start warning phase
                self.green_laser_warning = True
                self.green_laser_warning_start_time = current_time
            elif self.green_laser_warning and self.green_laser is None:
                # Check if warning is complete
                warning_elapsed = current_time - self.green_laser_warning_start_time
                if warning_elapsed >= self.green_warning_duration:
                    # Fire laser - duration is remaining time in attack phase after warning
                    remaining_duration = self.attack_phase_duration - self.green_warning_duration
                    self.green_laser = GreenLaser(self, remaining_duration)
                    bullets.append(self.green_laser)
                    self.green_laser_warning = False  # Reset warning

                    if sound_manager:
                        sound_manager.play_sound('enemy_shoot', volume_override=0.5)

        elif self.current_attack_color == (255, 255, 0):  # Yellow - slow falling balls
            if current_time - self.last_attack_time >= self.yellow_cooldown:
                # Spawn at random X position near boss
                spawn_x = self.center_x + random.randint(-100, 100)
                bullet = YellowBall(spawn_x, self.center_y, 1.0)
                bullets.append(bullet)
                self.last_attack_time = current_time

        elif self.current_attack_color == (255, 255, 255):  # White - bouncing balls
            if current_time - self.last_white_ball_time >= self.white_cooldown:
                bullet = WhiteBall(self.center_x, self.center_y, 6.0)
                bullets.append(bullet)
                self.last_white_ball_time = current_time

                if sound_manager:
                    sound_manager.play_sound('enemy_shoot', volume_override=0.5)

        elif self.current_attack_color == (255, 140, 0):  # Orange - rotating fireball spray
            if current_time - self.last_attack_time >= self.orange_cooldown:
                # Calculate "barrel" position - right edge of center square at current rotation
                # The barrel rotates with the cube, shooting fireballs outward
                barrel_distance = self.total_size // 2  # Distance from center to edge
                angle_rad = math.radians(self.rotation_angle)

                # Barrel position rotates around center
                barrel_x = self.center_x + math.cos(angle_rad) * barrel_distance
                barrel_y = self.center_y + math.sin(angle_rad) * barrel_distance

                # Shoot fireball in the direction the barrel is pointing
                bullet = OrangeFireball(barrel_x, barrel_y, self.rotation_angle, 5.0)
                bullets.append(bullet)
                self.last_attack_time = current_time

                if sound_manager:
                    sound_manager.play_sound('enemy_shoot', volume_override=0.4)

        return bullets

    def get_rotated_square_corners(self, row, col, size_override=None):
        """Calculate the 4 corners of a square after rotation"""
        # Use override size if provided (for enlarged center square in final phase)
        square_size = size_override if size_override is not None else self.square_size

        # Local position relative to grid (before rotation)
        # Center the enlarged square around its normal position
        local_x = col * self.square_size
        local_y = row * self.square_size

        # If using override size, offset to center it
        if size_override is not None:
            offset = (size_override - self.square_size) / 2
            local_x -= offset
            local_y -= offset

        # Calculate 4 corners of the square (before rotation)
        corners = [
            (local_x, local_y),
            (local_x + square_size, local_y),
            (local_x + square_size, local_y + square_size),
            (local_x, local_y + square_size)
        ]

        # Rotate each corner around grid center
        grid_center_x = self.total_size // 2
        grid_center_y = self.total_size // 2

        rotated_corners = []
        angle_rad = math.radians(self.rotation_angle)

        for corner_x, corner_y in corners:
            # Translate to origin (relative to grid center)
            rel_x = corner_x - grid_center_x
            rel_y = corner_y - grid_center_y

            # Rotate
            rotated_x = rel_x * math.cos(angle_rad) - rel_y * math.sin(angle_rad)
            rotated_y = rel_x * math.sin(angle_rad) + rel_y * math.cos(angle_rad)

            # Translate back and add boss position
            final_x = rotated_x + grid_center_x + self.x
            final_y = rotated_y + grid_center_y + self.y

            rotated_corners.append((final_x, final_y))

        return rotated_corners

    def point_in_polygon(self, point, polygon):
        """Check if a point is inside a polygon using ray casting"""
        x, y = point
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def take_turret_damage(self, turret_index, damage=1):
        """Not used for this boss"""
        return False

    def take_main_damage(self, damage=1):
        """Check if bullet hit any square (including center)"""
        # This will be called with a bullet position
        # We need to check collision with rotated squares
        # Note: The game engine will need to pass bullet rect
        return False

    def take_square_damage(self, bullet_rect, damage=1):
        """Check if bullet hit any square and apply damage"""
        bullet_center = (bullet_rect.centerx, bullet_rect.centery)

        # Check if only center square remains (final phase)
        only_center_remains = all(sq['destroyed'] for sq in self.squares if not sq['is_center'])

        # Check each square
        for square in self.squares:
            if square['destroyed']:
                continue

            # Final phase: use enlarged size for center square
            size_override = None
            if square['is_center'] and only_center_remains:
                size_override = 100  # Double from 50px to 100px

            # Get rotated corners for this square (with size override for final phase)
            corners = self.get_rotated_square_corners(square['row'], square['col'], size_override)

            # Check if bullet center is inside this square's polygon
            if self.point_in_polygon(bullet_center, corners):
                square['health'] -= damage

                if square['health'] <= 0:
                    square['destroyed'] = True

                    # Create particle explosion
                    self.create_square_explosion(square, size_override)

                    # Check if center was destroyed (win condition)
                    if square['is_center']:
                        self.start_destruction()

                return True  # Return true if we hit ANY square (damaged or destroyed)

        return False

    def create_square_explosion(self, square, size_override=None):
        """Create particle explosion for destroyed square"""
        # Get center of square (use size override for enlarged final phase center)
        corners = self.get_rotated_square_corners(square['row'], square['col'], size_override)
        center_x = sum(c[0] for c in corners) / 4
        center_y = sum(c[1] for c in corners) / 4

        # Create more particles for enlarged squares
        num_particles = 30 if size_override else 15

        # Create particles (similar to enemy explosions)
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 4)
            particle = {
                'x': center_x,
                'y': center_y,
                'vel_x': math.cos(angle) * speed,
                'vel_y': math.sin(angle) * speed,
                'life': random.randint(30, 60),
                'color': square['color'],
                'size': random.randint(2, 5)
            }
            self.explosion_effects.append(particle)

    def get_turret_rects(self):
        """Return rects for all non-destroyed squares (for hit detection)"""
        # Check if only center square remains (final phase)
        only_center_remains = all(sq['destroyed'] for sq in self.squares if not sq['is_center'])

        rects = []
        for i, square in enumerate(self.squares):
            if not square['destroyed']:
                # Final phase: use enlarged size for center square
                size_override = None
                if square['is_center'] and only_center_remains:
                    size_override = 100  # Double from 50px to 100px

                # Get rotated corners (with size override for final phase)
                corners = self.get_rotated_square_corners(square['row'], square['col'], size_override)

                # Calculate bounding box for the rotated square
                min_x = min(c[0] for c in corners)
                max_x = max(c[0] for c in corners)
                min_y = min(c[1] for c in corners)
                max_y = max(c[1] for c in corners)

                rect = pygame.Rect(int(min_x), int(min_y), int(max_x - min_x), int(max_y - min_y))
                rects.append((i, rect, square))  # Return index, rect, and square data

        return rects

    def get_main_body_rect(self):
        """Return None - use get_turret_rects for all squares"""
        return None

    def start_destruction(self):
        """Start boss destruction sequence"""
        self.destruction_complete = True
        self.destruction_start_time = pygame.time.get_ticks()

        # Create final explosion
        self.create_final_explosion()

    def is_destruction_complete(self):
        """Check if destruction animation is complete"""
        if not self.destruction_complete:
            return False
        return pygame.time.get_ticks() - self.destruction_start_time > 2000  # 2 second animation

    def create_final_explosion(self):
        """Create large explosion effect when boss is destroyed"""
        particles = []

        # Create many particles from center
        for _ in range(50):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            particle = {
                'x': self.center_x,
                'y': self.center_y,
                'vel_x': math.cos(angle) * speed,
                'vel_y': math.sin(angle) * speed,
                'life': random.randint(60, 120),
                'color': random.choice(self.rubiks_colors + [self.center_color]),
                'size': random.randint(3, 8),
                'radius': random.randint(10, 30),
                'growth': random.uniform(0.5, 2)
            }
            self.explosion_effects.append(particle)

        return particles

    def draw_cracks_on_square(self, screen, square, corners, health_ratio, size_override=None):
        """Draw progressive crack lines on a square based on damage - rotates with square"""
        # Get center of square in world space
        center_x = sum(c[0] for c in corners) / 4
        center_y = sum(c[1] for c in corners) / 4

        # Calculate scale factor for enlarged squares
        scale = size_override / self.square_size if size_override else 1.0
        actual_size = size_override if size_override else self.square_size

        # Determine crack level (0 = no cracks, 3 = heavily cracked)
        # Using 25% increments: 75%, 50%, 25%
        if health_ratio > 0.75:
            return  # No cracks yet
        elif health_ratio > 0.5:
            crack_level = 1  # First crack at 75%
        elif health_ratio > 0.25:
            crack_level = 2  # Second crack at 50%
        else:
            crack_level = 3  # Third crack at 25%

        # Draw crack lines - calculate in local space, then rotate
        crack_color = (50, 50, 50)  # Dark gray cracks

        # Helper function to transform local point to world space (rotated and scaled)
        def rotate_point(local_x, local_y):
            # Scale the coordinates first (from 0-50 to 0-actual_size)
            scaled_x = local_x * scale
            scaled_y = local_y * scale

            # Convert from local square coords to centered coords
            rel_x = scaled_x - actual_size // 2
            rel_y = scaled_y - actual_size // 2

            # Rotate by current rotation angle
            angle_rad = math.radians(self.rotation_angle)
            rotated_x = rel_x * math.cos(angle_rad) - rel_y * math.sin(angle_rad)
            rotated_y = rel_x * math.sin(angle_rad) + rel_y * math.cos(angle_rad)

            # Translate to world position
            world_x = center_x + rotated_x
            world_y = center_y + rotated_y
            return (world_x, world_y)

        # Scale line thickness with square size
        thick_line = max(2, int(2 * scale))
        thin_line = max(1, int(1 * scale))

        if crack_level >= 1:
            # First crack - diagonal from edge to edge with organic variation
            start = rotate_point(2, 2)
            mid1 = rotate_point(20, 22)
            mid2 = rotate_point(30, 28)
            end = rotate_point(48, 48)
            pygame.draw.line(screen, crack_color, start, mid1, thick_line)
            pygame.draw.line(screen, crack_color, mid1, mid2, thick_line)
            pygame.draw.line(screen, crack_color, mid2, end, thick_line)

        if crack_level >= 2:
            # Second crack - another diagonal edge to edge with branching
            start = rotate_point(48, 2)
            mid1 = rotate_point(32, 18)
            mid2 = rotate_point(18, 32)
            end = rotate_point(2, 48)
            pygame.draw.line(screen, crack_color, start, mid1, thick_line)
            pygame.draw.line(screen, crack_color, mid1, mid2, thick_line)
            pygame.draw.line(screen, crack_color, mid2, end, thick_line)

            # Branch from middle extending to edge
            branch_start = rotate_point(25, 25)
            branch_end = rotate_point(48, 8)
            pygame.draw.line(screen, crack_color, branch_start, branch_end, thin_line)

        if crack_level >= 3:
            # Third set - edge to edge cracks with curves
            # Horizontal crack from left edge to right edge
            start = rotate_point(0, 25)
            mid1 = rotate_point(15, 20)
            mid2 = rotate_point(35, 30)
            end = rotate_point(50, 25)
            pygame.draw.line(screen, crack_color, start, mid1, thick_line)
            pygame.draw.line(screen, crack_color, mid1, mid2, thick_line)
            pygame.draw.line(screen, crack_color, mid2, end, thick_line)

            # Vertical crack from top edge to bottom edge
            start = rotate_point(25, 0)
            mid1 = rotate_point(30, 15)
            mid2 = rotate_point(20, 35)
            end = rotate_point(25, 50)
            pygame.draw.line(screen, crack_color, start, mid1, thick_line)
            pygame.draw.line(screen, crack_color, mid1, mid2, thick_line)
            pygame.draw.line(screen, crack_color, mid2, end, thick_line)

            # More branches extending to edges
            b1_start = rotate_point(25, 25)
            b1_end = rotate_point(2, 40)
            pygame.draw.line(screen, crack_color, b1_start, b1_end, thin_line)

            b2_start = rotate_point(25, 25)
            b2_end = rotate_point(40, 2)
            pygame.draw.line(screen, crack_color, b2_start, b2_end, thin_line)

    def draw(self, screen):
        """Draw the Rubik's Cube boss"""
        if self.destruction_complete:
            # Draw explosion particles
            for particle in self.explosion_effects:
                if 'radius' in particle:
                    # Expanding circle explosion
                    pygame.draw.circle(screen, particle['color'],
                                     (int(particle['x']), int(particle['y'])),
                                     int(particle['radius']))
                else:
                    # Regular particle
                    pygame.draw.circle(screen, particle['color'],
                                     (int(particle['x']), int(particle['y'])),
                                     particle['size'])
            return

        # Green laser warning flash effect
        show_warning_flash = False
        warning_flash_color = None
        if self.green_laser_warning:
            current_time = pygame.time.get_ticks()
            warning_elapsed = current_time - self.green_laser_warning_start_time
            warning_progress = warning_elapsed / self.green_warning_duration  # 0.0 to 1.0

            # Flash interval decreases from 500ms to 50ms (faster and faster)
            flash_interval = max(50, 500 - (warning_progress * 450))  # 500ms -> 50ms, clamped at 50
            flash_on = (warning_elapsed % int(flash_interval)) < (int(flash_interval) / 2)

            if flash_on:
                show_warning_flash = True
                # Flash yellow/white (very visible against green)
                warning_flash_color = (255, 255, 0) if (warning_elapsed // 100) % 2 == 0 else (255, 255, 255)

        # Check if only center square remains (final phase)
        only_center_remains = all(sq['destroyed'] for sq in self.squares if not sq['is_center'])

        # Draw each square with rotation
        for square in self.squares:
            if square['destroyed']:
                continue

            # Final phase: enlarge center square and change behavior
            size_override = None
            if square['is_center'] and only_center_remains:
                size_override = 100  # Double from 50px to 100px

            # Get rotated corners (with size override for final phase center)
            corners = self.get_rotated_square_corners(square['row'], square['col'], size_override)

            # Determine color to draw
            if square['is_center'] and only_center_remains:
                # Final phase center: use attack color or light blue during mixed phase
                if self.current_phase == 'attack' and self.current_attack_color:
                    base_color = self.current_attack_color
                else:
                    base_color = self.center_color  # Light blue during mixed phase

                # Add slow pulsing flash effect
                current_time = pygame.time.get_ticks()
                pulse = (math.sin(current_time / 500) + 1) / 2  # 0.0 to 1.0, slow pulse
                flash_intensity = int(pulse * 100)  # 0 to 100

                # Brighten the color based on pulse
                draw_color = tuple(min(255, c + flash_intensity) for c in base_color)
            elif show_warning_flash and not square['is_center']:
                draw_color = warning_flash_color  # Flash yellow/white during warning
            else:
                draw_color = square['color']

            # Draw the square as a polygon
            pygame.draw.polygon(screen, draw_color, corners)

            # Draw thick warning border during warning phase
            if self.green_laser_warning and not square['is_center']:
                pygame.draw.polygon(screen, (255, 255, 0), corners, 4)  # Thick yellow border
            else:
                # Draw normal black border
                pygame.draw.polygon(screen, BLACK, corners, 2)

            # Draw cracks on damaged squares
            health_ratio = square['health'] / square['max_health']
            if health_ratio < 1.0:
                self.draw_cracks_on_square(screen, square, corners, health_ratio, size_override)

        # Draw explosion particles on top
        for particle in self.explosion_effects:
            if 'radius' not in particle:  # Only draw small particles during combat
                pygame.draw.circle(screen, particle['color'],
                                 (int(particle['x']), int(particle['y'])),
                                 particle['size'])

        # Draw center cube health bar at top (like other bosses)
        center_square = next((s for s in self.squares if s['is_center']), None)
        if center_square and not center_square['destroyed']:
            bar_width = 600
            bar_height = 30
            bar_x = SCREEN_WIDTH // 2 - bar_width // 2
            bar_y = 60

            health_ratio = center_square['health'] / center_square['max_health']

            # Background (red)
            pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
            # Health (cyan/light blue to match center square color)
            pygame.draw.rect(screen, self.center_color, (bar_x, bar_y, int(bar_width * health_ratio), bar_height))
            # Border
            pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 3)

            # Label
            font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 14)
            label = f"RUBIK'S CUBE CORE: {int(health_ratio * 100)}%"
            text = font.render(label, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, bar_y - 20))
            screen.blit(text, text_rect)

        # Update particles
        for particle in self.explosion_effects[:]:
            particle['x'] += particle.get('vel_x', 0)
            particle['y'] += particle.get('vel_y', 0)
            particle['life'] -= 1

            if particle['life'] <= 0:
                self.explosion_effects.remove(particle)


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
        
        font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 14)
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
    def __init__(self, x, y, max_block_health=1):
        self.x = x
        self.y = y
        self.width = 90
        self.height = 60
        self.max_block_health = max_block_health  # 1 = normal, 2 = reinforced level 1, 3 = reinforced level 2
        self.block_health = {}  # Dictionary mapping block positions to health
        self.create_barrier()

    def create_barrier(self):
        for row in range(5):
            for col in range(8):
                if not (row == 0 and (col == 0 or col == 7)) and not (row == 1 and (col <= 1 or col >= 6)):
                    block_x = self.x + col * 11
                    block_y = self.y + row * 12
                    block = pygame.Rect(block_x, block_y, 11, 12)
                    # Store block with full health
                    self.block_health[tuple([block.x, block.y, block.width, block.height])] = self.max_block_health

    def check_collision(self, bullet_rect):
        for block_key, health in list(self.block_health.items()):
            block = pygame.Rect(block_key[0], block_key[1], block_key[2], block_key[3])
            if block.colliderect(bullet_rect):
                # Decrease health instead of immediate removal
                self.block_health[block_key] -= 1
                if self.block_health[block_key] <= 0:
                    del self.block_health[block_key]
                return True
        return False

    def draw(self, screen):
        for block_key, health in self.block_health.items():
            block = pygame.Rect(block_key[0], block_key[1], block_key[2], block_key[3])
            # Color based on remaining health
            if health >= self.max_block_health:
                color = GREEN  # Full health
            elif health == 2:
                color = YELLOW  # 2 hits remaining (for level 2 reinforced)
            elif health == 1:
                if self.max_block_health == 3:
                    color = RED  # 1 hit remaining (for level 2 reinforced)
                elif self.max_block_health == 2:
                    color = YELLOW  # 1 hit remaining (for level 1 reinforced)
                else:
                    color = GREEN  # Should not happen for normal barriers
            else:
                color = GREEN  # Fallback
            pygame.draw.rect(screen, color, block)

class ProfileNameInputScreen:
    """Screen for entering a profile name (similar to NameInputScreen)"""
    def __init__(self, screen, sound_manager, key_bindings=None):
        self.screen = screen
        self.sound_manager = sound_manager
        self.key_bindings = key_bindings if key_bindings else {}
        self.font_large = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 36)
        self.font_medium = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 24)
        self.font_small = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 20)

        # Name input system
        self.max_name_length = 15
        self.min_name_length = 3
        self.name = ["A"] * self.max_name_length
        self.name_length = self.min_name_length  # Start with 3 characters
        self.current_position = 0
        self.alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -"
        self.current_letter_index = [0] * self.max_name_length
        self.input_mode = "controller"
        self.keyboard_name = ""
        self.ok_selected = False

        # Starfield background
        self.starfield = StarField(direction='horizontal')

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
                        self.sound_manager.play_sound('menu_select')
                        return self.keyboard_name.strip()[:self.max_name_length]
                    return None
                elif event.key == pygame.K_BACKSPACE:
                    self.keyboard_name = self.keyboard_name[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.sound_manager.play_sound('menu_select')
                    return "cancel"
                elif len(self.keyboard_name) < self.max_name_length and event.unicode.isprintable():
                    self.keyboard_name += event.unicode.upper()

            elif event.type == pygame.JOYBUTTONDOWN:
                self.input_mode = "controller"
                fire_button = self.key_bindings.get('player1_fire_button', 0)
                if isinstance(fire_button, int) and event.button == fire_button:
                    self.sound_manager.play_sound('menu_select')
                    if self.ok_selected:
                        return "".join(self.name[:self.name_length]).strip()
                    else:
                        if self.current_position < self.name_length - 1:
                            self.current_position += 1
                        else:
                            self.ok_selected = True
                elif event.button == 1:  # B button - cancel or go back
                    if self.ok_selected:
                        self.ok_selected = False
                        self.current_position = self.name_length - 1
                    elif self.current_position > 0:
                        self.current_position -= 1
                    else:
                        self.sound_manager.play_sound('menu_select')
                        return "cancel"
                elif event.button == 2:  # X button - increase length
                    if self.name_length < self.max_name_length:
                        self.name_length += 1
                elif event.button == 3:  # Y button - decrease length
                    if self.name_length > self.min_name_length:
                        self.name_length -= 1
                        if self.current_position >= self.name_length:
                            self.current_position = self.name_length - 1

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
                        self.current_position = self.name_length - 1
                    elif self.current_position > 0:
                        self.current_position -= 1
                elif event.value[0] == 1:  # Right
                    if self.current_position < self.name_length - 1:
                        self.current_position += 1
                    else:
                        self.ok_selected = True

            elif event.type == pygame.JOYAXISMOTION:
                self.input_mode = "controller"
                threshold = 0.5
                if event.axis == 1:  # Y-axis
                    if event.value < -threshold:  # Up
                        if not self.ok_selected:
                            self.current_letter_index[self.current_position] = (
                                self.current_letter_index[self.current_position] - 1
                            ) % len(self.alphabet)
                            self.name[self.current_position] = self.alphabet[self.current_letter_index[self.current_position]]
                    elif event.value > threshold:  # Down
                        if not self.ok_selected:
                            self.current_letter_index[self.current_position] = (
                                self.current_letter_index[self.current_position] + 1
                            ) % len(self.alphabet)
                            self.name[self.current_position] = self.alphabet[self.current_letter_index[self.current_position]]
                elif event.axis == 0:  # X-axis
                    if event.value < -threshold:  # Left
                        if self.ok_selected:
                            self.ok_selected = False
                            self.current_position = self.name_length - 1
                        elif self.current_position > 0:
                            self.current_position -= 1
                    elif event.value > threshold:  # Right
                        if self.current_position < self.name_length - 1:
                            self.current_position += 1
                        else:
                            self.ok_selected = True

        return None

    def draw(self):
        self.screen.fill(BLACK)

        # Update and draw starfield background
        self.starfield.update(parallax_active=True)
        self.starfield.draw(self.screen)

        # Title
        title_text = self.font_large.render("SAVE PROFILE", True, GREEN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title_text, title_rect)

        # Input method indicator
        if self.input_mode == "keyboard":
            prompt_text = self.font_medium.render("Enter profile name:", True, WHITE)
            prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, 400))
            self.screen.blit(prompt_text, prompt_rect)

            name_display = self.keyboard_name + "_" if len(self.keyboard_name) < self.max_name_length else self.keyboard_name
            name_text = self.font_large.render(name_display, True, CYAN)
            name_rect = name_text.get_rect(center=(SCREEN_WIDTH // 2, 500))

            box_rect = name_rect.inflate(40, 20)
            pygame.draw.rect(self.screen, WHITE, box_rect, 3)
            self.screen.blit(name_text, name_rect)

            inst_text = self.font_small.render("Type name and press ENTER (ESC to cancel)", True, GRAY)
            inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, 620))
            self.screen.blit(inst_text, inst_rect)

        else:
            prompt_text = self.font_medium.render("Enter profile name:", True, WHITE)
            prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
            self.screen.blit(prompt_text, prompt_rect)

            # Calculate letter spacing based on name length
            letter_spacing = min(100, 800 // self.name_length)
            start_x = SCREEN_WIDTH // 2 - (letter_spacing * (self.name_length - 1)) // 2

            for i in range(self.name_length):
                x = start_x + i * letter_spacing
                color = YELLOW if i == self.current_position and not self.ok_selected else WHITE

                if i == self.current_position and not self.ok_selected:
                    box_rect = pygame.Rect(x - 30, 420, 60, 60)
                    pygame.draw.rect(self.screen, YELLOW, box_rect, 3)

                letter_text = self.font_large.render(self.name[i], True, color)
                letter_rect = letter_text.get_rect(center=(x, 450))
                self.screen.blit(letter_text, letter_rect)

            ok_color = YELLOW if self.ok_selected else WHITE
            ok_text = self.font_medium.render("OK", True, ok_color)
            ok_rect = ok_text.get_rect(center=(SCREEN_WIDTH // 2, 570))

            if self.ok_selected:
                box_rect = ok_rect.inflate(40, 20)
                pygame.draw.rect(self.screen, YELLOW, box_rect, 3)

            self.screen.blit(ok_text, ok_rect)

            instructions = [
                "D-pad Up/Down: Change letter",
                "D-pad Left/Right: Move cursor",
                "A: Confirm/Next | B: Back/Cancel",
                "X: Add letter | Y: Remove letter"
            ]

            for i, inst in enumerate(instructions):
                inst_text = self.font_small.render(inst, True, GRAY)
                inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, 680 + i * 35))
                self.screen.blit(inst_text, inst_rect)

        pygame.display.flip()

class ProfileSelectionScreen:
    """Screen for selecting a profile to load"""
    def __init__(self, screen, sound_manager, profile_manager, key_bindings=None):
        self.screen = screen
        self.sound_manager = sound_manager
        self.profile_manager = profile_manager
        self.key_bindings = key_bindings if key_bindings else {}
        self.font_large = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 36)
        self.font_medium = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 24)
        self.font_small = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 18)

        self.profile_names = profile_manager.get_profile_names()
        self.profile_names.append("Cancel")  # Add cancel option
        self.selected_index = 0

        # Starfield background
        self.starfield = StarField(direction='horizontal')

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.sound_manager.play_sound('menu_change')
                    self.selected_index = (self.selected_index - 1) % len(self.profile_names)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.sound_manager.play_sound('menu_change')
                    self.selected_index = (self.selected_index + 1) % len(self.profile_names)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.sound_manager.play_sound('menu_select')
                    selected_name = self.profile_names[self.selected_index]
                    if selected_name == "Cancel":
                        return "cancel"
                    return selected_name
                elif event.key == pygame.K_ESCAPE:
                    self.sound_manager.play_sound('menu_select')
                    return "cancel"
            elif event.type == pygame.JOYBUTTONDOWN:
                fire_button = self.key_bindings.get('player1_fire_button', 0)
                if isinstance(fire_button, int) and event.button == fire_button:
                    self.sound_manager.play_sound('menu_select')
                    selected_name = self.profile_names[self.selected_index]
                    if selected_name == "Cancel":
                        return "cancel"
                    return selected_name
                elif event.button == 1:  # B button
                    self.sound_manager.play_sound('menu_select')
                    return "cancel"
            elif event.type == pygame.JOYHATMOTION:
                if event.value[1] == 1:  # Up
                    self.sound_manager.play_sound('menu_change')
                    self.selected_index = (self.selected_index - 1) % len(self.profile_names)
                elif event.value[1] == -1:  # Down
                    self.sound_manager.play_sound('menu_change')
                    self.selected_index = (self.selected_index + 1) % len(self.profile_names)
            elif event.type == pygame.JOYAXISMOTION:
                # Support joystick axis for menu navigation
                threshold = 0.5
                if event.axis == 1:  # Y-axis
                    if event.value < -threshold:  # Up
                        self.sound_manager.play_sound('menu_change')
                        self.selected_index = (self.selected_index - 1) % len(self.profile_names)
                    elif event.value > threshold:  # Down
                        self.sound_manager.play_sound('menu_change')
                        self.selected_index = (self.selected_index + 1) % len(self.profile_names)

        return None

    def draw(self):
        self.screen.fill(BLACK)

        # Update and draw starfield background
        self.starfield.update(parallax_active=True)
        self.starfield.draw(self.screen)

        # Title
        title_text = self.font_large.render("LOAD PROFILE", True, GREEN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title_text, title_rect)

        if not self.profile_names or (len(self.profile_names) == 1 and self.profile_names[0] == "Cancel"):
            # No profiles available
            no_profiles_text = self.font_medium.render("No saved profiles", True, WHITE)
            no_profiles_rect = no_profiles_text.get_rect(center=(SCREEN_WIDTH // 2, 400))
            self.screen.blit(no_profiles_text, no_profiles_rect)
        else:
            # Show profile list
            start_y = 300
            spacing = 60

            for i, profile_name in enumerate(self.profile_names):
                color = YELLOW if i == self.selected_index else WHITE
                profile_text = self.font_medium.render(profile_name, True, color)
                profile_rect = profile_text.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * spacing))
                self.screen.blit(profile_text, profile_rect)

        # Instructions
        inst_text = self.font_small.render("Up/Down: Select | Enter/A: Load | ESC/B: Cancel", True, GRAY)
        inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, 900))
        self.screen.blit(inst_text, inst_rect)

        pygame.display.flip()

class SettingsScreen:
    def __init__(self, screen, sound_manager, key_bindings, profile_manager):
        self.screen = screen
        self.sound_manager = sound_manager
        self.key_bindings = key_bindings
        self.profile_manager = profile_manager
        self.font_large = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 32)
        self.font_medium = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 20)
        self.font_small = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 16)
        self.font_tiny = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 12)

        # Options organized as (display_text, binding_key, input_type)
        self.options = [
            ("Keyboard - P1 Left", "player1_left_key", "keyboard"),
            ("Keyboard - P1 Right", "player1_right_key", "keyboard"),
            ("Keyboard - P1 Fire", "player1_fire_key", "keyboard"),
            ("Keyboard - P2 Left", "player2_left_key", "keyboard"),
            ("Keyboard - P2 Right", "player2_right_key", "keyboard"),
            ("Keyboard - P2 Fire", "player2_fire_key", "keyboard"),
            ("Controller - P1 Left", "player1_left_button", "controller"),
            ("Controller - P1 Right", "player1_right_button", "controller"),
            ("Controller - P1 Up", "player1_up_button", "controller"),
            ("Controller - P1 Down", "player1_down_button", "controller"),
            ("Controller - P1 Fire", "player1_fire_button", "controller"),
            ("Controller - P2 Left", "player2_left_button", "controller"),
            ("Controller - P2 Right", "player2_right_button", "controller"),
            ("Controller - P2 Up", "player2_up_button", "controller"),
            ("Controller - P2 Down", "player2_down_button", "controller"),
            ("Controller - P2 Fire", "player2_fire_button", "controller"),
            ("Save Profile", None, "save"),
            ("Load Profile", None, "load"),
            ("Back", None, None)
        ]
        self.selected_option = 0
        self.awaiting_input = False  # Whether we're waiting for input
        self.awaiting_input_for = None  # Which binding key is being remapped
        self.awaiting_input_type = None  # "keyboard" or "controller"

        # Message feedback system
        self.message = None
        self.message_time = 0
        self.message_duration = 2000  # Show message for 2 seconds

        # Starfield background
        self.starfield = StarField(direction='horizontal')

    def get_key_name(self, key):
        """Get a readable name for a pygame key constant"""
        name = pygame.key.name(key)
        # Capitalize and clean up the name
        if name == 'space':
            return 'SPACE'
        elif name.startswith('right'):
            return name.replace('right ', 'R').upper()
        elif name.startswith('left'):
            return name.replace('left ', 'L').upper()
        else:
            return name.upper()

    def get_controller_binding_name(self, binding):
        """Get a readable name for a controller binding"""
        if isinstance(binding, str):
            if binding == HAT_LEFT:
                return "D-pad Left"
            if binding == HAT_RIGHT:
                return "D-pad Right"
            if binding == HAT_UP:
                return "D-pad Up"
            if binding == HAT_DOWN:
                return "D-pad Down"
            if binding == AXIS_LEFT:
                return "Joystick Left"
            if binding == AXIS_RIGHT:
                return "Joystick Right"
            if binding == AXIS_UP:
                return "Joystick Up"
            if binding == AXIS_DOWN:
                return "Joystick Down"
            return binding.upper()
        return f"Button {binding}"

    def show_message(self, message):
        """Show a temporary message on screen"""
        self.message = message
        self.message_time = pygame.time.get_ticks()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if self.awaiting_input and self.awaiting_input_type == "keyboard":
                    # We're waiting for a keyboard key press to assign
                    self.key_bindings[self.awaiting_input_for] = event.key
                    self.sound_manager.play_sound('menu_select')
                    self.awaiting_input = False
                    self.awaiting_input_for = None
                    self.awaiting_input_type = None
                else:
                    # Normal menu navigation
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.sound_manager.play_sound('menu_change')
                        self.selected_option = (self.selected_option - 1) % len(self.options)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.sound_manager.play_sound('menu_change')
                        self.selected_option = (self.selected_option + 1) % len(self.options)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        selected = self.options[self.selected_option]
                        if selected[2] == "save":
                            self.sound_manager.play_sound('menu_select')
                            return "save"
                        elif selected[2] == "load":
                            self.sound_manager.play_sound('menu_select')
                            return "load"
                        elif selected[1] is None:  # Back option
                            self.sound_manager.play_sound('menu_select')
                            return "back"
                        else:
                            self.sound_manager.play_sound('menu_select')
                            self.awaiting_input = True
                            self.awaiting_input_for = selected[1]
                            self.awaiting_input_type = selected[2]
                    elif event.key == pygame.K_ESCAPE:
                        return "back"
            elif event.type == pygame.JOYBUTTONDOWN:
                if self.awaiting_input and self.awaiting_input_type == "controller":
                    # We're waiting for a controller button press to assign
                    self.key_bindings[self.awaiting_input_for] = event.button
                    self.sound_manager.play_sound('menu_select')
                    self.awaiting_input = False
                    self.awaiting_input_for = None
                    self.awaiting_input_type = None
                elif not self.awaiting_input:
                    # Normal menu navigation with controller
                    if event.button == 0:  # A button - select
                        selected = self.options[self.selected_option]
                        if selected[2] == "save":
                            self.sound_manager.play_sound('menu_select')
                            return "save"
                        elif selected[2] == "load":
                            self.sound_manager.play_sound('menu_select')
                            return "load"
                        elif selected[1] is None:  # Back option
                            self.sound_manager.play_sound('menu_select')
                            return "back"
                        else:
                            self.sound_manager.play_sound('menu_select')
                            self.awaiting_input = True
                            self.awaiting_input_for = selected[1]
                            self.awaiting_input_type = selected[2]
                    elif event.button == 1:  # B button - back
                        self.sound_manager.play_sound('menu_select')
                        return "back"
            elif event.type == pygame.JOYHATMOTION:
                if self.awaiting_input and self.awaiting_input_type == "controller":
                    if self.awaiting_input_for:
                        if event.value[0] != 0:
                            binding = HAT_LEFT if event.value[0] < 0 else HAT_RIGHT
                        elif event.value[1] != 0:
                            binding = HAT_UP if event.value[1] > 0 else HAT_DOWN
                        else:
                            binding = None

                        if binding:
                            self.key_bindings[self.awaiting_input_for] = binding
                            self.sound_manager.play_sound('menu_select')
                            self.awaiting_input = False
                            self.awaiting_input_for = None
                            self.awaiting_input_type = None
                elif not self.awaiting_input:
                    if event.value[1] == 1:  # Up
                        self.sound_manager.play_sound('menu_change')
                        self.selected_option = (self.selected_option - 1) % len(self.options)
                    elif event.value[1] == -1:  # Down
                        self.sound_manager.play_sound('menu_change')
                        self.selected_option = (self.selected_option + 1) % len(self.options)
            elif event.type == pygame.JOYAXISMOTION:
                if self.awaiting_input and self.awaiting_input_type == "controller":
                    if self.awaiting_input_for:
                        # Use a threshold to detect significant axis movement
                        threshold = 0.5
                        binding = None

                        if abs(event.value) > threshold:
                            if event.axis == 0:  # X-axis (left/right)
                                binding = AXIS_LEFT if event.value < 0 else AXIS_RIGHT
                            elif event.axis == 1:  # Y-axis (up/down)
                                binding = AXIS_UP if event.value < 0 else AXIS_DOWN

                        if binding:
                            self.key_bindings[self.awaiting_input_for] = binding
                            self.sound_manager.play_sound('menu_select')
                            self.awaiting_input = False
                            self.awaiting_input_for = None
                            self.awaiting_input_type = None
                elif not self.awaiting_input:
                    # Allow axis motion for menu navigation
                    threshold = 0.5
                    if event.axis == 1:  # Y-axis
                        if event.value < -threshold:  # Up
                            self.sound_manager.play_sound('menu_change')
                            self.selected_option = (self.selected_option - 1) % len(self.options)
                        elif event.value > threshold:  # Down
                            self.sound_manager.play_sound('menu_change')
                            self.selected_option = (self.selected_option + 1) % len(self.options)

        return None

    def draw(self):
        self.screen.fill(BLACK)

        # Update and draw starfield background
        self.starfield.update(parallax_active=True)
        self.starfield.draw(self.screen)

        # Title
        title_text = self.font_large.render("SETTINGS", True, GREEN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title_text, title_rect)

        # Check if we're awaiting input
        if self.awaiting_input:
            # Show appropriate prompt based on input type
            if self.awaiting_input_type == "keyboard":
                prompt_text = self.font_medium.render("Press any key...", True, YELLOW)
            else:
                prompt_text = self.font_medium.render("Press any button or D-pad direction...", True, YELLOW)
            prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, 500))
            self.screen.blit(prompt_text, prompt_rect)

            # Show which setting is being changed
            option_display = self.options[self.selected_option][0]
            setting_text = self.font_small.render(option_display, True, WHITE)
            setting_rect = setting_text.get_rect(center=(SCREEN_WIDTH // 2, 450))
            self.screen.blit(setting_text, setting_rect)
        else:
            # Count items in each section dynamically
            keyboard_items = [opt for opt in self.options if opt[2] == "keyboard"]
            controller_items = [opt for opt in self.options if opt[2] == "controller"]
            profile_items = [opt for opt in self.options if opt[2] in ["save", "load"]]

            # Calculate positions dynamically
            spacing = 32
            keyboard_start_y = 160
            keyboard_header_y = keyboard_start_y - 25

            controller_start_y = keyboard_start_y + len(keyboard_items) * spacing + 40
            controller_header_y = controller_start_y - 25

            profile_start_y = controller_start_y + len(controller_items) * spacing + 40
            profile_header_y = profile_start_y - 25

            back_button_y = profile_start_y + len(profile_items) * spacing + 50

            # Section headers
            keyboard_header = self.font_small.render("KEYBOARD CONTROLS", True, CYAN)
            keyboard_rect = keyboard_header.get_rect(center=(SCREEN_WIDTH // 2, keyboard_header_y))
            self.screen.blit(keyboard_header, keyboard_rect)

            controller_header = self.font_small.render("CONTROLLER INPUTS", True, CYAN)
            controller_rect = controller_header.get_rect(center=(SCREEN_WIDTH // 2, controller_header_y))
            self.screen.blit(controller_header, controller_rect)

            profile_header = self.font_small.render("PROFILE MANAGEMENT", True, CYAN)
            profile_rect = profile_header.get_rect(center=(SCREEN_WIDTH // 2, profile_header_y))
            self.screen.blit(profile_header, profile_rect)

            # Show menu options with current bindings
            keyboard_index = 0
            controller_index = 0
            profile_index = 0

            for i, option in enumerate(self.options):
                display_text, binding_key, input_type = option
                color = YELLOW if i == self.selected_option else WHITE

                if input_type == "keyboard":
                    key_name = self.get_key_name(self.key_bindings[binding_key])
                    option_text = self.font_small.render(f"{display_text}: {key_name}", True, color)
                    option_rect = option_text.get_rect(center=(SCREEN_WIDTH // 2, keyboard_start_y + keyboard_index * spacing))
                    keyboard_index += 1
                elif input_type == "controller":
                    binding_name = self.get_controller_binding_name(self.key_bindings[binding_key])
                    option_text = self.font_small.render(f"{display_text}: {binding_name}", True, color)
                    option_rect = option_text.get_rect(center=(SCREEN_WIDTH // 2, controller_start_y + controller_index * spacing))
                    controller_index += 1
                elif input_type in ["save", "load"]:
                    option_text = self.font_medium.render(display_text, True, color)
                    option_rect = option_text.get_rect(center=(SCREEN_WIDTH // 2, profile_start_y + profile_index * spacing))
                    profile_index += 1
                else:  # Back option
                    option_text = self.font_medium.render(display_text, True, color)
                    option_rect = option_text.get_rect(center=(SCREEN_WIDTH // 2, back_button_y))

                self.screen.blit(option_text, option_rect)

        # Display message if active
        if self.message:
            current_time = pygame.time.get_ticks()
            if current_time - self.message_time < self.message_duration:
                # Message is still active
                message_text = self.font_medium.render(self.message, True, GREEN)
                message_rect = message_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
                # Draw a background for the message
                bg_rect = pygame.Rect(message_rect.x - 10, message_rect.y - 5, message_rect.width + 20, message_rect.height + 10)
                pygame.draw.rect(self.screen, BLACK, bg_rect)
                pygame.draw.rect(self.screen, GREEN, bg_rect, 2)
                self.screen.blit(message_text, message_rect)
            else:
                # Message has expired
                self.message = None

        pygame.display.flip()

class TitleScreen:
    def __init__(self, screen, score_manager, sound_manager, key_bindings):
        self.screen = screen
        self.score_manager = score_manager
        self.sound_manager = sound_manager
        self.key_bindings = key_bindings
        self.font_large = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 48)
        self.font_medium = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 28)
        self.font_small = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 20)
        self.selected_option = 0

        # Check if save file exists and add Continue option if it does
        self.has_save_file = os.path.exists("savegame.json")
        if self.has_save_file:
            self.options = ["Continue", "Single Player", "Co-op", "Settings", "High Scores", "Quit"]
        else:
            self.options = ["Single Player", "Co-op", "Settings", "High Scores", "Quit"]

        self.controllers = []
        self.scan_controllers()

        # Debug code detection (up, down, left, right, right, left, down, up)
        self.debug_sequence = ["up", "down", "left", "right", "right", "left", "down", "up"]
        self.debug_index = 0

        # Starfield background with horizontal scrolling
        self.starfield = StarField(direction='horizontal')
        
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
                    selected_text = self.options[self.selected_option]
                    if selected_text == "Continue":
                        return "continue"
                    elif selected_text == "Single Player":
                        return "single"
                    elif selected_text == "Co-op":
                        return "coop"
                    elif selected_text == "Settings":
                        return "settings"
                    elif selected_text == "High Scores":
                        return "highscores"
                    elif selected_text == "Quit":
                        return "quit"
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    if self._register_debug_input("left"):
                        return "debug_menu"
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    if self._register_debug_input("right"):
                        return "debug_menu"
            elif event.type == pygame.JOYBUTTONDOWN:
                # Use the fire button from player 1 settings
                fire_button = self.key_bindings.get('player1_fire_button', 0)
                if isinstance(fire_button, int) and event.button == fire_button:
                    self.sound_manager.play_sound('menu_select')
                    selected_text = self.options[self.selected_option]
                    if selected_text == "Continue":
                        return "continue"
                    elif selected_text == "Single Player":
                        return "single"
                    elif selected_text == "Co-op":
                        return "coop"
                    elif selected_text == "Settings":
                        return "settings"
                    elif selected_text == "High Scores":
                        return "highscores"
                    elif selected_text == "Quit":
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
            elif event.type == pygame.JOYAXISMOTION:
                # Support joystick axis for menu navigation
                threshold = 0.5
                if event.axis == 1:  # Y-axis
                    if event.value < -threshold:  # Up
                        if self._register_debug_input("up"):
                            return "debug_menu"
                        self.sound_manager.play_sound('menu_change')
                        self.selected_option = (self.selected_option - 1) % len(self.options)
                    elif event.value > threshold:  # Down
                        if self._register_debug_input("down"):
                            return "debug_menu"
                        self.sound_manager.play_sound('menu_change')
                        self.selected_option = (self.selected_option + 1) % len(self.options)
                elif event.axis == 0:  # X-axis for debug sequence
                    if event.value < -threshold:  # Left
                        if self._register_debug_input("left"):
                            return "debug_menu"
                    elif event.value > threshold:  # Right
                        if self._register_debug_input("right"):
                            return "debug_menu"

        return None
        
    def draw(self):
        self.screen.fill(BLACK)

        # Update and draw starfield background with parallax effect
        self.starfield.update(parallax_active=True)
        self.starfield.draw(self.screen)

        # Title
        title_text = self.font_large.render("PLACE INVADERS", True, GREEN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title_text, title_rect)

        # Menu options
        for i, option in enumerate(self.options):
            color = YELLOW if i == self.selected_option else WHITE
            option_text = self.font_medium.render(option, True, color)
            option_rect = option_text.get_rect(center=(SCREEN_WIDTH // 2, 380 + i * 70))
            self.screen.blit(option_text, option_rect)

        # High score previews
        single_best = self.score_manager.get_best_score(False)
        coop_best = self.score_manager.get_best_score(True)

        preview_y = 880
        if single_best:
            single_text = self.font_small.render(f"Best Single: {single_best['score']:,} - {single_best['name']}", True, CYAN)
            single_rect = single_text.get_rect(center=(SCREEN_WIDTH // 2, preview_y))
            self.screen.blit(single_text, single_rect)
            preview_y += 40

        if coop_best:
            coop_text = self.font_small.render(f"Best Co-op: {coop_best['score']:,} - {coop_best['name']}", True, CYAN)
            coop_rect = coop_text.get_rect(center=(SCREEN_WIDTH // 2, preview_y))
            self.screen.blit(coop_text, coop_rect)

        pygame.display.flip()

class DebugMenu:
    def __init__(self, screen, sound_manager, key_bindings=None):
        self.screen = screen
        self.sound_manager = sound_manager
        self.key_bindings = key_bindings if key_bindings else {}
        self.font_large = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 36)
        self.font_medium = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 24)
        self.font_small = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 16)
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
            'reinforced_barriers_level': 2,
            'auto_fire_level': 1,
        }

        self.config = {
            'mode': 'single',
            'start_level': 1,
            'start_score': 0,
            'xp_level': 1,
            'xp_current': 0,
            'force_boss_level': False,
            'force_boss_type': 'Random',
            'boss_encounter_level': 1,
            'force_rubiks_attack_color': 'Random',
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
            {'type': 'label', 'label': 'Boss Testing'},
            {'type': 'bool', 'label': 'Force Boss Level', 'path': ('force_boss_level',)},
            {'type': 'choice', 'label': 'Force Boss Type', 'choices': ['Random', 'Boss', 'AlienOverlordBoss', 'BulletHellBoss', 'AsteroidFieldBoss', 'RubiksCubeBoss'], 'path': ('force_boss_type',)},
            {'type': 'int', 'label': 'Boss Encounter Level', 'path': ('boss_encounter_level',), 'min': 1, 'max': 50, 'step': 1},
        ]

        # Conditionally add Rubik's Cube attack color selector if RubiksCubeBoss is selected
        if self.config.get('force_boss_type') == 'RubiksCubeBoss':
            self.menu_items.append({
                'type': 'choice',
                'label': 'Force Attack Color',
                'choices': ['Random', 'Red', 'Blue', 'Green', 'Yellow', 'White', 'Orange'],
                'path': ('force_rubiks_attack_color',)
            })

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
        # Store old boss type to detect changes
        old_boss_type = self.config.get('force_boss_type')

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

        # Rebuild menu if boss type changed (to show/hide Rubik's attack color option)
        new_boss_type = self.config.get('force_boss_type')
        if old_boss_type != new_boss_type:
            current_selection = self.selected_index
            self._build_menu_items()
            # Try to keep selection close to where it was
            self.selected_index = min(current_selection, len(self.menu_items) - 1)
            self._move_selection(0)  # Ensure valid selection

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
            elif event.type == pygame.JOYAXISMOTION:
                # Support joystick axis for menu navigation
                threshold = 0.5
                if event.axis == 1:  # Y-axis
                    if event.value < -threshold:  # Up
                        self._move_selection(-1)
                    elif event.value > threshold:  # Down
                        self._move_selection(1)
                elif event.axis == 0:  # X-axis
                    if event.value < -threshold:  # Left
                        self._adjust_value(self.menu_items[self.selected_index], -1)
                    elif event.value > threshold:  # Right
                        self._adjust_value(self.menu_items[self.selected_index], 1)
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 1:  # B button - back
                    return 'back', None
                else:
                    fire_button = self.key_bindings.get('player1_fire_button', 0)
                    if isinstance(fire_button, int) and event.button == fire_button:
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
        self.font_huge = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 48)
        self.font_large = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 36)
        self.font_medium = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 24)
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
    def __init__(self, score_manager, sound_manager, key_bindings=None):
        try:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        except:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        pygame.display.set_caption("Place Invaders")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        self.score = 0
        self.level = 1
        self.total_enemies_killed = 0
        self.coop_mode = False

        # DEBUG: Track powerup drops per level
        self.powerups_spawned_this_level = 0
        self.enemies_killed_this_level = 0
        self.score_manager = score_manager
        self.sound_manager = sound_manager

        # Key bindings for player controls
        if key_bindings is None:
            key_bindings = {
                'player1_fire_key': pygame.K_SPACE,
                'player1_left_key': pygame.K_LEFT,
                'player1_right_key': pygame.K_RIGHT,
                'player2_fire_key': pygame.K_RCTRL,
                'player2_left_key': pygame.K_a,
                'player2_right_key': pygame.K_d,
                'player1_left_button': 13,  # D-pad left
                'player1_right_button': 14,  # D-pad right
                'player1_up_button': 11,  # D-pad up
                'player1_down_button': 12,  # D-pad down
                'player1_fire_button': 0,  # A button
                'player2_left_button': 13,  # D-pad left
                'player2_right_button': 14,  # D-pad right
                'player2_up_button': 11,  # D-pad up
                'player2_down_button': 12,  # D-pad down
                'player2_fire_button': 0  # A button
            }
        self.key_bindings = key_bindings
        self.awaiting_name_input = False
        self.awaiting_level_up = False
        self.pending_level_up = False  # Track if player leveled up during current level
        self.player_xp_level = 1  # Track player's XP level separately from game level
        self.showing_ufo_warning = False
        self.ufo_warning_screen = None
        self.showing_stats_screen = False  # Flag for showing stats on high score screen
        self.stats_screen = None  # Will hold the HighScoreScreen with stats
        
        # ADDED: Game over timing and input delay
        self.game_over_time = 0
        self.input_delay_duration = 1000  # 1 second delay
        
        # XP and upgrade system
        self.xp_system = XPSystem()
        self.last_permanent_powerup = {}  # Track last permanent powerup per player to prevent consecutive repeats

        # Player statistics tracking
        self.player_stats = []  # Will be populated when players are created

        # Visual feedback
        self.floating_texts = []
        
        # Boss system
        self.current_boss = None
        self.is_boss_level = False
        self.boss_shield_granted = False
        self.boss_encounters = {Boss: 0, AlienOverlordBoss: 0, BulletHellBoss: 0, AsteroidFieldBoss: 0, RubiksCubeBoss: 0}
        self.last_boss_type = None  # Track last boss to prevent consecutive repeats

        # Debug overrides for boss testing
        self.debug_force_boss_level = False
        self.debug_force_boss_type = None
        self.debug_boss_encounter_level = None
        
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
        self.player_explosion_particles = []
        self.muzzle_flash_particles = []
        self.muzzle_flash_flashes = []  # Bright expanding circles for muzzle flash
        self.screen_shake_intensity = 0
        self.screen_shake_duration = 0
        self.screen_flash_intensity = 0
        self.screen_flash_duration = 0
        self.boss_explosion_waves = []
        self.available_bosses = [Boss, AlienOverlordBoss, BulletHellBoss, AsteroidFieldBoss, RubiksCubeBoss]

        self.font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 28)
        self.small_font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 20)
        self.tiny_font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 16)
        self.powerup_font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 12)  # Small font for powerup indicators below ships

        # Starfield background
        self.starfield = StarField()

    def scan_controllers(self):
        self.controllers = []
        for i in range(pygame.joystick.get_count()):
            controller = pygame.joystick.Joystick(i)
            controller.init()
            self.controllers.append(controller)
            
    def setup_game(self, mode, debug_config=None):
        self.coop_mode = (mode == "coop")
        self.players = []
        self.player_stats = []  # Reset stats

        # Delete any existing save file when starting a new game
        if os.path.exists("savegame.json"):
            os.remove("savegame.json")

        if self.coop_mode:
            controller1 = self.controllers[0] if len(self.controllers) > 0 else None
            # Create individual upgrades for each player
            player1_upgrades = PlayerUpgrades()
            player1 = Player(SCREEN_WIDTH // 2 - 90, SCREEN_HEIGHT - 80, 1, controller1, player1_upgrades)
            player1.coop_mode = True
            self.players.append(player1)
            self.player_stats.append(PlayerStats(player_id=1))

            controller2 = self.controllers[1] if len(self.controllers) > 1 else None
            player2_upgrades = PlayerUpgrades()
            player2 = Player(SCREEN_WIDTH // 2 + 30, SCREEN_HEIGHT - 80, 2, controller2, player2_upgrades)
            player2.coop_mode = True
            self.players.append(player2)
            self.player_stats.append(PlayerStats(player_id=2))
        else:
            controller = self.controllers[0] if len(self.controllers) > 0 else None
            player_upgrades = PlayerUpgrades()
            self.players.append(Player(SCREEN_WIDTH // 2 - 30, SCREEN_HEIGHT - 80, 1, controller, player_upgrades))
            self.player_stats.append(PlayerStats(player_id=1))
            
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

        # Apply boss testing overrides
        self.debug_force_boss_level = debug_config.get('force_boss_level', False)
        boss_type_name = debug_config.get('force_boss_type', 'Random')
        if boss_type_name == 'Random':
            self.debug_force_boss_type = None
        else:
            # Map boss name to boss class
            boss_map = {
                'Boss': Boss,
                'AlienOverlordBoss': AlienOverlordBoss,
                'BulletHellBoss': BulletHellBoss,
                'AsteroidFieldBoss': AsteroidFieldBoss,
                'RubiksCubeBoss': RubiksCubeBoss
            }
            self.debug_force_boss_type = boss_map.get(boss_type_name)

        # Set boss encounter level override
        self.debug_boss_encounter_level = debug_config.get('boss_encounter_level', None)

        # Set Rubik's Cube attack color override
        self.debug_force_rubiks_attack_color = debug_config.get('force_rubiks_attack_color', 'Random')

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
                player.has_boss_shield_upgrade = True
                player.activate_boss_shield()
                player.upgrades.boss_shield_level = 1
            else:
                player.has_boss_shield_upgrade = False
                player.clear_boss_shield()
                player.upgrades.boss_shield_level = 0

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

    def save_game(self, filename="savegame.json"):
        """Save the current game state to a file"""
        save_data = {
            'coop_mode': self.coop_mode,
            'level': self.level,
            'score': self.score,
            'total_enemies_killed': self.total_enemies_killed,
            'awaiting_level_up': self.awaiting_level_up,
            'pending_level_up': self.pending_level_up,
            'xp_system': {
                'current_xp': self.xp_system.current_xp,
                'level': self.xp_system.level,
                'xp_for_next_level': self.xp_system.xp_for_next_level
            },
            'boss_encounters': {boss_class.__name__: count for boss_class, count in self.boss_encounters.items()},
            'players': [],
            'player_stats': []
        }

        # Save player data
        for player in self.players:
            # Update active_ammo_powerup with current ammo count before saving
            active_powerup = None
            if player.active_ammo_powerup:
                active_powerup = player.active_ammo_powerup.copy()
                # Update with current ammo count
                if active_powerup['type'] == 'rapid_fire':
                    active_powerup['ammo'] = player.rapid_fire_ammo
                elif active_powerup['type'] == 'multi_shot':
                    active_powerup['ammo'] = player.multi_shot_ammo

            player_data = {
                'player_id': player.player_id,
                'lives': player.lives,
                'is_alive': player.is_alive,
                'has_boss_shield_upgrade': player.has_boss_shield_upgrade,
                'boss_shield_active': player.boss_shield_active,
                'rapid_fire': player.rapid_fire,
                'rapid_fire_ammo': player.rapid_fire_ammo,
                'has_multi_shot': player.has_multi_shot,
                'multi_shot_ammo': player.multi_shot_ammo,
                'has_laser': player.has_laser,
                'active_ammo_powerup': active_powerup,
                'ammo_powerup_queue': player.ammo_powerup_queue,
                'upgrades': {
                    'shot_speed_level': player.upgrades.shot_speed_level,
                    'fire_rate_level': player.upgrades.fire_rate_level,
                    'movement_speed_level': player.upgrades.movement_speed_level,
                    'powerup_duration_level': player.upgrades.powerup_duration_level,
                    'pierce_level': player.upgrades.pierce_level,
                    'bullet_length_level': player.upgrades.bullet_length_level,
                    'barrier_phase_level': player.upgrades.barrier_phase_level,
                    'powerup_spawn_level': player.upgrades.powerup_spawn_level,
                    'boss_damage_level': player.upgrades.boss_damage_level,
                    'ammo_capacity_level': player.upgrades.ammo_capacity_level,
                    'extra_bullet_level': player.upgrades.extra_bullet_level,
                    'boss_shield_level': player.upgrades.boss_shield_level
                }
            }
            save_data['players'].append(player_data)

        # Save player stats
        for stats in self.player_stats:
            stats_data = {
                'player_id': stats.player_id,
                'enemies_killed': stats.enemies_killed,
                'shots_fired_total': stats.shots_fired_total,
                'shots_fired_normal': stats.shots_fired_normal,
                'shots_fired_rapid': stats.shots_fired_rapid,
                'shots_fired_laser': stats.shots_fired_laser,
                'shots_fired_multi': stats.shots_fired_multi,
                'invincibility_time': stats.invincibility_time,
                'permanent_upgrades_used': stats.permanent_upgrades_used,
                'deaths': stats.deaths,
                'boss_damage_dealt': stats.boss_damage_dealt,
                'bosses_fought_count': stats.bosses_fought_count,
                'bosses_fought_names': stats.bosses_fought_names,
                'final_score': stats.final_score,
                'final_xp_level': stats.final_xp_level,
                'final_xp': stats.final_xp
            }
            save_data['player_stats'].append(stats_data)

        # Write to file
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)

    def load_game(self, filename="savegame.json"):
        """Load game state from a file and setup the game"""
        with open(filename, 'r') as f:
            save_data = json.load(f)

        # Restore basic game state
        self.coop_mode = save_data['coop_mode']
        self.level = save_data['level']
        self.score = save_data['score']
        self.total_enemies_killed = save_data['total_enemies_killed']

        # Restore XP system
        self.xp_system.current_xp = save_data['xp_system']['current_xp']
        self.xp_system.level = save_data['xp_system']['level']
        self.xp_system.xp_for_next_level = save_data['xp_system']['xp_for_next_level']

        # Restore boss encounters
        from types import SimpleNamespace
        boss_class_map = {
            'Boss': Boss,
            'AlienOverlordBoss': AlienOverlordBoss,
            'BulletHellBoss': BulletHellBoss,
            'AsteroidFieldBoss': AsteroidFieldBoss
        }
        self.boss_encounters = {}
        for boss_name, count in save_data['boss_encounters'].items():
            if boss_name in boss_class_map:
                self.boss_encounters[boss_class_map[boss_name]] = count

        # Create players with saved state
        self.players = []
        self.player_stats = []

        for player_data in save_data['players']:
            player_id = player_data['player_id']
            controller = self.controllers[player_id - 1] if player_id - 1 < len(self.controllers) else None

            # Create player upgrades from saved data
            player_upgrades = PlayerUpgrades()
            for key, value in player_data['upgrades'].items():
                setattr(player_upgrades, key, value)

            # Determine player position based on mode
            if self.coop_mode:
                if player_id == 1:
                    x_pos = SCREEN_WIDTH // 2 - 90
                else:
                    x_pos = SCREEN_WIDTH // 2 + 30
            else:
                x_pos = SCREEN_WIDTH // 2 - 30

            player = Player(x_pos, SCREEN_HEIGHT - 80, player_id, controller, player_upgrades)
            player.coop_mode = self.coop_mode
            player.lives = player_data['lives']
            player.is_alive = player_data['is_alive']
            player.has_boss_shield_upgrade = player_data['has_boss_shield_upgrade']
            player.boss_shield_active = player_data['boss_shield_active']
            player.has_laser = player_data['has_laser']

            # Restore ammo power-ups with current ammo counts
            player.rapid_fire = player_data.get('rapid_fire', False)
            player.rapid_fire_ammo = player_data['rapid_fire_ammo']
            player.has_multi_shot = player_data.get('has_multi_shot', False)
            player.multi_shot_ammo = player_data['multi_shot_ammo']

            # Restore active powerup state
            if player_data.get('active_ammo_powerup'):
                player.active_ammo_powerup = player_data['active_ammo_powerup']

            player.ammo_powerup_queue = player_data.get('ammo_powerup_queue', [])

            self.players.append(player)

        # Restore player stats
        for stats_data in save_data['player_stats']:
            stats = PlayerStats(stats_data['player_id'])
            stats.enemies_killed = stats_data['enemies_killed']
            stats.shots_fired_total = stats_data['shots_fired_total']
            stats.shots_fired_normal = stats_data['shots_fired_normal']
            stats.shots_fired_rapid = stats_data['shots_fired_rapid']
            stats.shots_fired_laser = stats_data['shots_fired_laser']
            stats.shots_fired_multi = stats_data['shots_fired_multi']
            stats.invincibility_time = stats_data['invincibility_time']
            stats.permanent_upgrades_used = stats_data['permanent_upgrades_used']
            stats.deaths = stats_data['deaths']
            stats.boss_damage_dealt = stats_data['boss_damage_dealt']
            stats.bosses_fought_count = stats_data['bosses_fought_count']
            stats.bosses_fought_names = stats_data['bosses_fought_names']
            stats.final_score = stats_data['final_score']
            stats.final_xp_level = stats_data['final_xp_level']
            stats.final_xp = stats_data['final_xp']
            self.player_stats.append(stats)

        # Reset game state
        self.game_over = False

        # Restore level up state (if saved from level up screen)
        self.awaiting_level_up = save_data.get('awaiting_level_up', False)
        self.pending_level_up = save_data.get('pending_level_up', False)

        # Setup barriers and level (only if not awaiting level up)
        if not self.awaiting_level_up:
            self.create_barriers()
            self.setup_level()
        else:
            # If we're awaiting level up, we'll need to setup the level after the level up screen
            # For now just create barriers
            self.create_barriers()

    def count_bosses_before_level(self, level):
        """Count how many boss levels occur before the given level.
        Used for boss-based speed progression."""
        boss_count = 0
        boss_level = BOSS_FIRST_LEVEL
        gap = BOSS_INITIAL_GAP

        while boss_level < level:
            boss_count += 1
            gap += BOSS_GAP_INCREMENT
            boss_level += gap

        return boss_count

    def calculate_enemy_speed_for_level(self, level):
        # Enemy speed increases based on configuration
        if USE_BOSS_BASED_SPEED_PROGRESSION:
            # Speed increases after each boss defeated
            bosses_defeated = self.count_bosses_before_level(level)
            speed_increase = bosses_defeated * ENEMY_SPEED_PROGRESSION
        else:
            # Speed increases every N levels (legacy behavior)
            speed_level = ((level - 1) // ENEMY_SPEED_LEVEL_INTERVAL) + 1
            speed_increase = (speed_level - 1) * ENEMY_SPEED_PROGRESSION

        return BASE_ENEMY_SPEED + speed_increase

    def is_level_a_boss_level(self, level):
        """Determine if this level is a boss level using progressive spacing.
        First boss at configured level, then each subsequent boss requires additional levels.
        Example (defaults): 4, 9 (4+5), 15 (9+6), 22 (15+7), 30 (22+8), etc.
        """
        boss_level = BOSS_FIRST_LEVEL
        gap = BOSS_INITIAL_GAP

        while boss_level <= level:
            if boss_level == level:
                return True
            gap += BOSS_GAP_INCREMENT  # Each subsequent boss requires more levels
            boss_level += gap

        return False

    def setup_level(self):
        """Setup current level - either boss or regular enemies"""
        # Check for debug override first
        if self.debug_force_boss_level:
            self.is_boss_level = True
        else:
            self.is_boss_level = self.is_level_a_boss_level(self.level)
        self.boss_shield_granted = False

        if self.is_boss_level:
            # ADDED: Show UFO warning before boss level
            self.showing_ufo_warning = True
            self.ufo_warning_screen = UFOWarningScreen(self.screen, self.level)
            self.current_boss = None  # Don't create boss until warning is done
            self.enemies = []
        else:
            self.showing_ufo_warning = False
            self.ufo_warning_screen = None
            self.current_boss = None
            self.create_enemy_grid()

    def create_boss_instance(self):
        # Check for debug override first
        if self.debug_force_boss_type is not None:
            boss_class = self.debug_force_boss_type
        else:
            # Filter out the last boss to prevent consecutive repeats
            available = [b for b in self.available_bosses if b != self.last_boss_type]
            # If all bosses are filtered out (shouldn't happen with 4+ bosses), use all
            if not available:
                available = self.available_bosses
            boss_class = random.choice(available)
            # Track this boss for next selection
            self.last_boss_type = boss_class

        # Use debug encounter level if set, otherwise increment normally
        if self.debug_boss_encounter_level is not None:
            encounter_number = self.debug_boss_encounter_level
        else:
            self.boss_encounters[boss_class] = self.boss_encounters.get(boss_class, 0) + 1
            encounter_number = self.boss_encounters[boss_class]

        # Create boss instance
        boss = boss_class(encounter_number)

        # Apply debug forced attack color for RubiksCubeBoss
        if boss_class == RubiksCubeBoss and hasattr(self, 'debug_force_rubiks_attack_color'):
            if self.debug_force_rubiks_attack_color != 'Random':
                boss.debug_forced_attack_color = self.debug_force_rubiks_attack_color

        return boss
        
    def create_barriers(self):
        self.barriers = []
        barrier_count = 5
        barrier_spacing = SCREEN_WIDTH // (barrier_count + 1)
        # Get max barrier health from player's reinforced_barriers upgrade (1 + upgrade level)
        max_block_health = 1
        if self.players and len(self.players) > 0:
            max_block_health = 1 + self.players[0].upgrades.get_barrier_reinforcement_level()
        for i in range(barrier_count):
            barrier_x = barrier_spacing * (i + 1) - 45
            barrier_y = SCREEN_HEIGHT - 300
            self.barriers.append(Barrier(barrier_x, barrier_y, max_block_health))
            
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
        total_enemies = ENEMY_GRID_TOTAL
        remaining_enemies = len(self.enemies)
        if remaining_enemies > 0:
            if USE_THRESHOLD_PROGRESSION:
                # Threshold-based progression: precise control at specific enemy counts
                # Iterate through thresholds to find the best matching multiplier
                # (list should be sorted descending, lowest threshold = highest multiplier)
                speed_multiplier = 1.0  # Default fallback
                for threshold_enemies, multiplier in ENEMY_SPEED_THRESHOLDS:
                    if remaining_enemies <= threshold_enemies:
                        speed_multiplier = multiplier
                    # Keep iterating to find the lowest applicable threshold
            else:
                # Formula-based progression with configurable curve
                destroyed_ratio = (total_enemies - remaining_enemies) / total_enemies
                # Apply exponent to curve the progression:
                # - 1.0 = linear (default)
                # - 2.0 = quadratic (accelerates faster)
                # - 0.5 = square root (accelerates slower)
                curved_ratio = destroyed_ratio ** ENEMY_SPEED_PROGRESSION_EXPONENT
                speed_multiplier = 1 + curved_ratio * ENEMY_SPEED_MULTIPLIER_MAX

                # Legacy final threshold boost (only in formula mode)
                if remaining_enemies <= ENEMY_SPEED_FINAL_THRESHOLD:
                    extra_multiplier = (ENEMY_SPEED_FINAL_THRESHOLD - remaining_enemies + 1) * ENEMY_SPEED_FINAL_MULTIPLIER
                    speed_multiplier += extra_multiplier

            for enemy in self.enemies:
                enemy.speed = enemy.base_speed * speed_multiplier

    def grant_post_boss_shield(self):
        """Give each player a one-hit shield after defeating a boss"""
        if self.boss_shield_granted:
            return

        granted_any = False
        for player in self.players:
            if player.has_boss_shield_upgrade:
                player.activate_boss_shield()
                granted_any = True

        self.boss_shield_granted = True
        if granted_any:
            self.floating_texts.append(FloatingText(
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                "Shield Ready!",
                color=CYAN,
                duration=1500
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
        base_chance = BASE_LUCKY_DROP_CHANCE

        # In co-op mode, halve the drop chance since players kill enemies twice as fast
        if self.coop_mode:
            base_chance = base_chance / 2

        drop_chance = base_chance + bonus_chance
        if random.randint(1, 100) <= drop_chance:
            power_types = ['rapid_fire', 'invincibility', 'laser', 'multi_shot']

            # Check if player has an active laser (either ready to fire or currently firing)
            player_has_laser = False
            if player:
                # Check if player has laser ready to fire
                player_has_laser = player.has_laser
                # Check if player has an active laser beam
                if not player_has_laser:
                    for laser in self.laser_beams:
                        if laser.owner_player_id == player.player_id and laser.is_active():
                            player_has_laser = True
                            break

            # If player has laser, don't spawn any powerups (prevents laser chaining strategy)
            if player_has_laser:
                return

            power_type = random.choice(power_types)
            x = random.randint(100, SCREEN_WIDTH - 100)
            y = 100
            self.power_ups.append(PowerUp(x, y, power_type))

            # DEBUG: Track powerup spawn and log details
            self.powerups_spawned_this_level += 1
            powerup_spawn_level = player.upgrades.powerup_spawn_level if player else 0
            print(f"[POWERUP DEBUG] Level {self.level}: Powerup #{self.powerups_spawned_this_level} spawned! "
                  f"Type: {power_type}, Drop chance: {drop_chance}% "
                  f"(base: {base_chance}% + bonus: {bonus_chance}% from {powerup_spawn_level} Lucky Drops upgrades)")

    def handle_events(self):
        if self.showing_stats_screen:
            return self.handle_stats_screen_events()
        elif self.awaiting_name_input:
            return self.handle_name_input_events()
        elif self.awaiting_level_up:
            return self.handle_level_up_events()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == self.key_bindings['player1_fire_key'] and not self.game_over:
                    if len(self.players) > 0 and self.players[0].is_alive:
                        player = self.players[0]
                        # Determine shot type for stats tracking
                        if player.has_laser:
                            shot_stat_type = 'laser'
                        elif player.has_multi_shot and player.multi_shot_ammo > 0:
                            shot_stat_type = 'multi'
                        elif player.rapid_fire and player.rapid_fire_ammo > 0:
                            shot_stat_type = 'rapid'
                        else:
                            shot_stat_type = 'normal'

                        shots = player.shoot(self.sound_manager)
                        for shot_type, shot in shots:
                            if shot_type == 'bullet':
                                self.sound_manager.play_sound('shoot')
                                self.player_bullets.append(shot)
                                # Track shot in stats
                                if len(self.player_stats) > 0:
                                    self.player_stats[0].record_shot(shot_stat_type)
                            elif shot_type == 'laser':
                                self.sound_manager.play_sound('laser')
                                self.laser_beams.append(shot)
                                # Track laser shot in stats
                                if len(self.player_stats) > 0:
                                    self.player_stats[0].record_shot(shot_stat_type)
                            elif shot_type == 'muzzle_flash':
                                # Add muzzle flash particles to the particle list
                                self.muzzle_flash_particles.extend(shot)
                            elif shot_type == 'muzzle_flash_flashes':
                                # Add muzzle flash circles to the flash list
                                self.muzzle_flash_flashes.extend(shot)
                elif event.key == self.key_bindings['player2_fire_key'] and not self.game_over and self.coop_mode:
                    if len(self.players) > 1 and self.players[1].is_alive:
                        player = self.players[1]
                        # Determine shot type for stats tracking
                        if player.has_laser:
                            shot_stat_type = 'laser'
                        elif player.has_multi_shot and player.multi_shot_ammo > 0:
                            shot_stat_type = 'multi'
                        elif player.rapid_fire and player.rapid_fire_ammo > 0:
                            shot_stat_type = 'rapid'
                        else:
                            shot_stat_type = 'normal'

                        shots = player.shoot(self.sound_manager)
                        for shot_type, shot in shots:
                            if shot_type == 'bullet':
                                self.sound_manager.play_sound('shoot')
                                self.player_bullets.append(shot)
                                # Track shot in stats
                                if len(self.player_stats) > 1:
                                    self.player_stats[1].record_shot(shot_stat_type)
                            elif shot_type == 'laser':
                                self.sound_manager.play_sound('laser')
                                self.laser_beams.append(shot)
                                # Track laser shot in stats
                                if len(self.player_stats) > 1:
                                    self.player_stats[1].record_shot(shot_stat_type)
                            elif shot_type == 'muzzle_flash':
                                # Add muzzle flash particles to the particle list
                                self.muzzle_flash_particles.extend(shot)
                            elif shot_type == 'muzzle_flash_flashes':
                                # Add muzzle flash circles to the flash list
                                self.muzzle_flash_flashes.extend(shot)
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
                            # Check which player and use their configured fire button
                            fire_button = self.key_bindings['player1_fire_button'] if i == 0 else self.key_bindings['player2_fire_button']
                            if event.button == fire_button:
                                # Determine shot type for stats tracking
                                if player.has_laser:
                                    shot_stat_type = 'laser'
                                elif player.has_multi_shot and player.multi_shot_ammo > 0:
                                    shot_stat_type = 'multi'
                                elif player.rapid_fire and player.rapid_fire_ammo > 0:
                                    shot_stat_type = 'rapid'
                                else:
                                    shot_stat_type = 'normal'

                                shots = player.shoot(self.sound_manager)
                                for shot_type, shot in shots:
                                    if shot_type == 'bullet':
                                        self.sound_manager.play_sound('shoot')
                                        self.player_bullets.append(shot)
                                        # Track shot in stats
                                        if i < len(self.player_stats):
                                            self.player_stats[i].record_shot(shot_stat_type)
                                    elif shot_type == 'laser':
                                        self.sound_manager.play_sound('laser')
                                        self.laser_beams.append(shot)
                                        # Track laser shot in stats
                                        if i < len(self.player_stats):
                                            self.player_stats[i].record_shot(shot_stat_type)
                                    elif shot_type == 'muzzle_flash':
                                        # Add muzzle flash particles to the particle list
                                        self.muzzle_flash_particles.extend(shot)
                                    elif shot_type == 'muzzle_flash_flashes':
                                        # Add muzzle flash circles to the flash list
                                        self.muzzle_flash_flashes.extend(shot)

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

                # Show high score screen with stats
                self.stats_screen = HighScoreScreen(
                    self.screen,
                    self.score_manager,
                    self.sound_manager,
                    player_stats=self.player_stats,
                    players=self.players,
                    key_bindings=self.key_bindings
                )
                self.showing_stats_screen = True
        return None
    
    def handle_level_up_events(self):
        """Handle events during level up screen"""
        if hasattr(self, 'level_up_screen'):
            result = self.level_up_screen.handle_events()
            if result == "quit":
                self.running = False
                return None
            elif result == "save_and_quit":
                print("Saving game and returning to title screen...")
                self.save_game()
                self.awaiting_level_up = False
                self.pending_level_up = False
                del self.level_up_screen
                return "title"
            elif result == "continue":
                print("Level up complete, continuing...")  # Debug
                self.awaiting_level_up = False
                self.pending_level_up = False  # Clear the flag
                del self.level_up_screen

                # DEBUG: Log powerup stats before advancing to next level
                if self.enemies_killed_this_level > 0:
                    drop_rate = (self.powerups_spawned_this_level / self.enemies_killed_this_level) * 100
                    print(f"\n{'='*70}")
                    print(f"[POWERUP DEBUG] LEVEL {self.level} SUMMARY:")
                    print(f"  Enemies killed: {self.enemies_killed_this_level}")
                    print(f"  Powerups spawned: {self.powerups_spawned_this_level}")
                    print(f"  Actual drop rate: {drop_rate:.2f}%")
                    print(f"{'='*70}\n")

                # Now advance the game level
                self.level += 1
                print(f"Advanced to game level {self.level} after level up")  # Debug

                # Reset powerup tracking for new level
                self.powerups_spawned_this_level = 0
                self.enemies_killed_this_level = 0

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

    def handle_stats_screen_events(self):
        """Handle events during stats screen display"""
        if hasattr(self, 'stats_screen'):
            result = self.stats_screen.handle_events()
            if result == "quit":
                self.running = False
                return None
            elif result == "back":
                self.showing_stats_screen = False
                del self.stats_screen
                return "title"
        return None

    def handle_input(self):
        if not self.game_over and not self.awaiting_level_up:
            keys = pygame.key.get_pressed()

            if len(self.players) > 0:
                if keys[self.key_bindings['player1_left_key']]:
                    self.players[0].move_left()
                if keys[self.key_bindings['player1_right_key']]:
                    self.players[0].move_right()

                # Auto-fire: check if fire key is held and auto-fire upgrade is active
                if keys[self.key_bindings['player1_fire_key']] and self.players[0].is_alive and self.players[0].upgrades.has_auto_fire():
                    player = self.players[0]
                    # Determine shot type for stats tracking
                    if player.has_laser:
                        shot_stat_type = 'laser'
                    elif player.has_multi_shot and player.multi_shot_ammo > 0:
                        shot_stat_type = 'multi'
                    elif player.rapid_fire and player.rapid_fire_ammo > 0:
                        shot_stat_type = 'rapid'
                    else:
                        shot_stat_type = 'normal'

                    shots = player.shoot(self.sound_manager)
                    for shot_type, shot in shots:
                        if shot_type == 'bullet':
                            self.sound_manager.play_sound('shoot')
                            self.player_bullets.append(shot)
                            if len(self.player_stats) > 0:
                                self.player_stats[0].record_shot(shot_stat_type)
                        elif shot_type == 'laser':
                            self.sound_manager.play_sound('laser')
                            self.laser_beams.append(shot)
                            if len(self.player_stats) > 0:
                                self.player_stats[0].record_shot(shot_stat_type)
                        elif shot_type == 'muzzle_flash':
                            self.muzzle_flash_particles.extend(shot)
                        elif shot_type == 'muzzle_flash_flashes':
                            self.muzzle_flash_flashes.extend(shot)

                # Create shoot callback for player 1 controller auto-fire
                def player1_shoot():
                    player = self.players[0]
                    if player.has_laser:
                        shot_stat_type = 'laser'
                    elif player.has_multi_shot and player.multi_shot_ammo > 0:
                        shot_stat_type = 'multi'
                    elif player.rapid_fire and player.rapid_fire_ammo > 0:
                        shot_stat_type = 'rapid'
                    else:
                        shot_stat_type = 'normal'

                    shots = player.shoot(self.sound_manager)
                    for shot_type, shot in shots:
                        if shot_type == 'bullet':
                            self.sound_manager.play_sound('shoot')
                            self.player_bullets.append(shot)
                            if len(self.player_stats) > 0:
                                self.player_stats[0].record_shot(shot_stat_type)
                        elif shot_type == 'laser':
                            self.sound_manager.play_sound('laser')
                            self.laser_beams.append(shot)
                            if len(self.player_stats) > 0:
                                self.player_stats[0].record_shot(shot_stat_type)
                        elif shot_type == 'muzzle_flash':
                            self.muzzle_flash_particles.extend(shot)
                        elif shot_type == 'muzzle_flash_flashes':
                            self.muzzle_flash_flashes.extend(shot)

                self.players[0].handle_controller_input(
                    player1_shoot,
                    self.key_bindings['player1_fire_button'],
                    self.key_bindings.get('player1_left_button'),
                    self.key_bindings.get('player1_right_button')
                )

            if self.coop_mode and len(self.players) > 1:
                if not self.players[1].controller:
                    if keys[self.key_bindings['player2_left_key']]:
                        self.players[1].move_left()
                    if keys[self.key_bindings['player2_right_key']]:
                        self.players[1].move_right()
                    # Auto-fire for player 2
                    if keys[self.key_bindings['player2_fire_key']] and self.players[1].is_alive and self.players[1].upgrades.has_auto_fire():
                        player = self.players[1]
                        # Determine shot type for stats tracking
                        if player.has_laser:
                            shot_stat_type = 'laser'
                        elif player.has_multi_shot and player.multi_shot_ammo > 0:
                            shot_stat_type = 'multi'
                        elif player.rapid_fire and player.rapid_fire_ammo > 0:
                            shot_stat_type = 'rapid'
                        else:
                            shot_stat_type = 'normal'

                        shots = player.shoot(self.sound_manager)
                        for shot_type, shot in shots:
                            if shot_type == 'bullet':
                                self.sound_manager.play_sound('shoot')
                                self.player_bullets.append(shot)
                                if len(self.player_stats) > 1:
                                    self.player_stats[1].record_shot(shot_stat_type)
                            elif shot_type == 'laser':
                                self.sound_manager.play_sound('laser')
                                self.laser_beams.append(shot)
                                if len(self.player_stats) > 1:
                                    self.player_stats[1].record_shot(shot_stat_type)
                            elif shot_type == 'muzzle_flash':
                                self.muzzle_flash_particles.extend(shot)
                            elif shot_type == 'muzzle_flash_flashes':
                                self.muzzle_flash_flashes.extend(shot)
                else:
                    # Create shoot callback for player 2 controller auto-fire
                    def player2_shoot():
                        player = self.players[1]
                        if player.has_laser:
                            shot_stat_type = 'laser'
                        elif player.has_multi_shot and player.multi_shot_ammo > 0:
                            shot_stat_type = 'multi'
                        elif player.rapid_fire and player.rapid_fire_ammo > 0:
                            shot_stat_type = 'rapid'
                        else:
                            shot_stat_type = 'normal'

                        shots = player.shoot(self.sound_manager)
                        for shot_type, shot in shots:
                            if shot_type == 'bullet':
                                self.sound_manager.play_sound('shoot')
                                self.player_bullets.append(shot)
                                if len(self.player_stats) > 1:
                                    self.player_stats[1].record_shot(shot_stat_type)
                            elif shot_type == 'laser':
                                self.sound_manager.play_sound('laser')
                                self.laser_beams.append(shot)
                                if len(self.player_stats) > 1:
                                    self.player_stats[1].record_shot(shot_stat_type)
                            elif shot_type == 'muzzle_flash':
                                self.muzzle_flash_particles.extend(shot)
                            elif shot_type == 'muzzle_flash_flashes':
                                self.muzzle_flash_flashes.extend(shot)

                    self.players[1].handle_controller_input(
                        player2_shoot,
                        self.key_bindings['player2_fire_button'],
                        self.key_bindings.get('player2_left_button'),
                        self.key_bindings.get('player2_right_button')
                    )
    
    def activate_power_up(self, player, power_type):
        if power_type == 'rapid_fire':
            player.activate_rapid_fire()
        elif power_type == 'invincibility':
            player.activate_invincibility()
            # Track start of invincibility in stats
            player_idx = player.player_id - 1
            if player_idx < len(self.player_stats):
                self.player_stats[player_idx].start_invincibility()
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

            # DEBUG: Log powerup stats before advancing to next level
            if self.enemies_killed_this_level > 0:
                drop_rate = (self.powerups_spawned_this_level / self.enemies_killed_this_level) * 100
                print(f"\n{'='*70}")
                print(f"[POWERUP DEBUG] LEVEL {self.level} SUMMARY:")
                print(f"  Enemies killed: {self.enemies_killed_this_level}")
                print(f"  Powerups spawned: {self.powerups_spawned_this_level}")
                print(f"  Actual drop rate: {drop_rate:.2f}%")
                print(f"{'='*70}\n")

            # No level up pending, advance to next level
            self.level += 1
            print(f"Advanced to game level {self.level}")  # Debug

            # Reset powerup tracking for new level
            self.powerups_spawned_this_level = 0
            self.enemies_killed_this_level = 0

            # Clear all enemy bullets to prevent them from carrying over to the next level
            self.enemy_bullets.clear()

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

            # Delete save file on game over
            if os.path.exists("savegame.json"):
                os.remove("savegame.json")

            # Set final stats for all players
            for i, stats in enumerate(self.player_stats):
                if self.coop_mode:
                    # In coop, each player gets their own score (we'll use total score / 2 for simplicity)
                    player_score = self.score // 2
                else:
                    player_score = self.score
                stats.set_final_stats(player_score, self.xp_system.level, self.xp_system.current_xp)

            if self.score_manager.is_high_score(self.score, self.coop_mode):
                self.awaiting_name_input = True
                self.name_input_screen = NameInputScreen(self.screen, self.score, self.level, self.coop_mode, self.key_bindings)
                
        return game_over 
    
    def update(self):
        # ADDED: Handle UFO warning screen
        if self.showing_ufo_warning:
            if self.ufo_warning_screen.is_finished():
                self.showing_ufo_warning = False
                self.current_boss = self.create_boss_instance()

                # Track boss encounter in player stats
                boss_name = self.current_boss.__class__.__name__
                for stat in self.player_stats:
                    stat.record_boss_encounter(boss_name)

                # Clear barriers for Asteroid Field Boss
                if isinstance(self.current_boss, AsteroidFieldBoss):
                    self.barriers.clear()
                self.ufo_warning_screen = None
            return  # Don't update game during warning

        # Update player explosion particles (even during game over so death animation plays)
        for particle in self.player_explosion_particles[:]:
            particle['x'] += particle['vel_x']
            particle['y'] += particle['vel_y']
            particle['vel_y'] += particle['gravity']  # Apply particle's gravity
            particle['life'] -= 16  # Assuming 60 FPS

            if particle['life'] <= 0:
                self.player_explosion_particles.remove(particle)

        # Update boss explosion particles (even during game over)
        for particle in self.boss_explosion_particles[:]:
            particle['x'] += particle['vel_x']
            particle['y'] += particle['vel_y']
            particle['vel_y'] += 0.2  # Gravity
            particle['life'] -= 16  # Assuming 60 FPS

            if particle['life'] <= 0:
                self.boss_explosion_particles.remove(particle)

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

        # Update starfield (with parallax effect during Asteroid Field Boss)
        parallax_active = (self.is_boss_level and
                          self.current_boss and
                          isinstance(self.current_boss, AsteroidFieldBoss))
        self.starfield.update(parallax_active)

        # Update explosion waves
        for wave in self.boss_explosion_waves[:]:
            wave['radius'] += wave['growth_speed']
            wave['life'] -= 1

            if wave['life'] <= 0 or wave['radius'] >= wave['max_radius']:
                self.boss_explosion_waves.remove(wave)

        # Update muzzle flash particles
        for particle in self.muzzle_flash_particles[:]:
            particle['x'] += particle['vel_x']
            particle['y'] += particle['vel_y']
            particle['life'] -= 16  # Assuming 60 FPS

            if particle['life'] <= 0:
                self.muzzle_flash_particles.remove(particle)

        # Update muzzle flash circles (bright expanding flashes)
        for flash in self.muzzle_flash_flashes[:]:
            flash['radius'] += flash['growth_speed']
            flash['life'] -= 16  # Assuming 60 FPS

            if flash['life'] <= 0 or flash['radius'] >= flash['max_radius']:
                self.muzzle_flash_flashes.remove(flash)

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
            boss_explosion_particles = self.current_boss.update(self.players, self.sound_manager)
            # Capture player explosion particles from boss update (e.g., AlienOverlordBoss hand attacks)
            if boss_explosion_particles:
                self.player_explosion_particles.extend(boss_explosion_particles)
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
                        took_damage, explosion_particles = player.take_damage(self.sound_manager)
                        if took_damage:
                            # Add explosion particles if player died
                            if explosion_particles:
                                self.player_explosion_particles.extend(explosion_particles)
                
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
                    took_damage, explosion_particles = player.take_damage(self.sound_manager)
                    # Add explosion particles if player died
                    if explosion_particles:
                        self.player_explosion_particles.extend(explosion_particles)
                    self.game_over = True
                    self.game_over_time = pygame.time.get_ticks()
                    if self.score_manager.is_high_score(self.score, self.coop_mode):
                        self.awaiting_name_input = True
                        self.name_input_screen = NameInputScreen(self.screen, self.score, self.level, self.coop_mode, self.key_bindings)
                    
    def check_collisions(self):
        # Player bullets vs enemies
        for bullet in self.player_bullets[:]:
            owner = next((p for p in self.players if p.player_id == bullet.owner_id), None)
            if self.is_boss_level and self.current_boss and not self.current_boss.destruction_complete:
                # Special handling for RubiksCubeBoss
                if isinstance(self.current_boss, RubiksCubeBoss):
                    if self.current_boss.take_square_damage(bullet.rect, max(1, int(math.ceil(bullet.boss_damage_multiplier)))):
                        # Hit a square
                        if bullet.pierce_hits <= 0:
                            self.player_bullets.remove(bullet)
                        self.sound_manager.play_sound('ufo_hit', volume_override=0.5)
                        self.score += 10
                        self.add_xp(5, bullet.rect.centerx, bullet.rect.centery)
                        if bullet.pierce_hits > 0:
                            bullet.pierce_hits -= 1
                    continue  # Skip normal boss collision logic

                # Check turret collisions first (for other bosses)
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

                        # Track boss damage in player stats
                        if bullet.owner_id and bullet.owner_id <= len(self.player_stats):
                            self.player_stats[bullet.owner_id - 1].record_boss_damage(damage)

                        if self.current_boss.take_main_damage(damage):
                            # Boss completely destroyed - EPIC EXPLOSION SEQUENCE
                            self.score += 1000
                            self.add_xp(200, self.current_boss.x + self.current_boss.width // 2, self.current_boss.y)

                            # Clear all enemy bullets immediately when boss is destroyed
                            self.enemy_bullets.clear()

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
                        self.enemies_killed_this_level += 1  # DEBUG: Track kills per level
                        self.add_xp(5, enemy.x + enemy.width // 2, enemy.y)
                        self.update_enemy_speed()
                        self.spawn_power_up(owner)

                        # Track enemy kill in player stats
                        if bullet.owner_id and bullet.owner_id <= len(self.player_stats):
                            self.player_stats[bullet.owner_id - 1].record_enemy_kill()
                        if bullet.pierce_hits > 0:
                            bullet.pierce_hits -= 1
                        break
                        
        # Laser vs enemies
        for laser in self.laser_beams:
            owner = next((p for p in self.players if p.player_id == laser.owner_player_id), None)
            if laser.is_active():
                if self.is_boss_level and self.current_boss and not self.current_boss.destruction_complete:
                    # Special handling for RubiksCubeBoss with lasers
                    if isinstance(self.current_boss, RubiksCubeBoss):
                        # Laser continuously damages squares
                        if pygame.time.get_ticks() % 100 == 0:  # Damage every 100ms
                            if self.current_boss.take_square_damage(laser.rect, 2):
                                if pygame.time.get_ticks() % 200 == 0:
                                    self.sound_manager.play_sound('ufo_hit', volume_override=0.4)
                                self.score += 10
                                self.add_xp(4, laser.rect.centerx, laser.rect.centery)
                        continue  # Skip normal boss collision logic

                    # Laser vs turrets (for other bosses)
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

                        # Track boss damage in player stats (laser does 3 damage)
                        if laser.owner_player_id and laser.owner_player_id <= len(self.player_stats):
                            self.player_stats[laser.owner_player_id - 1].record_boss_damage(3)

                        if self.current_boss.take_main_damage(3):  # Laser does lots of damage to main body
                            self.score += 1000
                            self.add_xp(200, main_body_rect.centerx, main_body_rect.centery)

                            # Clear all enemy bullets immediately when boss is destroyed
                            self.enemy_bullets.clear()

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
                            self.enemies_killed_this_level += 1  # DEBUG: Track kills per level
                            self.add_xp(5, enemy.x + enemy.width // 2, enemy.y)
                            self.spawn_power_up(owner)

                            # Track enemy kill in player stats
                            if laser.owner_player_id and laser.owner_player_id <= len(self.player_stats):
                                self.player_stats[laser.owner_player_id - 1].record_enemy_kill()
                            
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
                    # White ball and green laser persist through barriers
                    if not isinstance(bullet, (WhiteBall, GreenLaser)):
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
            for i, player in enumerate(self.players):
                if player.is_alive and bullet.rect.colliderect(player.rect):
                    was_alive = player.lives > 0
                    took_damage, explosion_particles = player.take_damage(self.sound_manager)
                    if took_damage:
                        # Track death if player died
                        if was_alive and player.lives <= 0 and i < len(self.player_stats):
                            self.player_stats[i].record_death()
                        # Add explosion particles if player died
                        if explosion_particles:
                            self.player_explosion_particles.extend(explosion_particles)
                        # Don't remove green laser or white ball when they hit player - they persist
                        if not isinstance(bullet, (GreenLaser, WhiteBall)):
                            self.enemy_bullets.remove(bullet)
                        break

        # Asteroids vs players (for Asteroid Field Boss)
        if self.is_boss_level and self.current_boss and isinstance(self.current_boss, AsteroidFieldBoss):
            for asteroid in self.current_boss.asteroids[:]:
                for i, player in enumerate(self.players):
                    if player.is_alive:
                        # Use circular collision detection for more accurate asteroid hits
                        player_center_x = player.x + player.width // 2
                        player_center_y = player.y + player.height // 2
                        player_radius = min(player.width, player.height) // 2

                        # Calculate distance between asteroid center and player center
                        asteroid_radius = asteroid.size // 2
                        dx = asteroid.x - player_center_x
                        dy = asteroid.y - player_center_y
                        distance = math.sqrt(dx * dx + dy * dy)

                        # Near-miss XP: Award XP if within half ship width (30 pixels) but not colliding
                        # Half ship width = 30 pixels
                        near_miss_threshold = asteroid_radius + player_radius + 30
                        collision_threshold = asteroid_radius + player_radius

                        if not asteroid.near_miss_triggered and distance <= near_miss_threshold and distance > collision_threshold:
                            # Award near-miss XP
                            asteroid.near_miss_triggered = True
                            self.add_xp(10, player_center_x, player_center_y)
                            self.sound_manager.play_sound('levelup')

                        if asteroid.collides_with_circle(player_center_x, player_center_y, player_radius):
                            was_alive = player.lives > 0
                            took_damage, explosion_particles = player.take_damage(self.sound_manager)
                            if took_damage:
                                # Track death if player died
                                if was_alive and player.lives <= 0 and i < len(self.player_stats):
                                    self.player_stats[i].record_death()
                                # Add explosion particles if player died
                                if explosion_particles:
                                    self.player_explosion_particles.extend(explosion_particles)
                                self.current_boss.remove_asteroid(asteroid)
                                self.sound_manager.play_sound('explosion_small', volume_override=0.5)
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
        self.player_explosion_particles = []
        self.screen_shake_intensity = 0
        self.screen_shake_duration = 0
        self.screen_flash_intensity = 0
        self.screen_flash_duration = 0
        self.boss_explosion_waves = []
        self.available_bosses = [Boss, AlienOverlordBoss, BulletHellBoss, AsteroidFieldBoss, RubiksCubeBoss]
        self.boss_encounters = {Boss: 0, AlienOverlordBoss: 0, BulletHellBoss: 0, AsteroidFieldBoss: 0, RubiksCubeBoss: 0}

        # Reset all players with new individual upgrades
        for player in self.players:
            player.lives = 3
            player.is_alive = True
            player.upgrades = PlayerUpgrades()  # Each player gets their own upgrades
            player.reset_position()
            player.clear_all_power_ups()
            player.invincible = False
            player.respawn_immunity = False
            player.has_boss_shield_upgrade = False
            player.afterimage_positions = []
        
        self.create_barriers()
        self.setup_level()
        
    def draw(self):
        # ADDED: Show UFO warning screen if active
        if self.showing_ufo_warning and self.ufo_warning_screen:
            self.ufo_warning_screen.draw()
            return
            
        self.screen.fill(BLACK)

        # Draw starfield background (after black fill, before everything else)
        self.starfield.draw(self.screen)

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
                self.level_up_screen = LevelUpScreen(self.screen, self.players, self.coop_mode, self.sound_manager, self.xp_system.level, self.level, self.score, self.key_bindings)
            self.level_up_screen.draw()
            return
        
        # Handle name input screen
        if self.awaiting_name_input and hasattr(self, 'name_input_screen'):
            self.name_input_screen.draw()
            return

        # Handle stats screen (shown after high score name entry)
        if self.showing_stats_screen and hasattr(self, 'stats_screen'):
            self.stats_screen.draw()
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
                player.draw(self.screen, self.powerup_font)
            
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

            # Draw muzzle flash particles
            for particle in self.muzzle_flash_particles:
                if particle['life'] > 0:
                    # Fade out quickly based on remaining life
                    alpha = max(0, min(255, particle['life']))
                    particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
                    color_with_alpha = (*particle['color'], alpha)
                    pygame.draw.circle(particle_surface, color_with_alpha,
                                     (particle['size'], particle['size']), particle['size'])
                    self.screen.blit(particle_surface, (int(particle['x'] - particle['size']),
                                                     int(particle['y'] - particle['size'])))

            # Draw muzzle flash circles (bright expanding flashes)
            for flash in self.muzzle_flash_flashes:
                if flash['life'] > 0 and flash['radius'] < flash['max_radius']:
                    # Fade out as life decreases
                    alpha = max(0, min(255, int(255 * (flash['life'] / 120))))
                    surface_size = int(flash['radius'] * 2 + 4)
                    flash_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
                    color_with_alpha = (*flash['color'], alpha)
                    center = (surface_size // 2, surface_size // 2)
                    # Draw filled circle for bright flash
                    pygame.draw.circle(flash_surface, color_with_alpha, center, int(flash['radius']))
                    self.screen.blit(flash_surface, (int(flash['x'] - flash['radius']),
                                                   int(flash['y'] - flash['radius'])))

            for barrier in self.barriers:
                barrier.draw(self.screen)
                
            for power_up in self.power_ups:
                power_up.draw(self.screen)
            
            # Draw floating texts
            for text in self.floating_texts:
                text.draw(self.screen)

        # Draw player explosion particles (outside game_over check so they're always visible)
        for particle in self.player_explosion_particles:
            if particle['life'] > 0:
                alpha = max(0, min(255, particle['life'] // 2))
                particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
                color_with_alpha = (*particle['color'], alpha)
                pygame.draw.circle(particle_surface, color_with_alpha,
                                 (particle['size'], particle['size']), particle['size'])
                self.screen.blit(particle_surface, (int(particle['x'] - particle['size']),
                                                 int(particle['y'] - particle['size'])))

        # UI - Clean retro style
        score_text = self.small_font.render(f"SCORE {self.score:,}", True, GREEN)
        level_text = self.small_font.render(f"LEVEL {self.level}", True, CYAN)

        self.screen.blit(score_text, (20, 20))
        self.screen.blit(level_text, (20, 50))

        # Player lives display
        if self.coop_mode:
            lives_text1 = self.small_font.render(f"P1 {self.players[0].lives} {'X' if not self.players[0].is_alive else ''}", True, GREEN if self.players[0].is_alive else RED)
            lives_text2 = self.small_font.render(f"P2 {self.players[1].lives} {'X' if not self.players[1].is_alive else ''}", True, BLUE if self.players[1].is_alive else RED)
            self.screen.blit(lives_text1, (20, 80))
            self.screen.blit(lives_text2, (20, 110))
        else:
            if self.players:
                lives_text = self.small_font.render(f"LIVES {self.players[0].lives}", True, WHITE)
                self.screen.blit(lives_text, (20, 80))

        # XP Bar - Clean retro style
        bar_width = 250
        bar_height = 20
        bar_x = SCREEN_WIDTH - bar_width - 20
        bar_y = 20

        # XP Bar background
        pygame.draw.rect(self.screen, GRAY, (bar_x, bar_y, bar_width, bar_height))

        # XP Progress
        progress = self.xp_system.get_xp_progress()
        progress_width = int(bar_width * progress)
        pygame.draw.rect(self.screen, GOLD, (bar_x, bar_y, progress_width, bar_height))

        # XP Bar border
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

        # XP level text
        xp_level_text = self.small_font.render(f"XP LV {self.xp_system.level}", True, GOLD)
        self.screen.blit(xp_level_text, (bar_x, bar_y + bar_height + 5))
        
        # Power-up status is now displayed below each player's ship (see Player.draw())
        
        # Game over screen with comprehensive player stats
        if self.game_over and not self.awaiting_name_input:
            # Draw semi-transparent background
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))

            # Title
            game_over_text = self.font.render("GAME OVER", True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, 50))
            self.screen.blit(game_over_text, text_rect)

            # Draw stats for each player
            stats_font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 12)
            header_font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", 14)

            num_players = len(self.player_stats)
            if num_players == 1:
                # Single player - center column
                self.draw_player_stats(self.player_stats[0], stats_font, header_font, SCREEN_WIDTH//2 - 200, 120, self.players[0])
            else:
                # Coop - two columns
                col_width = SCREEN_WIDTH // 2
                for i, stats in enumerate(self.player_stats):
                    x_offset = i * col_width + (col_width // 2) - 200
                    player = self.players[i] if i < len(self.players) else None
                    self.draw_player_stats(stats, stats_font, header_font, x_offset, 120, player)

            # Controls
            if pygame.time.get_ticks() - self.game_over_time < self.input_delay_duration:
                remaining = (self.input_delay_duration - (pygame.time.get_ticks() - self.game_over_time)) / 1000.0
                controls_text = self.small_font.render(f"Controls unlocking in {remaining:.1f}s...", True, YELLOW)
            else:
                controls_text = self.small_font.render("R/A: Restart | ESC/B: Title Menu", True, WHITE)

            controls_rect = controls_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 40))
            self.screen.blit(controls_text, controls_rect)

        # Draw instructions and screen flash, then update display
        self.update_display()

    def draw_player_stats(self, stats, stats_font, header_font, x, y, player):
        """Draw comprehensive stats for a single player"""
        # Player header
        player_color = GREEN if stats.player_id == 1 else BLUE
        header_text = header_font.render(f"PLAYER {stats.player_id}", True, player_color)
        self.screen.blit(header_text, (x, y))
        y += 40

        # Stats list
        stat_lines = [
            f"Score: {stats.final_score:,}",
            f"XP Level: {stats.final_xp_level}",
            f"",
            f"Enemies Killed: {stats.enemies_killed}",
            f"",
            f"Shots Fired: {stats.shots_fired_total}",
            f"  Normal: {stats.shots_fired_normal}",
            f"  Rapid: {stats.shots_fired_rapid}",
            f"  Multi: {stats.shots_fired_multi}",
            f"  Laser: {stats.shots_fired_laser}",
            f"",
            f"Invincibility: {stats.get_invincibility_seconds():.1f}s",
            f"Deaths: {stats.deaths}",
            f"",
            f"Boss Damage: {stats.boss_damage_dealt}",
            f"Bosses Fought: {stats.bosses_fought_count}",
        ]

        # Add boss names if any
        if stats.bosses_fought_names:
            for boss_name in stats.bosses_fought_names:
                # Simplify boss names
                simple_name = boss_name.replace("Boss", "").replace("Alien", "").replace("Overlord", "Ovl.")
                stat_lines.append(f"  {simple_name}")

        # Draw all stats
        for line in stat_lines:
            if line:  # Skip empty lines
                text = stats_font.render(line, True, WHITE)
                self.screen.blit(text, (x, y))
            y += 25

    def update_display(self):
        """Update the display"""
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

    # Initialize profile manager and load last profile (or defaults)
    profile_manager = ProfileManager()
    key_bindings = profile_manager.get_last_profile_bindings()

    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    except:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    clock = pygame.time.Clock()

    while True:
        title_screen = TitleScreen(screen, score_manager, sound_manager, key_bindings)
        
        while True:
            action = title_screen.handle_events()
            if action == "quit":
                pygame.quit()
                sys.exit()
            elif action == "highscores":
                high_score_screen = HighScoreScreen(screen, score_manager, sound_manager, key_bindings=key_bindings)
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
            elif action == "settings":
                settings_screen = SettingsScreen(screen, sound_manager, key_bindings, profile_manager)
                while True:
                    settings_action = settings_screen.handle_events()
                    if settings_action == "back":
                        break
                    elif settings_action == "quit":
                        pygame.quit()
                        sys.exit()
                    elif settings_action == "save":
                        # Show profile name input screen
                        profile_name_screen = ProfileNameInputScreen(screen, sound_manager, key_bindings)
                        while True:
                            name_result = profile_name_screen.handle_events()
                            if name_result == "quit":
                                pygame.quit()
                                sys.exit()
                            elif name_result == "cancel":
                                break
                            elif name_result:
                                # Save the profile
                                profile_manager.save_profile(name_result, key_bindings)
                                settings_screen.show_message(f"Profile '{name_result}' saved!")
                                break
                            profile_name_screen.draw()
                            clock.tick(60)
                    elif settings_action == "load":
                        # Show profile selection screen
                        profile_selection_screen = ProfileSelectionScreen(screen, sound_manager, profile_manager, key_bindings)
                        while True:
                            load_result = profile_selection_screen.handle_events()
                            if load_result == "quit":
                                pygame.quit()
                                sys.exit()
                            elif load_result == "cancel":
                                break
                            elif load_result:
                                # Load the selected profile
                                loaded_bindings = profile_manager.get_profile(load_result)
                                if loaded_bindings:
                                    key_bindings.update(loaded_bindings)
                                    profile_manager.last_profile = load_result
                                    profile_manager.save_profiles()
                                    settings_screen.show_message(f"Profile '{load_result}' loaded!")
                                break
                            profile_selection_screen.draw()
                            clock.tick(60)
                    settings_screen.draw()
                    clock.tick(60)
                break
            elif action == "debug_menu":
                debug_menu = DebugMenu(screen, sound_manager, key_bindings)
                debug_action, debug_config = debug_menu.run()

                if debug_action == "quit":
                    pygame.quit()
                    sys.exit()
                elif debug_action == "start":
                    game_mode = debug_config.get('mode', 'single')
                    game = Game(score_manager, sound_manager, key_bindings)
                    game.setup_game(game_mode, debug_config)
                    result = game.run()

                    if result == "title":
                        break  # Go back to title screen
                    elif not result:
                        pygame.quit()
                        sys.exit()
                else:
                    break
            elif action == "continue":
                # Load saved game
                game = Game(score_manager, sound_manager, key_bindings)
                try:
                    game.load_game()
                    result = game.run()

                    if result == "title":
                        break  # Go back to title screen
                    elif not result:
                        pygame.quit()
                        sys.exit()
                except FileNotFoundError:
                    print("Save file not found!")
                    break  # Go back to title screen
            elif action in ["single", "coop"]:
                game = Game(score_manager, sound_manager, key_bindings)
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
