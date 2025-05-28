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

# Game settings
PLAYER_SPEED = 8
BULLET_SPEED = 10
BASE_ENEMY_SPEED = 0.8
ENEMY_DROP_SPEED = 30
SHOOT_COOLDOWN = 300
RAPID_FIRE_COOLDOWN = 100
AFTERIMAGE_INTERVAL = 80
RESPAWN_IMMUNITY_DURATION = 1000

# High scores files
SINGLE_SCORES_FILE = "high_scores_single.json"
COOP_SCORES_FILE = "high_scores_coop.json"

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
    def __init__(self, screen, score_manager):
        self.screen = screen
        self.score_manager = score_manager
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
                    return "back"
                elif event.key == pygame.K_TAB or event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    self.viewing_coop = not self.viewing_coop
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0 or event.button == 1:  # A or B button
                    return "back"
            elif event.type == pygame.JOYHATMOTION:
                if event.value[0] != 0:  # Left or Right
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
    def __init__(self, x, y, player_id=1, controller=None):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 45
        self.speed = PLAYER_SPEED
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.last_shot_time = 0
        self.invincible = False
        self.invincible_end_time = 0
        self.rapid_fire = False
        self.rapid_fire_end_time = 0
        self.has_laser = False
        self.has_multi_shot = False
        self.multi_shot_end_time = 0
        self.afterimage_positions = []
        self.last_afterimage_time = 0
        self.player_id = player_id
        self.controller = controller
        self.color = GREEN if player_id == 1 else BLUE  # Changed to BLUE for player 2
        self.lives = 3
        self.respawn_immunity = False
        self.respawn_immunity_end_time = 0
        self.is_alive = True
        
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
        
    def take_damage(self):
        """Player takes damage"""
        if self.respawn_immunity or self.invincible:
            return False
        
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
            self.x -= self.speed
            self.rect.x = self.x
            self.update_afterimage()
            
    def move_right(self):
        if not self.is_alive:
            return
        if self.x < SCREEN_WIDTH - self.width:
            self.x += self.speed
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
        cooldown = RAPID_FIRE_COOLDOWN if self.rapid_fire else SHOOT_COOLDOWN
        return current_time - self.last_shot_time >= cooldown
        
    def shoot(self):
        if not self.can_shoot():
            return []
            
        self.last_shot_time = pygame.time.get_ticks()
        bullets = []
        
        if self.has_laser:
            laser = LaserBeam(self.x + self.width // 2, self.player_id)  # Pass player ID
            bullets.append(('laser', laser))
            self.has_laser = False
        elif self.has_multi_shot:
            center_bullet = Bullet(self.x + self.width // 2, self.y, -BULLET_SPEED)
            left_bullet = Bullet(self.x + self.width // 2 - 25, self.y, -BULLET_SPEED)
            right_bullet = Bullet(self.x + self.width // 2 + 25, self.y, -BULLET_SPEED)
            bullets.extend([('bullet', center_bullet), ('bullet', left_bullet), ('bullet', right_bullet)])
        else:
            bullet = Bullet(self.x + self.width // 2, self.y, -BULLET_SPEED)
            bullets.append(('bullet', bullet))
            
        return bullets
        
    def update_power_ups(self):
        current_time = pygame.time.get_ticks()
        
        # Update respawn immunity
        if self.respawn_immunity and current_time >= self.respawn_immunity_end_time:
            self.respawn_immunity = False
        
        if self.invincible and current_time >= self.invincible_end_time:
            self.invincible = False
            self.afterimage_positions = []
            
        if self.rapid_fire and current_time >= self.rapid_fire_end_time:
            self.rapid_fire = False
            
        if self.has_multi_shot and current_time >= self.multi_shot_end_time:
            self.has_multi_shot = False
            
    def clear_all_power_ups(self):
        self.rapid_fire = False
        self.has_laser = False
        self.has_multi_shot = False
        
    def activate_invincibility(self):
        self.invincible = True
        self.invincible_end_time = pygame.time.get_ticks() + 10000
        
    def activate_rapid_fire(self):
        self.clear_all_power_ups()
        self.rapid_fire = True
        self.rapid_fire_end_time = pygame.time.get_ticks() + 10000
        
    def activate_laser(self):
        self.clear_all_power_ups()
        self.has_laser = True
        
    def activate_multi_shot(self):
        self.clear_all_power_ups()
        self.has_multi_shot = True
        self.multi_shot_end_time = pygame.time.get_ticks() + 10000
        
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

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 45
        self.height = 30
        self.base_speed = BASE_ENEMY_SPEED  # Store base speed for the level
        self.speed = BASE_ENEMY_SPEED
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.direction = 1
        
    def move(self):
        self.x += self.speed * self.direction
        self.rect.x = self.x
        
    def drop_down(self):
        self.y += ENEMY_DROP_SPEED
        self.rect.y = self.y
        self.direction *= -1
        
    def shoot(self):
        if random.randint(1, 1500) < 3:
            return Bullet(self.x + self.width // 2, self.y + self.height, BULLET_SPEED)
        return None
        
    def draw(self, screen):
        pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, WHITE, (self.x + 8, self.y + 8, 8, 8))
        pygame.draw.rect(screen, WHITE, (self.x + 30, self.y + 8, 8, 8))

class Bullet:
    def __init__(self, x, y, speed):
        self.x = x
        self.y = y
        self.width = 5
        self.height = 15
        self.speed = speed
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
    def move(self):
        self.y += self.speed
        self.rect.y = self.y
        
    def is_off_screen(self):
        return self.y < -20 or self.y > SCREEN_HEIGHT + 20
        
    def draw(self, screen):
        color = YELLOW if self.speed < 0 else RED
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
    def __init__(self, x, owner_player_id=1):
        self.x = x
        self.width = 15
        self.height = SCREEN_HEIGHT
        self.duration = 1000
        self.start_time = pygame.time.get_ticks()
        self.rect = pygame.Rect(x - self.width // 2, 0, self.width, self.height)
        self.owner_player_id = owner_player_id  # Track which player owns this laser
        
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
    def __init__(self, screen, score_manager):
        self.screen = screen
        self.score_manager = score_manager
        self.font_large = pygame.font.Font(None, 128)
        self.font_medium = pygame.font.Font(None, 72)
        self.font_small = pygame.font.Font(None, 48)
        self.selected_option = 0
        self.options = ["Single Player", "Co-op", "High Scores", "Quit"]
        self.controllers = []
        self.scan_controllers()
        
    def scan_controllers(self):
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
                if event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self.selected_option == 0:
                        return "single"
                    elif self.selected_option == 1:
                        return "coop"
                    elif self.selected_option == 2:
                        return "highscores"
                    elif self.selected_option == 3:
                        return "quit"
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:
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
                    self.selected_option = (self.selected_option - 1) % len(self.options)
                elif event.value[1] == -1:
                    self.selected_option = (self.selected_option + 1) % len(self.options)
                    
        return None
        
    def draw(self):
        self.screen.fill(BLACK)
        
        # Title
        title_text = self.font_large.render("SPACE INVADERS", True, WHITE)
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

class Game:
    def __init__(self, score_manager):
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
        self.awaiting_name_input = False
        
        self.controllers = []
        self.scan_controllers()
        
        self.players = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.barriers = []
        self.power_ups = []
        self.laser_beams = []
        
        self.font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 48)
        
    def scan_controllers(self):
        self.controllers = []
        for i in range(pygame.joystick.get_count()):
            controller = pygame.joystick.Joystick(i)
            controller.init()
            self.controllers.append(controller)
            
    def setup_game(self, mode):
        self.coop_mode = (mode == "coop")
        self.players = []
        
        if self.coop_mode:
            controller1 = self.controllers[0] if len(self.controllers) > 0 else None
            player1 = Player(SCREEN_WIDTH // 2 - 90, SCREEN_HEIGHT - 80, 1, controller1)
            player1.coop_mode = True
            self.players.append(player1)
            
            controller2 = self.controllers[1] if len(self.controllers) > 1 else None
            player2 = Player(SCREEN_WIDTH // 2 + 30, SCREEN_HEIGHT - 80, 2, controller2)
            player2.coop_mode = True
            self.players.append(player2)
        else:
            controller = self.controllers[0] if len(self.controllers) > 0 else None
            self.players.append(Player(SCREEN_WIDTH // 2 - 30, SCREEN_HEIGHT - 80, 1, controller))
            
        self.create_barriers()
        self.create_enemy_grid()
        
    def calculate_enemy_speed_for_level(self, level):
        # Remove speed cap - enemies get faster every level without limit
        speed_increase = (level - 1) * 0.2  # Increased increment for more challenge
        return BASE_ENEMY_SPEED + speed_increase
        
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
                enemy = Enemy(enemy_x, enemy_y)
                enemy.base_speed = level_speed  # Set base speed for this level
                enemy.speed = level_speed
                self.enemies.append(enemy)
                
        self.update_enemy_speed()
        
    def update_enemy_speed(self):
        # Progressive speed increase as enemies are destroyed within the level
        total_enemies = 60
        remaining_enemies = len(self.enemies)
        if remaining_enemies > 0:
            # Enemies get up to 4x faster as they're eliminated
            speed_multiplier = 1 + (total_enemies - remaining_enemies) / total_enemies * 3
            for enemy in self.enemies:
                enemy.speed = enemy.base_speed * speed_multiplier
                
    def spawn_power_up(self):
        if random.randint(1, 100) <= 5:
            power_types = ['rapid_fire', 'invincibility', 'laser', 'multi_shot']
            power_type = random.choice(power_types)
            x = random.randint(100, SCREEN_WIDTH - 100)
            y = 100
            self.power_ups.append(PowerUp(x, y, power_type))
        
    def handle_events(self):
        if self.awaiting_name_input:
            return self.handle_name_input_events()
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.game_over:
                    if len(self.players) > 0 and self.players[0].is_alive:
                        shots = self.players[0].shoot()
                        for shot_type, shot in shots:
                            if shot_type == 'bullet':
                                self.player_bullets.append(shot)
                            elif shot_type == 'laser':
                                self.laser_beams.append(shot)
                elif event.key == pygame.K_RCTRL and not self.game_over and self.coop_mode:
                    if len(self.players) > 1 and self.players[1].is_alive:
                        shots = self.players[1].shoot()
                        for shot_type, shot in shots:
                            if shot_type == 'bullet':
                                self.player_bullets.append(shot)
                            elif shot_type == 'laser':
                                self.laser_beams.append(shot)
                elif event.key == pygame.K_r and self.game_over and not self.awaiting_name_input:
                    return "restart"
                elif event.key == pygame.K_ESCAPE:
                    if self.game_over and not self.awaiting_name_input:
                        return "title"
                    elif not self.game_over:
                        return "title"
            elif event.type == pygame.JOYBUTTONDOWN:
                for i, player in enumerate(self.players):
                    if player.controller and event.joy == player.controller.get_instance_id() and player.is_alive:
                        if event.button == 0:
                            shots = player.shoot()
                            for shot_type, shot in shots:
                                if shot_type == 'bullet':
                                    self.player_bullets.append(shot)
                                elif shot_type == 'laser':
                                    self.laser_beams.append(shot)
                                    
        return None
    
    def handle_name_input_events(self):
        """Handle events during name input"""
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
                    
    def handle_input(self):
        if not self.game_over:
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
        """Check if level is complete and handle respawns"""
        if not self.enemies:
            self.level += 1
            
            # Respawn dead players with 1 life if their partner survived
            if self.coop_mode and len(self.players) == 2:
                if not self.players[0].is_alive and self.players[1].is_alive:
                    self.players[0].lives = 1
                    self.players[0].respawn()
                elif not self.players[1].is_alive and self.players[0].is_alive:
                    self.players[1].lives = 1
                    self.players[1].respawn()
            
            self.create_enemy_grid()
            self.create_barriers()
            return True
        return False
        
    def check_game_over(self):
        """Check if game is over based on player lives"""
        if self.coop_mode:
            # Game over only if both players are dead
            game_over = all(not player.is_alive for player in self.players)
        else:
            # Game over if single player is dead
            game_over = not self.players[0].is_alive if self.players else True
            
        if game_over and not self.game_over:
            self.game_over = True
            # Check for high score immediately
            if self.score_manager.is_high_score(self.score, self.coop_mode):
                self.awaiting_name_input = True
                self.name_input_screen = NameInputScreen(self.screen, self.score, self.level, self.coop_mode)
                
        return game_over
                
    def update(self):
        if self.game_over:
            return
            
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
                
        # Update laser beams and make them follow the correct owner
        for laser in self.laser_beams[:]:
            if laser.is_active():
                # Find the player who owns this laser
                owner = next((p for p in self.players if p.player_id == laser.owner_player_id and p.is_alive), None)
                if owner:
                    laser.update_position(owner.x + owner.width // 2)
                else:
                    # If owner is dead, remove laser
                    self.laser_beams.remove(laser)
                    continue
            else:
                self.laser_beams.remove(laser)
                
        edge_hit = False
        for enemy in self.enemies:
            enemy.move()
            if enemy.x <= 0 or enemy.x >= SCREEN_WIDTH - enemy.width:
                edge_hit = True
                
        if edge_hit:
            for enemy in self.enemies:
                enemy.drop_down()
                
        for enemy in self.enemies:
            bullet = enemy.shoot()
            if bullet:
                self.enemy_bullets.append(bullet)
                
        self.check_collisions()
        
        # Check level completion first
        if self.check_level_complete():
            pass  # Level completed, players may have been respawned
            
        # Then check game over
        self.check_game_over()
            
        # Check if enemies reached any alive player
        for enemy in self.enemies:
            for player in self.players:
                if player.is_alive and enemy.y + enemy.height >= player.y:
                    self.game_over = True
                    if self.score_manager.is_high_score(self.score, self.coop_mode):
                        self.awaiting_name_input = True
                        self.name_input_screen = NameInputScreen(self.screen, self.score, self.level, self.coop_mode)
                    
    def check_collisions(self):
        for bullet in self.player_bullets[:]:
            for enemy in self.enemies[:]:
                if bullet.rect.colliderect(enemy.rect):
                    self.player_bullets.remove(bullet)
                    self.enemies.remove(enemy)
                    self.score += 10
                    self.total_enemies_killed += 1
                    self.update_enemy_speed()  # Update speed as enemies are killed
                    self.spawn_power_up()
                    break
                    
        for laser in self.laser_beams:
            if laser.is_active():
                for enemy in self.enemies[:]:
                    if laser.rect.colliderect(enemy.rect):
                        self.enemies.remove(enemy)
                        self.score += 10
                        self.total_enemies_killed += 1
                        self.spawn_power_up()
                        
        self.update_enemy_speed()  # Update speed after laser kills too
                        
        for bullet in self.player_bullets[:]:
            for barrier in self.barriers:
                if barrier.check_collision(bullet.rect):
                    self.player_bullets.remove(bullet)
                    break
                    
        for bullet in self.enemy_bullets[:]:
            for barrier in self.barriers:
                if barrier.check_collision(bullet.rect):
                    self.enemy_bullets.remove(bullet)
                    break
                    
        for power_up in self.power_ups[:]:
            for player in self.players:
                if player.is_alive and power_up.rect.colliderect(player.rect):
                    self.power_ups.remove(power_up)
                    self.activate_power_up(player, power_up.power_type)
                    self.score += 50
                    break
                    
        for bullet in self.enemy_bullets[:]:
            for player in self.players:
                if player.is_alive and bullet.rect.colliderect(player.rect):
                    if player.take_damage():
                        self.enemy_bullets.remove(bullet)
                        break
                    
    def restart_game(self):
        self.game_over = False
        self.awaiting_name_input = False
        if hasattr(self, 'name_input_screen'):
            del self.name_input_screen
        self.score = 0
        self.level = 1
        self.total_enemies_killed = 0
        
        self.player_bullets = []
        self.enemy_bullets = []
        self.power_ups = []
        self.laser_beams = []
        
        # Reset all players
        for player in self.players:
            player.lives = 3
            player.is_alive = True
            player.reset_position()
            player.clear_all_power_ups()
            player.invincible = False
            player.respawn_immunity = False
            player.afterimage_positions = []
        
        self.create_barriers()
        self.create_enemy_grid()
        
    def draw(self):
        self.screen.fill(BLACK)
        
        # Handle name input screen
        if self.awaiting_name_input and hasattr(self, 'name_input_screen'):
            self.name_input_screen.draw()
            return
        
        if not self.game_over:
            for laser in self.laser_beams:
                laser.draw(self.screen)
                
            for player in self.players:
                player.draw(self.screen)
            
            for bullet in self.player_bullets:
                bullet.draw(self.screen)
                
            for bullet in self.enemy_bullets:
                bullet.draw(self.screen)
                
            for enemy in self.enemies:
                enemy.draw(self.screen)
                
            for barrier in self.barriers:
                barrier.draw(self.screen)
                
            for power_up in self.power_ups:
                power_up.draw(self.screen)
                
        # UI
        score_text = self.small_font.render(f"Score: {self.score:,}", True, WHITE)
        level_text = self.small_font.render(f"Level: {self.level}", True, WHITE)
        
        self.screen.blit(score_text, (20, 20))
        self.screen.blit(level_text, (20, 70))
        
        # Player lives display
        if self.coop_mode:
            mode_text = self.small_font.render("CO-OP MODE", True, CYAN)
            self.screen.blit(mode_text, (20, 120))
            
            for i, player in enumerate(self.players):
                status_text = f"P{player.player_id}: {player.lives} lives"
                if not player.is_alive:
                    status_text += " (DEAD)"
                color = player.color if player.is_alive else RED
                lives_text = self.small_font.render(status_text, True, color)
                self.screen.blit(lives_text, (20, 170 + i * 40))
        else:
            if self.players:
                lives_text = self.small_font.render(f"Lives: {self.players[0].lives}", True, WHITE)
                self.screen.blit(lives_text, (20, 120))
        
        # Power-up status
        status_y = 260 if self.coop_mode else 170
        current_time = pygame.time.get_ticks()
        
        for i, player in enumerate(self.players):
            if not player.is_alive:
                continue
                
            player_label = f"P{player.player_id}: " if self.coop_mode else ""
            
            if player.rapid_fire:
                time_left = (player.rapid_fire_end_time - current_time) / 1000
                text = self.small_font.render(f"{player_label}Rapid Fire: {time_left:.1f}s", True, ORANGE)
                self.screen.blit(text, (20, status_y))
                status_y += 40
                
            if player.has_laser:
                text = self.small_font.render(f"{player_label}Laser Ready!", True, CYAN)
                self.screen.blit(text, (20, status_y))
                status_y += 40
                
            if player.has_multi_shot:
                time_left = (player.multi_shot_end_time - current_time) / 1000
                text = self.small_font.render(f"{player_label}Multi-Shot: {time_left:.1f}s", True, YELLOW)
                self.screen.blit(text, (20, status_y))
                status_y += 40
                
            if player.invincible:
                time_left = (player.invincible_end_time - current_time) / 1000
                text = self.small_font.render(f"{player_label}Invincible: {time_left:.1f}s", True, PURPLE)
                self.screen.blit(text, (20, status_y))
                status_y += 40
        
        # Game over screen
        if self.game_over and not self.awaiting_name_input:
            game_over_text = self.font.render("GAME OVER", True, RED)
            final_score_text = self.small_font.render(f"Final Score: {self.score:,}", True, WHITE)
            level_reached_text = self.small_font.render(f"Level Reached: {self.level}", True, WHITE)
            restart_text = self.small_font.render("Press R to restart or ESC for title", True, WHITE)
            
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80))
            score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20))
            level_rect = level_reached_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30))
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80))
            
            self.screen.blit(game_over_text, text_rect)
            self.screen.blit(final_score_text, score_rect)
            self.screen.blit(level_reached_text, level_rect)
            self.screen.blit(restart_text, restart_rect)
            
        # Instructions
        if not self.game_over:
            instructions = [
                "P1: WASD/Arrows + Space",
                "ESC: Return to title",
                f"Enemy speed: {self.calculate_enemy_speed_for_level(self.level):.1f}"
            ]
            if self.coop_mode:
                instructions.insert(1, "P2: Right Ctrl (or controller)")
                
            for i, instruction in enumerate(instructions):
                text = self.small_font.render(instruction, True, WHITE)
                self.screen.blit(text, (SCREEN_WIDTH - 500, 20 + i * 40))
        
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
                if not self.awaiting_name_input:
                    self.handle_input()
                    self.update()
                self.draw()
                self.clock.tick(60)
                
        return result

def main():
    score_manager = HighScoreManager()
    
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    except:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
    clock = pygame.time.Clock()
    
    while True:
        title_screen = TitleScreen(screen, score_manager)
        
        while True:
            action = title_screen.handle_events()
            if action == "quit":
                pygame.quit()
                sys.exit()
            elif action == "highscores":
                high_score_screen = HighScoreScreen(screen, score_manager)
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
            elif action in ["single", "coop"]:
                game = Game(score_manager)
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