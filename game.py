import pygame
import sys
import random
import math
import numpy as np


pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2)


CARDWIDTH = 240
CARDHEIGHT = 135
SCALE = 4

SCREEN_WIDTH = CARDWIDTH * SCALE
SCREEN_HEIGHT = CARDHEIGHT * SCALE

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Procedural Data-Sonification Arcade Engine")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Courier", 20, bold=True)
small_font = pygame.font.SysFont("Courier", 12)

class SoundEngine:
    def __init__(self):
        self.sample_rate = 44100
        
        self.scales = {
            'ambient': [130.81, 146.83, 164.81, 196.00, 220.00, 261.63],
            'cyber': [110.00, 123.47, 146.83, 164.81, 196.00, 246.94, 293.66],
            'chaos': [100.00, 150.00, 210.00, 300.00, 450.00, 600.00]
        }
        self.current_scale = 'cyber'

    def play_tone(self, frequency, duration_ms=100, volume=0.3, wave_type='sine'):
        """Generates a raw numpy buffer audio tone on the fly from non-musical data parameters."""
        num_samples = int(self.sample_rate * (duration_ms / 1000.0))
        t = np.linspace(0, duration_ms / 1000.0, num_samples, endpoint=False)
        
        if wave_type == 'sine':
            wave = np.sin(2 * np.pi * frequency * t)
        elif wave_type == 'square':
            wave = np.sign(np.sin(2 * np.pi * frequency * t))
        elif wave_type == 'sawtooth':
            wave = 2 * (t * frequency - np.floor(0.5 + t * frequency))
        else:
            wave = np.sin(2 * np.pi * frequency * t)

        
        envelope = np.exp(-3.0 * t / (duration_ms / 1000.0))
        audio_data = wave * envelope * volume
        
        audio_data = np.int16(audio_data * 32767)
        stereo_data = np.column_stack((audio_data, audio_data))
        
        sound = pygame.sndarray.make_sound(stereo_data)
        sound.play()

    def get_data_mapped_frequency(self, x_pos, y_pos):
        """Maps coordinate data uniquely into structured musical notes."""
        scale = self.scales[self.current_scale]
        index = int((x_pos / CARDWIDTH) * len(scale)) % len(scale)
        base_freq = scale[index]
        
        modifier = 1.0 + ((CARDHEIGHT - y_pos) / CARDHEIGHT)
        return base_freq * modifier

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color):
        for _ in range(5):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            self.particles.append({
                'x': x, 'y': y,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'life': random.randint(15, 30),
                'color': color
            })

    def update_and_draw(self, surface):
        for p in self.particles[:]:
            p['x'] += p['dx']
            p['y'] += p['dy']
            p['life'] -= 1
            if p['life'] <= 0:
                self.particles.remove(p)
            else:
                pygame.draw.circle(surface, p['color'], (int(p['x'] * SCALE), int(p['y'] * SCALE)), 2)


class GameSession:
    def __init__(self):
        self.synth = SoundEngine()
        self.particles = ParticleSystem()
        self.reset()

    def reset(self):
        self.game_state = 'START'
        self.player_x = CARDWIDTH // 2
        self.player_y = CARDHEIGHT // 2
        self.player_size = 10
        self.player_speed = 3
        
        self.coins = 0
        self.score = 0
        self.speed_cost = 5
        self.size_cost = 3
        
        self.item_x = random.randint(20, CARDWIDTH - 20)
        self.item_y = random.randint(20, CARDHEIGHT - 20)
        
        self.obstacles = [
            {'x': 50, 'y': 40, 'w': 20, 'h': 6, 'dx': 1, 'dy': 0},
            {'x': 150, 'y': 90, 'w': 6, 'h': 20, 'dx': 0, 'dy': 1}
        ]
        self.frame_counter = 0

    def update(self):
        if self.game_state == 'PLAYING':
            self.frame_counter += 1
            
            keys = pygame.key.get_pressed()
            moved = False
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.player_x -= self.player_speed
                moved = True
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.player_x += self.player_speed
                moved = True
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.player_y -= self.player_speed
                moved = True
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.player_y += self.player_speed
                moved = True

            self.player_x = max(10, min(CARDWIDTH - 10, self.player_x))
            self.player_y = max(10, min(CARDHEIGHT - 10, self.player_y))

    
            if moved and self.frame_counter % 8 == 0:
                freq = self.synth.get_data_mapped_frequency(self.player_x, self.player_y)
                self.synth.play_tone(freq, duration_ms=80, volume=0.2, wave_type='square')

    
            for obs in self.obstacles:
                obs['x'] += obs['dx']
                obs['y'] += obs['dy']
                if obs['x'] <= 10 or obs['x'] + obs['w'] >= CARDWIDTH - 10:
                    obs['dx'] *= -1
                    self.synth.play_tone(80, duration_ms=50, volume=0.1, wave_type='sawtooth')
                if obs['y'] <= 10 or obs['y'] + obs['h'] >= CARDHEIGHT - 10:
                    obs['dy'] *= -1
                    self.synth.play_tone(95, duration_ms=50, volume=0.1, wave_type='sawtooth')

                
                if (self.player_x - self.player_size < obs['x'] + obs['w'] and
                    self.player_x + self.player_size > obs['x'] and
                    self.player_y - self.player_size < obs['y'] + obs['h'] and
                    self.player_y + self.player_size > obs['y']):
                    self.synth.play_tone(60.0, duration_ms=300, volume=0.5, wave_type='sawtooth')
                    self.game_state = 'GAMEOVER'

            
            distance_to_item = math.hypot(self.player_x - self.item_x, self.player_y - self.item_y)
            if distance_to_item < (self.player_size + 6):
                self.coins += 1
                self.score += 10
                self.particles.emit(self.item_x, self.item_y, (255, 215, 0))
                
                
                pickup_freq = self.synth.get_data_mapped_frequency(self.item_x, self.item_y) * 1.5
                self.synth.play_tone(pickup_freq, duration_ms=120, volume=0.4, wave_type='sine')
                
                
                self.item_x = random.randint(20, CARDWIDTH - 20)
                self.item_y = random.randint(20, CARDHEIGHT - 20)

    def draw(self, surface):
        surface.fill((15, 15, 25)) 


        pygame.draw.rect(surface, (50, 50, 80), (10 * SCALE, 10 * SCALE, (CARDWIDTH - 20) * SCALE, (CARDHEIGHT - 20) * SCALE), 2)

        if self.game_state == 'START':
            title_surf = font.render("DATA ARCADE", True, (0, 255, 200))
            sub_surf = small_font.render("Press 'S' to Launch Engine & Music", True, (200, 200, 200))
            info_surf = small_font.render("WASD to Move | Coordinates Drive the Synth", True, (120, 120, 180))
            
            surface.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 40 * SCALE))
            surface.blit(sub_surf, (SCREEN_WIDTH // 2 - sub_surf.get_width() // 2, 70 * SCALE))
            surface.blit(info_surf, (SCREEN_WIDTH // 2 - info_surf.get_width() // 2, 90 * SCALE))

        elif self.game_state == 'PLAYING' or self.game_state == 'SHOP':
            
            pulse_rad = int((self.player_size + math.sin(pygame.time.get_ticks() * 0.01) * 2) * SCALE)
            pygame.draw.circle(surface, (255, 215, 0), (int(self.item_x * SCALE), int(self.item_y * SCALE)), pulse_rad // 2)

        
            for obs in self.obstacles:
                pygame.draw.rect(surface, (255, 60, 90), (obs['x'] * SCALE, obs ['y'] * SCALE, obs ['w'] * SCALE, obs['h'] * SCALE))

            pygame.draw.circle(surface, (0,255, 280), (int(self.player_x * SCALE), int(self.player_y * SCALE)), self.player_size * SCALE // 2)

            self.particles.update_and_draw(surface)

            hud_text = small_font.render(f"COINS: {self.coins} | SCORE: {self.score} | SPEED: {self.player_speed}", True, (255, 255, 255))
            controls_text = small_font.render("[P] Shop / [Q] Quit", True (150, 150, 150))
            surface.blit(hud_text, (15 * SCALE, 12 * SCALE))
            surface.blit(controls_text, (15 * SCALE, 22))

            if self.game_state =='SHOP':
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCRALPHA)
                overlay.fill(0, 0, 0, 180))
                surface.blit(overlay, (0, 0))

                shop_title = font.render("DATA SYTH SHOP (UPGRADES)", True, (255, 255, 0))
                


