"""
Design tokens for Lumen Break.

Visual identity: a warm/cool duotone on deep plum, rather than the
generic "single neon accent on pure black" look. Amber is the primary
accent (menus, score, player paddle); teal is secondary (bricks, UI
chrome); a soft rose is reserved for danger/alerts and combo highlights.
"""

WIDTH, HEIGHT = 960, 640
FPS = 60
TITLE = "LUMEN BREAK"

# --- Color palette -----------------------------------------------------
BG_TOP = (21, 16, 32)          # deep plum
BG_BOTTOM = (13, 10, 20)       # near-black plum
PANEL = (30, 24, 44)
PANEL_LIGHT = (40, 33, 56)

TEXT_PRIMARY = (238, 233, 248)
TEXT_MUTED = (150, 141, 173)

AMBER = (255, 179, 102)
AMBER_DIM = (168, 122, 78)
TEAL = (86, 204, 191)
TEAL_DIM = (58, 133, 126)
ROSE = (255, 110, 148)
ROSE_DIM = (168, 78, 100)

BRICK_ROW_COLORS = [ROSE, AMBER, TEAL, (140, 158, 255)]

# --- Layout --------------------------------------------------------------
HUD_HEIGHT = 56

# --- Type scale (sizes only; family resolved at runtime in ui.py) -------
FONT_DISPLAY = 56
FONT_HEADING = 30
FONT_BODY = 20
FONT_SMALL = 15

# --- Save file -----------------------------------------------------------
SAVE_FILE = "lumen_break_save.json"
