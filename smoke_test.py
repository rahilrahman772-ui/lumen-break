import pygame
from src.app import App
from src import screens
from src import constants as C

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


assert isinstance(app.current, screens.MenuScreen)
step(5)
print("OK menu")

# Menu -> Settings
click((C.WIDTH // 2, 448))
step(20)  # let fade transition finish
assert isinstance(app.current, screens.SettingsScreen), type(app.current)
print("OK settings nav")

# drag slider, toggle fullscreen (then back off so window stays normal), back to menu
app.current.slider.handle_event(
    pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=app.current.slider.rect.center, button=1))
app.current.slider.handle_event(
    pygame.event.Event(pygame.MOUSEBUTTONUP, pos=app.current.slider.rect.center, button=1))
step(3)
click((C.WIDTH // 2, 500))  # back
step(20)
assert isinstance(app.current, screens.MenuScreen)
print("OK settings interactions + back")

# Menu -> Play
click((C.WIDTH // 2, 380))
step(20)
assert isinstance(app.current, screens.PlayScreen), type(app.current)
play = app.current
print("OK play nav, bricks:", len(play.bricks))

# Launch ball, force a bunch of brick hits deterministically
key(pygame.K_SPACE)
step(2)
assert not play.ball_attached

# Force-clear the level to exercise level-up path
for b in play.bricks:
    b.hp = 0
    b.alive = False
step(3)
print("OK level up ->", play.level_index)

# Force game over path
play.lives = 1
play._lose_life()
step(30)
assert isinstance(app.current, screens.GameOverScreen), type(app.current)
print("OK game over, high score saved:", app.save.get("high_score"))

# Retry
click((C.WIDTH // 2, 380))
step(20)
assert isinstance(app.current, screens.PlayScreen)
print("OK retry")

# Pause / resume / restart
key(pygame.K_ESCAPE)
step(2)
assert app.current.paused
click((app.current.pause_overlay.restart_btn.rect.centerx,
       app.current.pause_overlay.restart_btn.rect.centery))
step(2)
assert not app.current.paused
print("OK pause/restart")

# Powerup pickup path
p = play if False else app.current
from src.entities import PowerUp
pu = PowerUp(p.paddle.x, p.paddle.y - 5, kind="wide")
p.powerups.append(pu)
step(3)
print("OK powerup handling, paddle width:", p.paddle.width)

print("ALL SMOKE TESTS PASSED")
