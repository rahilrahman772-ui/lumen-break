import random
import pygame
from src.app import App
from src import screens
from src import constants as C
from src.entities import Particle

app = App()


def step(n=1, dt=1 / 60):
    for _ in range(n):
        app.transition.update(dt)
        if not app.transition.active:
            app.current.update(dt)
        app.current.draw(app.screen)
        app.transition.draw(app.screen)


def click(pos):
    app.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
    app.current.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=1))


def key(k):
    app.current.handle_event(pygame.event.Event(pygame.KEYDOWN, key=k))


# 1. Menu
step(40)
pygame.image.save(app.screen, "shots/01_menu.png")

# 2. Settings
click((C.WIDTH // 2, 448))
step(20)
step(15)
pygame.image.save(app.screen, "shots/02_settings.png")

# 3. Gameplay mid-action: knock out some bricks, add particles + combo + powerup
click((C.WIDTH // 2, 500))  # back to menu
step(20)
click((C.WIDTH // 2, 380))  # play
step(20)
play = app.current
key(pygame.K_SPACE)
step(1)
random.seed(3)
for i, b in enumerate(play.bricks):
    if i % 3 == 0:
        b.alive = False
    elif i % 5 == 0:
        b.hit()
play.score = 4280
play.combo = 6
play.combo_timer = 0.6
play.lives = 2
for _ in range(40):
    play.particles.append(Particle(420 + random.uniform(-60, 60),
                                    260 + random.uniform(-20, 20), C.ROSE))
from src.entities import PowerUp
play.powerups.append(PowerUp(600, 340, kind="multi"))
play.app.shaker.add(0.5)
step(1)
pygame.image.save(app.screen, "shots/03_gameplay.png")

# 4. Game over
play.lives = 1
play._lose_life()
step(20)
pygame.image.save(app.screen, "shots/04_gameover.png")

print("Screenshots saved.")
