"""Application shell: owns the window, the screen stack, and the main loop."""
import random
import sys
import pygame

from . import constants as C
from .ui import FadeTransition
from .state import Save
from .audio import Audio
from . import screens


class Shaker:
    """Trauma-based screen shake (decays quadratically, feels punchy but brief)."""

    def __init__(self):
        self.trauma = 0.0

    def add(self, amount):
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt):
        self.trauma = max(0.0, self.trauma - dt * 2.5)

    def offset(self, intensity_scale=1.0):
        t = self.trauma ** 2
        mag = 14 * t * intensity_scale
        if mag < 0.5:
            return (0, 0)
        return (random.uniform(-mag, mag), random.uniform(-mag, mag))


class App:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption(C.TITLE)
        self.save = Save()
        self.audio = Audio(self.save)
        flags = pygame.FULLSCREEN if self.save.get("fullscreen") else 0
        self.screen = pygame.display.set_mode((C.WIDTH, C.HEIGHT), flags)
        self.clock = pygame.time.Clock()
        self.shaker = Shaker()
        self.transition = FadeTransition(duration=0.3)
        self.running = True

        self.current = screens.MenuScreen(self)

    # --- navigation ------------------------------------------------------
    def _switch(self, factory):
        self.audio.play("click")

        def midpoint():
            self.current = factory()
        self.transition.start(on_midpoint=midpoint)

    def go_menu(self):
        self._switch(lambda: screens.MenuScreen(self))

    def go_settings(self):
        self._switch(lambda: screens.SettingsScreen(self))

    def go_play(self):
        self._switch(lambda: screens.PlayScreen(self))

    def go_gameover(self, score):
        self.audio.play("gameover")
        self._switch(lambda: screens.GameOverScreen(self, score))

    def set_fullscreen(self, value):
        self.save.set("fullscreen", value)
        self.audio.play("click")
        flags = pygame.FULLSCREEN if value else 0
        self.screen = pygame.display.set_mode((C.WIDTH, C.HEIGHT), flags)

    def set_volume(self, value):
        self.audio.set_volume(value)

    def quit(self):
        self.audio.play("click")
        self.running = False

    # --- loop --------------------------------------------------------------
    def run(self):
        while self.running:
            dt = min(0.05, self.clock.tick(C.FPS) / 1000)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif not self.transition.active:
                    self.current.handle_event(event)

            if not self.transition.active:
                self.current.update(dt)
            self.transition.update(dt)

            self.current.draw(self.screen)
            self.transition.draw(self.screen)
            pygame.display.flip()

        self.audio.shutdown()
        pygame.quit()
        sys.exit(0)
