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
pygame.display.set_caption("Pulsewidth: Procedural Data-Sonification Arcade Engine")
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