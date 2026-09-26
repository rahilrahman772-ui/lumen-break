"""Gameplay entities for the breakout core loop."""
import random
import math
import pygame

from . import constants as C
from .ui import lerp_color


class Paddle:
    WIDTH_NORMAL = 110
    HEIGHT = 16

    def __init__(self):
        self.width = self.WIDTH_NORMAL
        self.x = C.WIDTH / 2
        self.y = C.HEIGHT - 46
        self.speed = 620
        self.wide_timer = 0.0

    def rect(self):
        r = pygame.Rect(0, 0, int(self.width), self.HEIGHT)
        r.center = (int(self.x), int(self.y))
        return r

    def set_wide(self, duration=8.0):
        self.wide_timer = duration
        self.width = self.WIDTH_NORMAL * 1.6

    def update(self, dt, keys, mouse_x=None):
        if mouse_x is not None:
            self.x = mouse_x
        else:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.x -= self.speed * dt
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.x += self.speed * dt
        half = self.width / 2
        self.x = max(half, min(C.WIDTH - half, self.x))

        if self.wide_timer > 0:
            self.wide_timer -= dt
            if self.wide_timer <= 0:
                self.width = self.WIDTH_NORMAL

    def draw(self, surface):
        r = self.rect()
        glow = pygame.Surface((r.width + 20, r.height + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*C.AMBER, 60), glow.get_rect(), border_radius=10)
        surface.blit(glow, (r.left - 10, r.top - 10))
        pygame.draw.rect(surface, C.AMBER, r, border_radius=8)
        inner = r.inflate(-r.width * 0.5, -8)
        pygame.draw.rect(surface, (255, 224, 191), inner, border_radius=6)


class Ball:
    RADIUS = 8

    def __init__(self, x, y, speed=360, angle_deg=-60):
        self.x, self.y = x, y
        rad = math.radians(angle_deg)
        self.vx = speed * math.cos(rad)
        self.vy = speed * math.sin(rad)
        self.trail = []

    def speed(self):
        return math.hypot(self.vx, self.vy)

    def set_speed(self, s):
        cur = self.speed()
        if cur == 0:
            return
        scale = s / cur
        self.vx *= scale
        self.vy *= scale

    def update(self, dt):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 10:
            self.trail.pop(0)
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.x - self.RADIUS <= 0:
            self.x = self.RADIUS
            self.vx *= -1
        elif self.x + self.RADIUS >= C.WIDTH:
            self.x = C.WIDTH - self.RADIUS
            self.vx *= -1
        if self.y - self.RADIUS <= C.HUD_HEIGHT:
            self.y = C.HUD_HEIGHT + self.RADIUS
            self.vy *= -1

    def rect(self):
        r = pygame.Rect(0, 0, self.RADIUS * 2, self.RADIUS * 2)
        r.center = (int(self.x), int(self.y))
        return r

    def bounce_off_paddle(self, paddle):
        offset = (self.x - paddle.x) / (paddle.width / 2)
        offset = max(-1, min(1, offset))
        angle = -90 + offset * 65  # degrees, upward fan
        speed = min(self.speed() * 1.02, 780)
        rad = math.radians(angle)
        self.vx = speed * math.cos(rad)
        self.vy = speed * math.sin(rad)

    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            a = int(120 * (i / len(self.trail)))
            s = pygame.Surface((self.RADIUS * 2, self.RADIUS * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C.TEAL, a), (self.RADIUS, self.RADIUS), self.RADIUS)
            surface.blit(s, (tx - self.RADIUS, ty - self.RADIUS))
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), self.RADIUS)
        pygame.draw.circle(surface, C.TEAL, (int(self.x), int(self.y)), self.RADIUS, width=2)


class Brick:
    def __init__(self, x, y, w, h, hp, color):
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.hp = hp
        self.max_hp = hp
        self.color = color
        self.alive = True
        self.hit_flash = 0.0

    def hit(self):
        self.hp -= 1
        self.hit_flash = 1.0
        if self.hp <= 0:
            self.alive = False

    def update(self, dt):
        if self.hit_flash > 0:
            self.hit_flash -= dt * 6

    def draw(self, surface):
        t = self.hp / self.max_hp
        color = lerp_color((60, 55, 75), self.color, 0.35 + 0.65 * t)
        if self.hit_flash > 0:
            color = lerp_color(color, (255, 255, 255), max(0, self.hit_flash))
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, tuple(min(255, c + 30) for c in color),
                          self.rect, width=1, border_radius=5)


class Particle:
    def __init__(self, x, y, color):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(60, 260)
        self.x, self.y = x, y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.uniform(0.3, 0.7)
        self.max_life = self.life
        self.color = color
        self.size = random.uniform(2, 4)

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 380 * dt  # gravity
        self.vx *= 0.98

    @property
    def alive(self):
        return self.life > 0

    def draw(self, surface):
        t = max(0, self.life / self.max_life)
        s = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, int(255 * t)), (3, 3), max(1, self.size * t))
        surface.blit(s, (self.x - 3, self.y - 3))


class PowerUp:
    KINDS = ["wide", "slow", "multi"]
    LABELS = {"wide": "WIDE", "slow": "SLOW", "multi": "MULTI"}
    COLORS = {"wide": C.AMBER, "slow": C.TEAL, "multi": C.ROSE}

    def __init__(self, x, y, kind=None):
        self.x, self.y = x, y
        self.kind = kind or random.choice(self.KINDS)
        self.vy = 140

    def update(self, dt):
        self.y += self.vy * dt

    def rect(self):
        r = pygame.Rect(0, 0, 26, 26)
        r.center = (int(self.x), int(self.y))
        return r

    def draw(self, surface):
        r = self.rect()
        color = self.COLORS[self.kind]
        pygame.draw.rect(surface, (30, 24, 44), r, border_radius=6)
        pygame.draw.rect(surface, color, r, width=2, border_radius=6)
        from .ui import draw_text
        draw_text(surface, self.LABELS[self.kind][0], 16, color, center=r.center, bold=True)


def build_level(level_index):
    """Return a list of Brick objects for the given level (0-based)."""
    cols = 10
    rows = min(4 + level_index, 7)
    margin_x, margin_y = 30, 20
    gap = 6
    top = C.HUD_HEIGHT + 40
    bw = (C.WIDTH - 2 * margin_x - (cols - 1) * gap) / cols
    bh = 22
    bricks = []
    for row in range(rows):
        hp = 1 + (row // 2) + (level_index // 3)
        color = C.BRICK_ROW_COLORS[row % len(C.BRICK_ROW_COLORS)]
        for col in range(cols):
            x = margin_x + col * (bw + gap)
            y = top + margin_y + row * (bh + gap)
            bricks.append(Brick(x, y, bw, bh, hp, color))
    return bricks
