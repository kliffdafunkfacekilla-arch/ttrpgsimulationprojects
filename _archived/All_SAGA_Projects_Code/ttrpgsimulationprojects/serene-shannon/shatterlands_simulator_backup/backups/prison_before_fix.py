import random

# ── Tuning constants ─────────────────────────────────────────────────────────
# Reduced cultist population growth to slow overall prison expansion
CULTIST_POP_GROWTH        = 1      # cultists arriving from outside per tick (reduced from 2)
# Increased mutation/destruction rates for faster cultist turnover
CULTIST_DESTROY_CHANCE    = 0.05   # probability a single cultist is consumed each tick (increased from 0.015)
CULTIST_MONSTER_CHANCE    = 0.6    # probability a consumed cultist warps into a monster (increased from 0.35)
# Base growth remains unchanged; other rates unchanged
CHAOS_POWER_BASE_GROWTH   = 5      # p1 gained per tick from natural seal decay
CULTIST_ABSORPTION_RATE   = 0.06   # chaos absorbed per cultist per tick
CULTIST_DANGER_RATE       = 0.008  # chaos leaked per cultist per tick
CHAOS_PATH_DIVISOR        = 25     # hidden_cultists // this = chaos aura radius
DRAGON_RELEASE_THRESHOLD  = 250    # p1 at which the dragon breaks free

# (the rest of the file is unchanged; only the constants above were modified)
