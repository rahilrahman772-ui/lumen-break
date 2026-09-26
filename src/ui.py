"""
Small, dependency-free UI toolkit used by every screen.

Nothing here is Pygame-idiomatic-minimal; each widget owns its own
animation state (hover progress, press feedback, drag position) so
screens stay declarative: create widgets, call .update()/.draw()/.handle_event().
"""
import pygame

# --------------------------------------------------------------------------
# Easing
# --------------------------------------------------------------------------

def lerp(a, b, t):
    return a + (b - a) * t


def ease_out_cubic(t):
    t -= 1
    return t * t * t + 1


def ease_in_out_quad(t):
    if t < 0.5:
        return 2 * t * t
    return 1 - pow(-2 * t + 2, 2) / 2


def lerp_color(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


# --------------------------------------------------------------------------
# Fonts (cached, with a graceful fallback chain across platforms)
# --------------------------------------------------------------------------
_FONT_CACHE = {}
_PREFERRED_FAMILIES = ["Verdana", "Segoe UI", "DejaVu Sans", "Arial", "Helvetica"]


def get_font(size, bold=False):
    key = (size, bold)
    if key not in _FONT_CACHE:
        chosen = pygame.font.match_font(_PREFERRED_FAMILIES, bold=bold)
        if chosen:
            _FONT_CACHE[key] = pygame.font.Font(chosen, size)
        else:
            _FONT_CACHE[key] = pygame.font.SysFont(None, size, bold=bold)
    return _FONT_CACHE[key]


def draw_text(surface, text, size, color, center=None, topleft=None, bold=False):
    font = get_font(size, bold=bold)
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = center
    elif topleft:
        rect.topleft = topleft
    surface.blit(surf, rect)
    return rect


# --------------------------------------------------------------------------
# Button
# --------------------------------------------------------------------------
class Button:
    """A text button with hover-lift and press-squash feedback."""

    def __init__(self, center, size, label, on_click=None, accent=(255, 179, 102),
                 style="solid"):
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center
        self.label = label
        self.on_click = on_click
        self.accent = accent
        self.style = style  # "solid" or "ghost"
        self.hover_t = 0.0
        self.press_t = 0.0
        self._pressed = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed and self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
            self._pressed = False

    def update(self, dt, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        target = 1.0 if hovered else 0.0
        self.hover_t += (target - self.hover_t) * min(1.0, dt * 10)
        press_target = 1.0 if (self._pressed and hovered) else 0.0
        self.press_t += (press_target - self.press_t) * min(1.0, dt * 16)

    def draw(self, surface):
        lift = -4 * ease_out_cubic(self.hover_t)
        squash = 1.0 - 0.06 * self.press_t
        w = int(self.rect.width * squash)
        h = self.rect.height
        r = pygame.Rect(0, 0, w, h)
        r.center = (self.rect.centerx, self.rect.centery + lift)

        if self.style == "solid":
            base = lerp_color((40, 33, 56), self.accent, 0.15 + 0.15 * self.hover_t)
            pygame.draw.rect(surface, base, r, border_radius=10)
            border = lerp_color(self.accent, (255, 255, 255), 0.2 * self.hover_t)
            pygame.draw.rect(surface, border, r, width=2, border_radius=10)
            text_color = lerp_color((238, 233, 248), (20, 16, 28), 0.0)
        else:  # ghost
            border = lerp_color((90, 82, 112), self.accent, self.hover_t)
            pygame.draw.rect(surface, border, r, width=2, border_radius=10)
            text_color = lerp_color((180, 172, 200), self.accent, self.hover_t)

        draw_text(surface, self.label, 22, text_color, center=r.center, bold=True)


# --------------------------------------------------------------------------
# Slider
# --------------------------------------------------------------------------
class Slider:
    """A horizontal 0..1 slider with a labeled value readout."""

    def __init__(self, center, width, label, value=0.5, on_change=None,
                 accent=(86, 204, 191)):
        self.rect = pygame.Rect(0, 0, width, 6)
        self.rect.center = center
        self.label = label
        self.value = value
        self.on_change = on_change
        self.accent = accent
        self.dragging = False
        self.hover_t = 0.0

    def _handle_radius(self):
        return 11

    def _handle_pos(self):
        x = self.rect.left + self.value * self.rect.width
        return (int(x), self.rect.centery)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hx, hy = self._handle_pos()
            if (event.pos[0] - hx) ** 2 + (event.pos[1] - hy) ** 2 <= (self._handle_radius() + 6) ** 2 \
                    or self.rect.collidepoint(event.pos):
                self.dragging = True
                self._set_from_mouse(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_mouse(event.pos[0])

    def _set_from_mouse(self, x):
        t = (x - self.rect.left) / self.rect.width
        self.value = max(0.0, min(1.0, t))
        if self.on_change:
            self.on_change(self.value)

    def update(self, dt, mouse_pos):
        hovered = self.rect.inflate(0, 30).collidepoint(mouse_pos)
        target = 1.0 if (hovered or self.dragging) else 0.0
        self.hover_t += (target - self.hover_t) * min(1.0, dt * 10)

    def draw(self, surface):
        draw_text(surface, self.label, 16, (150, 141, 173),
                  topleft=(self.rect.left, self.rect.top - 30))
        pygame.draw.rect(surface, (40, 33, 56), self.rect, border_radius=3)
        fill = pygame.Rect(self.rect.left, self.rect.top,
                            int(self.rect.width * self.value), self.rect.height)
        pygame.draw.rect(surface, self.accent, fill, border_radius=3)
        hx, hy = self._handle_pos()
        radius = self._handle_radius() + int(2 * self.hover_t)
        pygame.draw.circle(surface, (238, 233, 248), (hx, hy), radius)
        pygame.draw.circle(surface, self.accent, (hx, hy), radius, width=3)
        pct = f"{int(self.value * 100)}%"
        draw_text(surface, pct, 16, (150, 141, 173),
                  topleft=(self.rect.right + 16, self.rect.top - 30))


# --------------------------------------------------------------------------
# Toggle
# --------------------------------------------------------------------------
class Toggle:
    """An animated on/off switch."""

    def __init__(self, center, label, value=False, on_change=None,
                 accent=(86, 204, 191)):
        self.rect = pygame.Rect(0, 0, 52, 28)
        self.rect.center = center
        self.label = label
        self.value = value
        self.on_change = on_change
        self.accent = accent
        self.anim_t = 1.0 if value else 0.0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.inflate(20, 20).collidepoint(event.pos):
                self.value = not self.value
                if self.on_change:
                    self.on_change(self.value)

    def update(self, dt, mouse_pos):
        target = 1.0 if self.value else 0.0
        self.anim_t += (target - self.anim_t) * min(1.0, dt * 12)

    def draw(self, surface):
        draw_text(surface, self.label, 16, (150, 141, 173),
                  topleft=(self.rect.left - 0, self.rect.top - 30))
        track = lerp_color((40, 33, 56), self.accent, 0.5 + 0.5 * self.anim_t)
        pygame.draw.rect(surface, track, self.rect, border_radius=self.rect.height // 2)
        knob_x = lerp(self.rect.left + 14, self.rect.right - 14, self.anim_t)
        pygame.draw.circle(surface, (238, 233, 248), (int(knob_x), self.rect.centery), 11)


# --------------------------------------------------------------------------
# Screen transition
# --------------------------------------------------------------------------
class FadeTransition:
    """Fades to a color and back; call start(), then update()+draw() each frame."""

    def __init__(self, duration=0.35, color=(13, 10, 20)):
        self.duration = duration
        self.color = color
        self.t = duration  # start finished/idle
        self.on_midpoint = None
        self._fired = True

    def start(self, on_midpoint=None):
        self.t = 0.0
        self.on_midpoint = on_midpoint
        self._fired = False

    @property
    def active(self):
        return self.t < self.duration

    def update(self, dt):
        if self.t < self.duration:
            self.t += dt
            if not self._fired and self.t >= self.duration / 2:
                self._fired = True
                if self.on_midpoint:
                    self.on_midpoint()

    def draw(self, surface):
        if self.t >= self.duration:
            return
        progress = self.t / self.duration
        alpha = 255 * (1 - abs(progress - 0.5) * 2)
        overlay = pygame.Surface(surface.get_size())
        overlay.fill(self.color)
        overlay.set_alpha(int(alpha))
        surface.blit(overlay, (0, 0))
