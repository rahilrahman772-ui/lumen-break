"""Every screen the app can show. Each implements handle_event/update/draw."""
import random
import pygame

from . import constants as C
from .ui import Button, Slider, Toggle, draw_text, lerp_color, ease_in_out_quad
from .entities import Paddle, Ball, Particle, PowerUp, build_level


def draw_background(surface, t):
    """Vertical gradient plus slow-drifting dot field, shared by every screen."""
    for y in range(0, C.HEIGHT, 4):
        f = y / C.HEIGHT
        color = lerp_color(C.BG_TOP, C.BG_BOTTOM, f)
        pygame.draw.rect(surface, color, (0, y, C.WIDTH, 4))

    random.seed(7)  # stable field, independent of gameplay RNG
    for i in range(46):
        x = (i * 197) % C.WIDTH
        base_y = (i * 131) % C.HEIGHT
        y = (base_y + t * (10 + (i % 5) * 4)) % C.HEIGHT
        size = 1 + (i % 3)
        alpha = 30 + (i % 4) * 15
        s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*C.TEAL, alpha), (size, size), size)
        surface.blit(s, (x, y))
    random.seed()


class MenuScreen:
    def __init__(self, app):
        self.app = app
        self.t = 0.0
        cx = C.WIDTH // 2
        self.buttons = [
            Button((cx, 380), (220, 56), "PLAY", on_click=app.go_play, accent=C.AMBER),
            Button((cx, 448), (220, 48), "SETTINGS", on_click=app.go_settings,
                   accent=C.TEAL, style="ghost"),
            Button((cx, 504), (220, 48), "QUIT", on_click=app.quit,
                   accent=C.ROSE, style="ghost"),
        ]

    def handle_event(self, event):
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt):
        self.t += dt
        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            b.update(dt, mouse)

    def draw(self, surface):
        draw_background(surface, self.t)
        pulse = 0.5 + 0.5 * pygame.math.Vector2(1, 0).rotate(self.t * 40).x
        title_color = lerp_color(C.AMBER, (255, 224, 191), pulse * 0.4)
        draw_text(surface, C.TITLE, C.FONT_DISPLAY, title_color,
                  center=(C.WIDTH // 2, 170), bold=True)
        draw_text(surface, "BREAK THE SIGNAL", C.FONT_BODY, C.TEXT_MUTED,
                  center=(C.WIDTH // 2, 220))
        for b in self.buttons:
            b.draw(surface)
        hs = self.app.save.get("high_score")
        draw_text(surface, f"HIGH SCORE  {hs}", C.FONT_SMALL, C.TEXT_MUTED,
                  center=(C.WIDTH // 2, C.HEIGHT - 30))


class SettingsScreen:
    def __init__(self, app):
        self.app = app
        self.t = 0.0
        cx = C.WIDTH // 2
        self.slider = Slider((cx, 300), 320, "EFFECTS INTENSITY",
                              value=app.save.get("effects_intensity") or 0.8,
                              on_change=self._set_effects, accent=C.TEAL)
        self.toggle = Toggle((cx, 400), "FULLSCREEN",
                              value=app.save.get("fullscreen"),
                              on_change=app.set_fullscreen, accent=C.AMBER)
        self.back = Button((cx, 500), (200, 48), "BACK", on_click=app.go_menu,
                            accent=C.TEAL, style="ghost")

    def _set_effects(self, v):
        self.app.save.set("effects_intensity", v)

    def handle_event(self, event):
        self.slider.handle_event(event)
        self.toggle.handle_event(event)
        self.back.handle_event(event)

    def update(self, dt):
        self.t += dt
        mouse = pygame.mouse.get_pos()
        self.slider.update(dt, mouse)
        self.toggle.update(dt, mouse)
        self.back.update(dt, mouse)

    def draw(self, surface):
        draw_background(surface, self.t)
        draw_text(surface, "SETTINGS", C.FONT_HEADING, C.TEXT_PRIMARY,
                  center=(C.WIDTH // 2, 160), bold=True)
        self.slider.draw(surface)
        self.toggle.draw(surface)
        self.back.draw(surface)


class PauseOverlay:
    def __init__(self, app, on_resume, on_restart):
        cx = C.WIDTH // 2
        self.resume_btn = Button((cx, 300), (220, 52), "RESUME", on_click=on_resume,
                                  accent=C.AMBER)
        self.restart_btn = Button((cx, 364), (220, 48), "RESTART", on_click=on_restart,
                                   accent=C.TEAL, style="ghost")
        self.menu_btn = Button((cx, 424), (220, 48), "MAIN MENU", on_click=app.go_menu,
                                accent=C.ROSE, style="ghost")
        self.buttons = [self.resume_btn, self.restart_btn, self.menu_btn]

    def handle_event(self, event):
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt):
        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            b.update(dt, mouse)

    def draw(self, surface):
        overlay = pygame.Surface((C.WIDTH, C.HEIGHT), pygame.SRCALPHA)
        overlay.fill((13, 10, 20, 190))
        surface.blit(overlay, (0, 0))
        draw_text(surface, "PAUSED", C.FONT_HEADING, C.TEXT_PRIMARY,
                  center=(C.WIDTH // 2, 210), bold=True)
        for b in self.buttons:
            b.draw(surface)


class PlayScreen:
    LIVES_START = 3

    def __init__(self, app):
        self.app = app
        self.reset()

    def reset(self):
        self.paddle = Paddle()
        self.balls = []
        self.bricks = []
        self.particles = []
        self.powerups = []
        self.score = 0
        self.lives = self.LIVES_START
        self.level_index = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.paused = False
        self.pause_overlay = None
        self.level_banner_t = 0.0
        self.game_over = False
        self._load_level()

    def _load_level(self):
        self.bricks = build_level(self.level_index)
        self._launch_new_ball()
        self.level_banner_t = 1.4

    def _launch_new_ball(self):
        self.balls = [self._make_attached_ball()]
        self.ball_attached = True

    def _make_attached_ball(self):
        b = Ball(self.paddle.x, self.paddle.y - 20, speed=380, angle_deg=-90)
        b.vx = b.vy = 0
        return b

    def _intensity(self):
        return self.app.save.get("effects_intensity") or 0.8

    def _spawn_particles(self, x, y, color, count=14):
        n = max(2, int(count * self._intensity()))
        for _ in range(n):
            self.particles.append(Particle(x, y, color))

    def _pause(self):
        self.paused = True
        self.pause_overlay = PauseOverlay(self.app, self._resume, self._restart)

    def _resume(self):
        self.paused = False
        self.pause_overlay = None

    def _restart(self):
        self.paused = False
        self.pause_overlay = None
        self.reset()

    def handle_event(self, event):
        if self.paused:
            self.pause_overlay.handle_event(event)
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._pause()
            elif event.key in (pygame.K_SPACE, pygame.K_UP) and self.ball_attached:
                self._launch()
        elif event.type == pygame.MOUSEBUTTONDOWN and self.ball_attached:
            self._launch()

    def _launch(self):
        self.ball_attached = False
        for b in self.balls:
            b.vx = random.uniform(-140, 140)
            b.vy = -380

    def update(self, dt):
        if self.game_over:
            return
        if self.paused:
            self.pause_overlay.update(dt)
            return

        self.level_banner_t = max(0.0, self.level_banner_t - dt)
        self.paddle.update(dt, pygame.key.get_pressed(), self._mouse_x_if_idle())

        if self.ball_attached:
            self.balls[0].x = self.paddle.x
            self.balls[0].y = self.paddle.y - 20
        else:
            for ball in self.balls:
                ball.update(dt)
            self._handle_collisions()
            self.balls = [b for b in self.balls if b.y - b.RADIUS < C.HEIGHT]
            if not self.balls:
                self._lose_life()

        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

        for pu in self.powerups:
            pu.update(dt)
        self._handle_powerup_pickup()
        self.powerups = [p for p in self.powerups if p.y < C.HEIGHT + 30]

        self.app.shaker.update(dt)

        if all(not b.alive for b in self.bricks):
            self.level_index += 1
            self._load_level()

    def _mouse_x_if_idle(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_a] or keys[pygame.K_d]:
            return None
        return pygame.mouse.get_pos()[0]

    def _handle_collisions(self):
        paddle_rect = self.paddle.rect()
        for ball in self.balls:
            brect = ball.rect()
            if paddle_rect.colliderect(brect) and ball.vy > 0:
                ball.bounce_off_paddle(self.paddle)
                self.app.shaker.add(0.08)

            for brick in self.bricks:
                if not brick.alive:
                    continue
                if brect.colliderect(brick.rect):
                    self._resolve_brick_hit(ball, brick)
                    break

    def _resolve_brick_hit(self, ball, brick):
        # Reflect based on which side was hit (approximate via overlap depth).
        overlap = ball.rect().clip(brick.rect)
        if overlap.width < overlap.height:
            ball.vx *= -1
        else:
            ball.vy *= -1

        brick.hit()
        self.combo += 1
        self.combo_timer = 1.1
        points = 10 * (1 + self.combo // 5)
        self.score += points

        if not brick.alive:
            self._spawn_particles(brick.rect.centerx, brick.rect.centery, brick.color)
            self.app.shaker.add(0.12)
            if random.random() < 0.16:
                self.powerups.append(PowerUp(brick.rect.centerx, brick.rect.centery))
        else:
            self.app.shaker.add(0.04)

    def _handle_powerup_pickup(self):
        paddle_rect = self.paddle.rect()
        remaining = []
        for pu in self.powerups:
            if paddle_rect.colliderect(pu.rect()):
                self._apply_powerup(pu.kind)
                self._spawn_particles(pu.x, pu.y, PowerUp.COLORS[pu.kind], count=10)
            else:
                remaining.append(pu)
        self.powerups = remaining

    def _apply_powerup(self, kind):
        if kind == "wide":
            self.paddle.set_wide()
        elif kind == "slow":
            for b in self.balls:
                b.set_speed(max(220, b.speed() * 0.7))
        elif kind == "multi" and self.balls:
            template = self.balls[0]
            for angle in (-30, 30):
                clone = Ball(template.x, template.y, speed=template.speed(),
                             angle_deg=angle - 90)
                self.balls.append(clone)

    def _lose_life(self):
        self.lives -= 1
        self.combo = 0
        if self.lives <= 0:
            self.game_over = True
            hs = self.app.save.get("high_score")
            if self.score > hs:
                self.app.save.set("high_score", self.score)
            self.app.go_gameover(self.score)
        else:
            self._launch_new_ball()

    def draw(self, surface):
        draw_background(surface, pygame.time.get_ticks() / 1000)
        shake = self.app.shaker.offset(self._intensity())
        world = pygame.Surface((C.WIDTH, C.HEIGHT), pygame.SRCALPHA)

        for brick in self.bricks:
            if brick.alive:
                brick.draw(world)
        for pu in self.powerups:
            pu.draw(world)
        self.paddle.draw(world)
        for ball in self.balls:
            ball.draw(world)
        for p in self.particles:
            p.draw(world)

        surface.blit(world, shake)
        self._draw_hud(surface)

        if self.level_banner_t > 0:
            a = min(1.0, self.level_banner_t / 0.4)
            s = pygame.Surface((C.WIDTH, 60), pygame.SRCALPHA)
            draw_text(s, f"LEVEL {self.level_index + 1}", C.FONT_HEADING,
                      (*C.TEXT_PRIMARY, int(255 * a)), center=(C.WIDTH // 2, 30), bold=True)
            surface.blit(s, (0, C.HEIGHT // 2 - 30))

        if self.ball_attached and self.level_banner_t <= 0:
            draw_text(surface, "CLICK OR PRESS SPACE TO LAUNCH", C.FONT_SMALL,
                      C.TEXT_MUTED, center=(C.WIDTH // 2, C.HEIGHT - 90))

        if self.paused:
            self.pause_overlay.draw(surface)

    def _draw_hud(self, surface):
        pygame.draw.rect(surface, C.PANEL, (0, 0, C.WIDTH, C.HUD_HEIGHT))
        pygame.draw.line(surface, C.PANEL_LIGHT, (0, C.HUD_HEIGHT), (C.WIDTH, C.HUD_HEIGHT), 2)
        draw_text(surface, f"SCORE {self.score}", C.FONT_BODY, C.TEXT_PRIMARY,
                  topleft=(20, 16), bold=True)
        if self.combo > 1:
            draw_text(surface, f"COMBO x{self.combo}", C.FONT_SMALL, C.ROSE,
                      center=(C.WIDTH // 2, 28), bold=True)
        draw_text(surface, f"LEVEL {self.level_index + 1}", C.FONT_SMALL, C.TEXT_MUTED,
                  center=(C.WIDTH // 2, C.HUD_HEIGHT + 14))
        for i in range(self.lives):
            cx = C.WIDTH - 24 - i * 22
            pygame.draw.rect(surface, C.AMBER, (cx - 8, 22, 16, 8), border_radius=3)


class GameOverScreen:
    def __init__(self, app, score):
        self.app = app
        self.score = score
        self.is_high = score >= app.save.get("high_score") and score > 0
        cx = C.WIDTH // 2
        self.retry_btn = Button((cx, 380), (220, 52), "RETRY", on_click=app.go_play,
                                 accent=C.AMBER)
        self.menu_btn = Button((cx, 444), (220, 48), "MAIN MENU", on_click=app.go_menu,
                                accent=C.TEAL, style="ghost")
        self.t = 0.0

    def handle_event(self, event):
        self.retry_btn.handle_event(event)
        self.menu_btn.handle_event(event)

    def update(self, dt):
        self.t += dt
        mouse = pygame.mouse.get_pos()
        self.retry_btn.update(dt, mouse)
        self.menu_btn.update(dt, mouse)

    def draw(self, surface):
        draw_background(surface, self.t)
        draw_text(surface, "GAME OVER", C.FONT_DISPLAY, C.ROSE,
                  center=(C.WIDTH // 2, 190), bold=True)
        draw_text(surface, f"SCORE {self.score}", C.FONT_HEADING, C.TEXT_PRIMARY,
                  center=(C.WIDTH // 2, 260))
        if self.is_high:
            pulse = 0.5 + 0.5 * ease_in_out_quad((pygame.time.get_ticks() % 900) / 900)
            color = lerp_color(C.AMBER, (255, 255, 255), pulse * 0.5)
            draw_text(surface, "NEW HIGH SCORE", C.FONT_BODY, color,
                      center=(C.WIDTH // 2, 300), bold=True)
        self.retry_btn.draw(surface)
        self.menu_btn.draw(surface)
