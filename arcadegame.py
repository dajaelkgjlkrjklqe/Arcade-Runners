import pygame
from PIL import Image
import random
import math
from enum import Enum
from typing import List, Tuple
import sys
import os

# Initialize pygame
pygame.init()
pygame.mixer.init()

class GameState(Enum):
    OPENING_CRAWL = 1
    MENU = 2
    PLAYING = 3
    CUTSCENE = 4
    GAME_OVER = 5

class PowerUpType(Enum):
    SHIELD = 1
    RAPID_FIRE = 2
    SLOW_TIME = 3
    MULTI_LIFE = 4

class Config:
    """Game configuration constants"""
    SCREEN_WIDTH = 900
    SCREEN_HEIGHT = 700
    FPS = 60
    
    # Player settings
    PLAYER_SPEED = 5
    PLAYER_SCALE = 2
    PLAYER_FRAME_DELAY = 5
    DASH_DISTANCE = 80
    DASH_COOLDOWN = 1000  # milliseconds
    
    # Enemy settings
    ENEMY_SCALE = 2
    CUTSCENE_TRIGGER_SCORE = 1000
    
    # Projectile settings
    PROJECTILE_COLOR = (255, 0, 0)
    PROJECTILE_SIZE = (20, 10)
    PROJECTILE_SPEED = 7
    PROJECTILE_FIRE_DELAY = 14
    
    # Power-up settings
    POWERUP_SPAWN_CHANCE = 0.002  # Per frame chance
    POWERUP_SIZE = 25
    POWERUP_DURATION = 5000  # 5 seconds
    
    # Game settings
    INITIAL_LIVES = 3
    CUTSCENE_MESSAGE_DURATION = 3000
    DIFFICULTY_INCREASE_SCORE = 500
    
    # Colors
    BACKGROUND_COLOR = (15, 15, 25)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 100, 255)
    YELLOW = (255, 255, 0)
    PURPLE = (128, 0, 128)
    ORANGE = (255, 165, 0)
    CYAN = (0, 255, 255)

class Particle:
    """Visual particle for effects"""
    def __init__(self, x, y, color, velocity, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = random.randint(2, 5)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1  # gravity
        self.lifetime -= 1
        return self.lifetime > 0
    
    def draw(self, screen):
        alpha = self.lifetime / self.max_lifetime
        color = tuple(int(c * alpha) for c in self.color)
        if alpha > 0:
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)

class ParticleSystem:
    """Manages visual particles"""
    def __init__(self):
        self.particles = []
    
    def add_explosion(self, x, y, color=Config.ORANGE, count=15):
        for _ in range(count):
            velocity = (random.uniform(-3, 3), random.uniform(-5, -1))
            lifetime = random.randint(20, 40)
            self.particles.append(Particle(x, y, color, velocity, lifetime))
    
    def add_trail(self, x, y, color=Config.CYAN):
        velocity = (random.uniform(-1, 1), random.uniform(-1, 1))
        lifetime = random.randint(10, 20)
        self.particles.append(Particle(x, y, color, velocity, lifetime))
    
    def update(self):
        self.particles = [p for p in self.particles if p.update()]
    
    def draw(self, screen):
        for particle in self.particles:
            particle.draw(screen)

class PowerUp:
    """Power-up collectibles"""
    def __init__(self, x, y):
        self.type = random.choice(list(PowerUpType))
        self.rect = pygame.Rect(x, y, Config.POWERUP_SIZE, Config.POWERUP_SIZE)
        self.bob_offset = random.uniform(0, math.pi * 2)
        self.spawn_time = pygame.time.get_ticks()
        
        # Define colors and symbols for each power-up type
        self.properties = {
            PowerUpType.SHIELD: {'color': Config.BLUE, 'symbol': 'S'},
            PowerUpType.RAPID_FIRE: {'color': Config.RED, 'symbol': 'R'},
            PowerUpType.SLOW_TIME: {'color': Config.PURPLE, 'symbol': 'T'},
            PowerUpType.MULTI_LIFE: {'color': Config.GREEN, 'symbol': '+'}
        }
    
    def update(self):
        # Bobbing animation
        time_alive = pygame.time.get_ticks() - self.spawn_time
        self.rect.y += math.sin(time_alive * 0.005 + self.bob_offset) * 0.5
        return time_alive < 10000  # Power-ups last 10 seconds
    
    def draw(self, screen):
        props = self.properties[self.type]
        
        # Draw glowing effect
        for i in range(3):
            alpha = 50 - i * 15
            glow_surf = pygame.Surface((Config.POWERUP_SIZE + i * 4, Config.POWERUP_SIZE + i * 4))
            glow_surf.set_alpha(alpha)
            glow_surf.fill(props['color'])
            glow_rect = glow_surf.get_rect(center=self.rect.center)
            screen.blit(glow_surf, glow_rect)
        
        # Draw main power-up
        pygame.draw.circle(screen, props['color'], self.rect.center, Config.POWERUP_SIZE // 2)
        pygame.draw.circle(screen, Config.WHITE, self.rect.center, Config.POWERUP_SIZE // 2, 2)
        
        # Draw symbol
        font = pygame.font.SysFont(None, 20)
        text = font.render(props['symbol'], True, Config.WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

class OpeningCrawl:
    """Star Wars-style opening crawl"""
    
    def __init__(self):
        self.font_title = pygame.font.Font(None, 48)
        self.font_text = pygame.font.Font(None, 28)
        self.font_intro = pygame.font.Font(None, 32)
        
        # Opening crawl text
        self.text_lines = [
            ("INTRO", "A long time ago in a galaxy far,"),
            ("INTRO", "far away...."),
            ("", ""),
            ("TITLE", "THE ARCADE ADVENTURE"),
            ("TITLE", "SISTER'S QUEST"),
            ("", ""),
            ("TEXT", "In a digital realm of endless"),
            ("TEXT", "projectiles and ancient evils,"),
            ("TEXT", "a brave hero searches for"),
            ("TEXT", "their missing sister."),
            ("", ""),
            ("TEXT", "Armed only with quick reflexes"),
            ("TEXT", "and mysterious power-ups,"),
            ("TEXT", "they must survive the"),
            ("TEXT", "relentless assault while"),
            ("TEXT", "uncovering the truth behind"),
            ("TEXT", "their sister's disappearance."),
            ("", ""),
            ("TEXT", "The enemy grows stronger"),
            ("TEXT", "with each passing moment,"),
            ("TEXT", "but hope remains as long"),
            ("TEXT", "as the hero keeps fighting..."),
            ("", ""),
            ("TEXT", "Will you find her?"),
        ]
        
        # Create text surfaces
        self.text_surfaces = []
        for line_type, line_text in self.text_lines:
            if line_type == "INTRO":
                surface = self.font_intro.render(line_text, True, Config.CYAN)
            elif line_type == "TITLE":
                surface = self.font_title.render(line_text, True, Config.YELLOW)
            elif line_type == "TEXT":
                surface = self.font_text.render(line_text, True, Config.YELLOW)
            else:  # Empty line
                surface = self.font_text.render("", True, Config.YELLOW)
            self.text_surfaces.append(surface)
        
        # Initialize all attributes
        self.reset()
    
    def reset(self):
        """Reset the crawl for replay"""
        self.text_y_positions = [Config.SCREEN_HEIGHT + i * 50 for i in range(len(self.text_surfaces))]
        self.scroll_speed = 1.5
        self.skip_timer = 0
        self.can_skip = False
    
    def update(self):
        """Update the crawl animation"""
        # Move text upward
        for i in range(len(self.text_y_positions)):
            self.text_y_positions[i] -= self.scroll_speed
        
        # Check if crawl is complete (last line is off screen)
        if self.text_y_positions[-1] < -100:
            return True
        
        # Allow skipping after 2 seconds
        self.skip_timer += 1
        if self.skip_timer > 60:  # 2 seconds at 30 FPS
            self.can_skip = True
        
        return False
    
    def draw(self, screen):
        """Draw the opening crawl"""
        # Black starfield background
        screen.fill((5, 5, 15))  # Very dark blue instead of pure black
        
        # Draw stars
        for _ in range(50):
            x = random.randint(0, Config.SCREEN_WIDTH)
            y = random.randint(0, Config.SCREEN_HEIGHT)
            brightness = random.randint(100, 255)
            pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), 1)
        
        # Draw scrolling text with perspective effect
        for i, surface in enumerate(self.text_surfaces):
            y_pos = self.text_y_positions[i]
            
            # Only draw text that's visible
            if -100 < y_pos < Config.SCREEN_HEIGHT + 100:
                # Create perspective effect (text gets smaller as it goes up)
                if y_pos < Config.SCREEN_HEIGHT * 0.4:
                    scale_factor = max(0.3, (y_pos + 100) / (Config.SCREEN_HEIGHT * 0.4 + 100))
                    
                    # Scale the surface
                    if scale_factor < 1.0:
                        original_width = surface.get_width()
                        original_height = surface.get_height()
                        new_width = int(original_width * scale_factor)
                        new_height = int(original_height * scale_factor)
                        
                        if new_width > 0 and new_height > 0:
                            scaled_surface = pygame.transform.scale(surface, (new_width, new_height))
                            x_pos = Config.SCREEN_WIDTH // 2 - scaled_surface.get_width() // 2
                            screen.blit(scaled_surface, (x_pos, y_pos))
                    else:
                        x_pos = Config.SCREEN_WIDTH // 2 - surface.get_width() // 2
                        screen.blit(surface, (x_pos, y_pos))
                else:
                    x_pos = Config.SCREEN_WIDTH // 2 - surface.get_width() // 2
                    screen.blit(surface, (x_pos, y_pos))
        
        # Draw skip instruction
        if self.can_skip:
            skip_font = pygame.font.Font(None, 24)
            skip_text = skip_font.render("Press any key to skip...", True, Config.WHITE)
            screen.blit(skip_text, (10, Config.SCREEN_HEIGHT - 30))

class AssetManager:
    """Handles loading and managing game assets"""
    
    def __init__(self):
        self.images = {}
        self.sounds = {}
        self.player_frames = []
        
    def load_assets(self):
        """Load all game assets with error handling"""
        try:
            # Load images
            self.images['menu_bg'] = self._load_image("images/arcade.background.png")
            self.images['start_button'] = self._load_image("images/start.png")
            self.images['enemy'] = self._load_image("images/enemy.png", Config.ENEMY_SCALE)
            
            # Load player GIF frames
            self._load_player_gif("images/player.gif")
            
            # Load sounds
            self.sounds['hit'] = self._load_sound("sound/pop.mp3")
            self.sounds['game_over'] = self._load_sound("sound/gameover.mp3")
            self.sounds['background'] = "sound/cool.mp3"
            
        except Exception as e:
            print(f"Error loading assets: {e}")
            sys.exit(1)
    
    def _load_image(self, path: str, scale: float = 1.0) -> pygame.Surface:
        """Load and optionally scale an image"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Image file not found: {path}")
        
        image = pygame.image.load(path).convert_alpha()
        if scale != 1.0:
            new_size = (int(image.get_width() * scale), int(image.get_height() * scale))
            image = pygame.transform.scale(image, new_size)
        return image
    
    def _load_sound(self, path: str) -> pygame.mixer.Sound:
        """Load a sound file"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Sound file not found: {path}")
        return pygame.mixer.Sound(path)
    
    def _load_player_gif(self, path: str):
        """Load and process GIF frames for player animation"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"GIF file not found: {path}")
            
        gif = Image.open(path)
        try:
            while True:
                frame = gif.copy().convert("RGBA")
                new_size = (frame.width * Config.PLAYER_SCALE, frame.height * Config.PLAYER_SCALE)
                frame = frame.resize(new_size, Image.LANCZOS)
                
                # Convert PIL image to pygame surface
                pygame_image = pygame.image.fromstring(
                    frame.tobytes(), frame.size, frame.mode
                ).convert_alpha()
                self.player_frames.append(pygame_image)
                gif.seek(len(self.player_frames))
        except EOFError:
            pass

class Player:
    """Player class handling movement and animation"""
    
    def __init__(self, frames: List[pygame.Surface], start_pos: Tuple[int, int]):
        self.frames = frames
        self.current_frame = 0
        self.frame_counter = 0
        self.rect = frames[0].get_rect(center=start_pos)
        self.frozen = False
        
        # Dash mechanics
        self.last_dash_time = 0
        self.is_dashing = False
        self.dash_trail = []
        
        # Power-up effects
        self.shield_active = False
        self.shield_end_time = 0
        self.rapid_fire_active = False
        self.rapid_fire_end_time = 0
        self.slow_time_active = False
        self.slow_time_end_time = 0
        
    def update(self):
        """Update player animation and effects"""
        if not self.frozen:
            self.frame_counter += 1
            if self.frame_counter >= Config.PLAYER_FRAME_DELAY:
                self.frame_counter = 0
                self.current_frame = (self.current_frame + 1) % len(self.frames)
        
        # Update power-up effects
        current_time = pygame.time.get_ticks()
        if self.shield_active and current_time > self.shield_end_time:
            self.shield_active = False
        if self.rapid_fire_active and current_time > self.rapid_fire_end_time:
            self.rapid_fire_active = False
        if self.slow_time_active and current_time > self.slow_time_end_time:
            self.slow_time_active = False
        
        # Update dash trail
        if self.dash_trail:
            self.dash_trail = [(pos, alpha - 30) for pos, alpha in self.dash_trail if alpha > 0]
    
    def move(self, keys):
        """Handle player movement"""
        if self.frozen:
            return
        
        speed = Config.PLAYER_SPEED
        if self.slow_time_active:
            speed *= 1.5  # Move faster when time is slowed
            
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.rect.x -= speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.rect.x += speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.rect.y -= speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.rect.y += speed
        
        # Keep player on screen
        self.rect.clamp_ip(pygame.Rect(0, 0, Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
    
    def dash(self, keys):
        """Handle dash ability"""
        current_time = pygame.time.get_ticks()
        if (current_time - self.last_dash_time > Config.DASH_COOLDOWN and 
            (keys[pygame.K_SPACE] or keys[pygame.K_LSHIFT])):
            
            # Determine dash direction
            dx, dy = 0, 0
            if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = 1
            if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = 1
            
            # Default to forward dash if no direction
            if dx == 0 and dy == 0:
                dx = 1
            
            # Normalize diagonal movement
            if dx != 0 and dy != 0:
                dx *= 0.707
                dy *= 0.707
            
            # Perform dash
            old_pos = self.rect.center
            self.rect.x += int(dx * Config.DASH_DISTANCE)
            self.rect.y += int(dy * Config.DASH_DISTANCE)
            self.rect.clamp_ip(pygame.Rect(0, 0, Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
            
            # Add trail effect
            for i in range(5):
                trail_x = old_pos[0] + (self.rect.centerx - old_pos[0]) * (i / 5)
                trail_y = old_pos[1] + (self.rect.centery - old_pos[1]) * (i / 5)
                self.dash_trail.append(((trail_x, trail_y), 150 - i * 30))
            
            self.last_dash_time = current_time
            return True
        return False
    
    def activate_powerup(self, powerup_type):
        """Activate a power-up effect"""
        current_time = pygame.time.get_ticks()
        
        if powerup_type == PowerUpType.SHIELD:
            self.shield_active = True
            self.shield_end_time = current_time + Config.POWERUP_DURATION
        elif powerup_type == PowerUpType.RAPID_FIRE:
            self.rapid_fire_active = True
            self.rapid_fire_end_time = current_time + Config.POWERUP_DURATION
        elif powerup_type == PowerUpType.SLOW_TIME:
            self.slow_time_active = True
            self.slow_time_end_time = current_time + Config.POWERUP_DURATION
    
    def draw(self, screen: pygame.Surface):
        """Draw the player"""
        # Draw dash trail
        for (x, y), alpha in self.dash_trail:
            trail_surf = pygame.Surface((self.rect.width, self.rect.height))
            trail_surf.set_alpha(alpha)
            trail_surf.blit(self.frames[self.current_frame], (0, 0))
            screen.blit(trail_surf, (x - self.rect.width // 2, y - self.rect.height // 2))
        
        # Draw player
        screen.blit(self.frames[self.current_frame], self.rect)
        
        # Draw shield effect
        if self.shield_active:
            time_left = (self.shield_end_time - pygame.time.get_ticks()) / Config.POWERUP_DURATION
            alpha = int(100 * abs(math.sin(pygame.time.get_ticks() * 0.01)))
            shield_surf = pygame.Surface((self.rect.width + 10, self.rect.height + 10))
            shield_surf.set_alpha(alpha)
            shield_surf.fill(Config.BLUE)
            shield_rect = shield_surf.get_rect(center=self.rect.center)
            screen.blit(shield_surf, shield_rect)
    
    def freeze(self, frozen: bool = True):
        """Freeze/unfreeze player animation"""
        self.frozen = frozen

class Projectile:
    """Individual projectile class"""
    
    def __init__(self, x: int, y: int, speed_multiplier: float = 1.0):
        self.rect = pygame.Rect(x, y, *Config.PROJECTILE_SIZE)
        self.speed = Config.PROJECTILE_SPEED * speed_multiplier
        self.trail_positions = []
    
    def update(self, time_multiplier: float = 1.0) -> bool:
        """Update projectile position. Returns False if off-screen"""
        # Add trail effect
        self.trail_positions.append(self.rect.center)
        if len(self.trail_positions) > 5:
            self.trail_positions.pop(0)
        
        self.rect.x += self.speed * time_multiplier
        return self.rect.x <= Config.SCREEN_WIDTH
    
    def draw(self, screen: pygame.Surface):
        """Draw the projectile with trail"""
        # Draw trail
        for i, pos in enumerate(self.trail_positions[:-1]):
            alpha = (i + 1) * 40
            trail_color = tuple(min(255, c + 50) for c in Config.PROJECTILE_COLOR)
            trail_surf = pygame.Surface(Config.PROJECTILE_SIZE)
            trail_surf.set_alpha(alpha)
            trail_surf.fill(trail_color)
            screen.blit(trail_surf, (pos[0] - Config.PROJECTILE_SIZE[0]//2, 
                                   pos[1] - Config.PROJECTILE_SIZE[1]//2))
        
        # Draw main projectile
        pygame.draw.rect(screen, Config.PROJECTILE_COLOR, self.rect)
        pygame.draw.rect(screen, Config.WHITE, self.rect, 1)

class ProjectileManager:
    """Manages all projectiles"""
    
    def __init__(self):
        self.projectiles: List[Projectile] = []
        self.fire_counter = 0
        self.active = True
        self.difficulty_multiplier = 1.0
    
    def update(self, player):
        """Update all projectiles"""
        if not self.active:
            return
        
        # Adjust fire rate based on difficulty and player power-ups
        fire_delay = Config.PROJECTILE_FIRE_DELAY / self.difficulty_multiplier
        if player.rapid_fire_active:
            fire_delay *= 2  # Slower projectiles when player has rapid fire
        
        # Time multiplier for slow-time effect
        time_multiplier = 0.3 if player.slow_time_active else 1.0
        
        # Spawn new projectiles
        self.fire_counter += 1
        if self.fire_counter >= fire_delay:
            self.fire_counter = 0
            
            # Multiple projectiles at higher difficulty
            num_projectiles = 1 if self.difficulty_multiplier < 2 else 2
            for _ in range(num_projectiles):
                random_y = random.randint(0, Config.SCREEN_HEIGHT - Config.PROJECTILE_SIZE[1])
                speed_mult = random.uniform(0.8, 1.2) * self.difficulty_multiplier
                self.projectiles.append(Projectile(0, random_y, speed_mult))
        
        # Update existing projectiles
        self.projectiles = [proj for proj in self.projectiles 
                          if proj.update(time_multiplier)]
    
    def draw(self, screen: pygame.Surface):
        """Draw all projectiles"""
        for projectile in self.projectiles:
            projectile.draw(screen)
    
    def check_collision(self, player_rect: pygame.Rect, player) -> bool:
        """Check collision with player and remove colliding projectiles"""
        if player.shield_active:
            return False  # Shield blocks all damage
            
        for i, projectile in enumerate(self.projectiles):
            if projectile.rect.colliderect(player_rect):
                del self.projectiles[i]
                return True
        return False
    
    def update_difficulty(self, score):
        """Increase difficulty based on score"""
        self.difficulty_multiplier = 1.0 + (score // Config.DIFFICULTY_INCREASE_SCORE) * 0.3
    
    def clear(self):
        """Clear all projectiles"""
        self.projectiles.clear()
    
    def set_active(self, active: bool):
        """Enable/disable projectile spawning"""
        self.active = active

class Cutscene:
    """Handles cutscene logic"""
    
    def __init__(self, enemy_image: pygame.Surface):
        self.enemy_image = enemy_image
        self.active = False
        self.stage = 0
        self.timer_start = 0
        self.enemy_rect = None
        self.font = pygame.font.SysFont(None, 30)
        
        self.messages = [
            "We're trapped here forever and you'll never see your sister again",
            "I don't care, I will keep looking!"
        ]
    
    def start(self, player_rect: pygame.Rect):
        """Start the cutscene"""
        self.active = True
        self.stage = 0
        self.timer_start = pygame.time.get_ticks()
        
        # Position enemy near player
        enemy_width = self.enemy_image.get_width()
        enemy_height = self.enemy_image.get_height()
        self.enemy_rect = pygame.Rect(
            player_rect.left - enemy_width,
            player_rect.top - enemy_height // 2,
            enemy_width,
            enemy_height
        )
    
    def update(self) -> bool:
        """Update cutscene. Returns True if cutscene is complete"""
        if not self.active:
            return True
            
        current_time = pygame.time.get_ticks()
        
        if current_time - self.timer_start >= Config.CUTSCENE_MESSAGE_DURATION:
            self.stage += 1
            if self.stage >= len(self.messages):
                self.active = False
                return True
            self.timer_start = current_time
        
        return False
    
    def draw(self, screen: pygame.Surface, player_rect: pygame.Rect):
        """Draw cutscene elements"""
        if not self.active or self.enemy_rect is None:
            return
            
        # Draw enemy
        screen.blit(self.enemy_image, self.enemy_rect)
        
        # Draw current message
        if self.stage < len(self.messages):
            text_surface = self.font.render(self.messages[self.stage], True, Config.WHITE)
            
            if self.stage == 0:  # Enemy speaking
                text_pos = (self.enemy_rect.x, self.enemy_rect.y - 40)
            else:  # Player speaking
                text_pos = (player_rect.x, player_rect.y - 40)
            
            screen.blit(text_surface, text_pos)

class Game:
    """Main game class"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Enhanced Arcade Game")
        self.clock = pygame.time.Clock()
        
        # Initialize managers and assets
        self.asset_manager = AssetManager()
        self.asset_manager.load_assets()
        
        # Initialize game objects
        self.opening_crawl = OpeningCrawl()
        self.player = Player(
            self.asset_manager.player_frames,
            (Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2)
        )
        self.projectile_manager = ProjectileManager()
        self.cutscene = Cutscene(self.asset_manager.images['enemy'])
        self.particle_system = ParticleSystem()
        
        # Power-ups
        self.powerups = []
        
        # Game state
        self.state = GameState.OPENING_CRAWL  # Start with opening crawl
        self.lives = Config.INITIAL_LIVES
        self.score = 0
        self.font = pygame.font.SysFont(None, 40)
        self.small_font = pygame.font.SysFont(None, 24)
        self.game_start_time = 0
        self.cutscene_triggered = False
        
        # UI elements
        self.start_button_rect = None
        
        # Screen shake
        self.screen_shake = 0
        self.shake_offset = (0, 0)
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.VIDEORESIZE:
                Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT = event.w, event.h
                self.screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT), pygame.RESIZABLE)
                
                
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == GameState.MENU and self.start_button_rect:
                    if self.start_button_rect.collidepoint(event.pos):
                        self.start_game()
                elif self.state == GameState.GAME_OVER:
                    self.reset_game()
        
        return True
    
    def start_game(self):
        """Start a new game"""
        self.state = GameState.PLAYING
        self.lives = Config.INITIAL_LIVES
        self.score = 0
        self.cutscene_triggered = False
        self.game_start_time = pygame.time.get_ticks()
        self.player.rect.center = (Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2)
        self.projectile_manager.clear()
        self.projectile_manager.set_active(True)
        self.powerups.clear()
        self.particle_system = ParticleSystem()
        
        # Start background music
        try:
            pygame.mixer.music.load(self.asset_manager.sounds['background'])
            pygame.mixer.music.play(-1)
        except pygame.error:
            print("Could not load background music")
    
    def reset_game(self):
        """Reset game to menu"""
        self.state = GameState.MENU
        pygame.mixer.music.stop()
    
    def update_opening_crawl(self):
        """Update opening crawl"""
        if self.opening_crawl.update():
            self.state = GameState.MENU
    
    def update_game(self):
        """Update game logic"""
        if self.state != GameState.PLAYING:
            return
            
        # Check for cutscene trigger (only once when score reaches 1000)
        if (not self.cutscene_triggered and 
            self.score >= Config.CUTSCENE_TRIGGER_SCORE):
            self.cutscene_triggered = True
            self.state = GameState.CUTSCENE
            self.cutscene.start(self.player.rect)
            self.player.freeze(True)
            self.projectile_manager.set_active(False)
            return
        
        # Handle player input
        keys = pygame.key.get_pressed()
        self.player.move(keys)
        
        # Handle dash
        if self.player.dash(keys):
            self.particle_system.add_trail(self.player.rect.centerx, self.player.rect.centery)
        
        self.player.update()
        
        # Update difficulty
        self.projectile_manager.update_difficulty(self.score)
        
        # Update projectiles
        self.projectile_manager.update(self.player)
        
        # Update particles
        self.particle_system.update()
        
        # Update power-ups
        self.powerups = [p for p in self.powerups if p.update()]
        
        # Spawn power-ups
        if random.random() < Config.POWERUP_SPAWN_CHANCE:
            x = random.randint(50, Config.SCREEN_WIDTH - 50)
            y = random.randint(50, Config.SCREEN_HEIGHT - 50)
            self.powerups.append(PowerUp(x, y))
        
        # Check power-up collection
        for powerup in self.powerups[:]:
            if powerup.rect.colliderect(self.player.rect):
                if powerup.type == PowerUpType.MULTI_LIFE:
                    self.lives += 1
                else:
                    self.player.activate_powerup(powerup.type)
                
                self.particle_system.add_explosion(
                    powerup.rect.centerx, powerup.rect.centery,
                    powerup.properties[powerup.type]['color']
                )
                self.powerups.remove(powerup)
        
        # Check collisions
        if self.projectile_manager.check_collision(self.player.rect, self.player):
            if not self.player.shield_active:
                self.lives -= 1
                self.asset_manager.sounds['hit'].play()
                self.screen_shake = 10
                self.particle_system.add_explosion(
                    self.player.rect.centerx, self.player.rect.centery, Config.RED
                )
                
                if self.lives <= 0:
                    self.state = GameState.GAME_OVER
                    pygame.mixer.music.stop()
                    self.asset_manager.sounds['game_over'].play()
        
        # Update screen shake
        if self.screen_shake > 0:
            self.screen_shake -= 1
            self.shake_offset = (random.randint(-self.screen_shake, self.screen_shake),
                               random.randint(-self.screen_shake, self.screen_shake))
        else:
            self.shake_offset = (0, 0)
        
        # Update score
        self.score += 1
    
    def update_cutscene(self):
        """Update cutscene state"""
        if self.cutscene.update():
            self.state = GameState.PLAYING
            self.player.freeze(False)
            self.projectile_manager.set_active(True)
    
    def draw_menu(self):
        """Draw menu screen"""
        # Scale and draw background
        bg_scaled = pygame.transform.scale(
            self.asset_manager.images['menu_bg'],
            (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT)
        )
        self.screen.blit(bg_scaled, (0, 0))
        
        # Draw start button
        self.start_button_rect = self.asset_manager.images['start_button'].get_rect(
            center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2)
        )
        self.screen.blit(self.asset_manager.images['start_button'], self.start_button_rect)
        
        # Draw controls
        controls = [
            "Controls:",
            "WASD or Arrow Keys - Move",
            "Space or Shift - Dash",
            "",
            "Power-ups:",
            "S - Shield", "R - Slow Projectiles", 
            "T - Slow Time", "+ - Extra Life"
        ]
        
        for i, text in enumerate(controls):
            color = Config.YELLOW if i == 0 or i == 4 else Config.WHITE
            font = self.font if i == 0 or i == 4 else self.small_font
            if text:  # Skip empty lines
                control_text = font.render(text, True, color)
                self.screen.blit(control_text, (50, 50 + i * 25))
    
    def draw_game(self):
        """Draw game screen"""
        self.screen.fill(Config.BACKGROUND_COLOR)
        
        # Apply screen shake
        shake_surface = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        shake_surface.fill(Config.BACKGROUND_COLOR)
        
        # Draw game objects on shake surface
        self.player.draw(shake_surface)
        self.projectile_manager.draw(shake_surface)
        self.particle_system.draw(shake_surface)
        
        # Draw power-ups
        for powerup in self.powerups:
            powerup.draw(shake_surface)
        
        # Blit shake surface with offset
        self.screen.blit(shake_surface, self.shake_offset)
        
        # Draw UI (not affected by shake)
        self.draw_ui()
    
    def draw_ui(self):
        """Draw user interface"""
        # Lives
        lives_text = self.font.render(f"Lives: {self.lives}", True, Config.WHITE)
        self.screen.blit(lives_text, (10, 10))
        
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, Config.WHITE)
        self.screen.blit(score_text, (10, 50))
        
        # Difficulty
        diff_level = int(self.projectile_manager.difficulty_multiplier * 10) / 10
        diff_text = self.small_font.render(f"Difficulty: {diff_level}x", True, Config.YELLOW)
        self.screen.blit(diff_text, (10, 90))
        
        # Dash cooldown indicator
        current_time = pygame.time.get_ticks()
        dash_ready = current_time - self.player.last_dash_time > Config.DASH_COOLDOWN
        dash_color = Config.GREEN if dash_ready else Config.RED
        dash_text = self.small_font.render("DASH READY" if dash_ready else "DASH COOLDOWN", True, dash_color)
        self.screen.blit(dash_text, (Config.SCREEN_WIDTH - 150, 10))
        
        # Power-up indicators
        y_offset = 40
        if self.player.shield_active:
            time_left = (self.player.shield_end_time - current_time) / 1000
            shield_text = self.small_font.render(f"SHIELD: {time_left:.1f}s", True, Config.BLUE)
            self.screen.blit(shield_text, (Config.SCREEN_WIDTH - 150, y_offset))
            y_offset += 25
        
        if self.player.rapid_fire_active:
            time_left = (self.player.rapid_fire_end_time - current_time) / 1000
            rapid_text = self.small_font.render(f"SLOW PROJECTILES: {time_left:.1f}s", True, Config.RED)
            self.screen.blit(rapid_text, (Config.SCREEN_WIDTH - 200, y_offset))
            y_offset += 25
        
        if self.player.slow_time_active:
            time_left = (self.player.slow_time_end_time - current_time) / 1000
            slow_text = self.small_font.render(f"SLOW TIME: {time_left:.1f}s", True, Config.PURPLE)
            self.screen.blit(slow_text, (Config.SCREEN_WIDTH - 150, y_offset))
            y_offset += 25
        
        # Score milestone indicator
        if not self.cutscene_triggered and self.score < Config.CUTSCENE_TRIGGER_SCORE:
            remaining = Config.CUTSCENE_TRIGGER_SCORE - self.score
            milestone_text = self.small_font.render(f"Story Event in: {remaining}", True, Config.CYAN)
            milestone_rect = milestone_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 30))
            self.screen.blit(milestone_text, milestone_rect)
    
    def draw_cutscene(self):
        """Draw cutscene"""
        self.draw_game()  # Draw game elements first
        self.cutscene.draw(self.screen, self.player.rect)
    
    def draw_game_over(self):
        """Draw game over screen"""
        self.screen.fill(Config.BACKGROUND_COLOR)
        
        # Game over text with glow effect
        game_over_text = self.font.render("Game Over!", True, Config.RED)
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            glow_text = self.font.render("Game Over!", True, (100, 0, 0))
            glow_rect = glow_text.get_rect(center=(Config.SCREEN_WIDTH // 2 + offset[0], 
                                                 Config.SCREEN_HEIGHT // 2 - 50 + offset[1]))
            self.screen.blit(glow_text, glow_rect)
        
        game_over_rect = game_over_text.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Final score
        final_score_text = self.font.render(f"Final Score: {self.score}", True, Config.WHITE)
        score_rect = final_score_text.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2))
        self.screen.blit(final_score_text, score_rect)
        
        # Performance rating
        if self.score >= 5000:
            rating = "LEGENDARY!"
            rating_color = Config.YELLOW
        elif self.score >= 3000:
            rating = "AMAZING!"
            rating_color = Config.ORANGE
        elif self.score >= 1500:
            rating = "GREAT!"
            rating_color = Config.GREEN
        elif self.score >= 1000:
            rating = "GOOD!"
            rating_color = Config.BLUE
        else:
            rating = "Keep Trying!"
            rating_color = Config.WHITE
        
        rating_text = self.small_font.render(rating, True, rating_color)
        rating_rect = rating_text.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2 + 30))
        self.screen.blit(rating_text, rating_rect)
        
        # Click to continue
        continue_text = self.small_font.render("Click anywhere to return to menu", True, Config.WHITE)
        continue_rect = continue_text.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2 + 80))
        self.screen.blit(continue_text, continue_rect)
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            # Handle events
            running = self.handle_events()
            if not running:
                break
            
            # Update game state
            if self.state == GameState.OPENING_CRAWL:
                self.update_opening_crawl()
            elif self.state == GameState.PLAYING:
                self.update_game()
            elif self.state == GameState.CUTSCENE:
                self.update_cutscene()
            
            # Draw everything
            if self.state == GameState.OPENING_CRAWL:
                self.opening_crawl.draw(self.screen)
            elif self.state == GameState.MENU:
                self.draw_menu()
            elif self.state == GameState.PLAYING:
                self.draw_game()
            elif self.state == GameState.CUTSCENE:
                self.draw_cutscene()
            elif self.state == GameState.GAME_OVER:
                self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(Config.FPS)
        
        pygame.quit()

if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Game crashed: {e}")
        pygame.quit()
        sys.exit(1)