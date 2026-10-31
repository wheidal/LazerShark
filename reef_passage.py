"""
Reef passages: stretches of solid rock with a winding route through them.
Rock can't be destroyed, but coral plugs can be shot out to reach rewards.
"""
import random

import pygame

from food import SmallFish
from obstacle import ReefSegment
from powerup import MissilePowerup, TorpedoPowerup

# --- Tuning: adjust these while playtesting ---
FIRST_PASSAGE_MS = 15000
PASSAGE_INTERVAL_MS = 25000
ROWS_PER_PASSAGE = 7
ROW_SPACING = 260
WIDEST_GAP = 160
NARROWEST_GAP = 100
GAP_NARROWS_PER_SCORE = 0.5
PLUG_CHANCE = 0.35
PLUG_WIDTH = 110
FISH_EVERY_ROWS = 2
CLEAR_BONUS = 10
ROCK_DAMAGE = 33
ROCK_INVULN_MS = 1000
ROCK_PUSH = 10  # px per step, faster than the shark can swim back
ROUTE_SAFETY = 0.7  # Share of the theoretical sideways reach a route may demand

# --- Facts about the game that limit what's fair ---
SCREEN_W = 800
ROCK_H = 44
EDGE_MARGIN = 30
SCROLL_PER_STEP = 3
SHARK_SPEED = 5
SHARK_BODY_W = 45
SHARK_BODY_H = 104
SUB_CLEAR_MS = 6000  # Submarines scroll slower than rock, so stop them before a passage


def max_gap_shift(gap_w):
    """Largest fair sideways move between rows.

    The shark can't change lane while any of its body is level with a row, which
    leaves only the space between that row and the next for crossing over.
    """
    free_scroll = ROW_SPACING - ROCK_H - SHARK_BODY_H
    reach = free_scroll * SHARK_SPEED / SCROLL_PER_STEP
    return (gap_w - SHARK_BODY_W) + reach * ROUTE_SAFETY


class RockWall(pygame.sprite.Sprite):
    """Indestructible rock. Knows where its row's gap is, to push the shark to safety."""

    def __init__(self, x, w, gap_center, rng=random):
        super().__init__()
        self.image = pygame.Surface((w, ROCK_H), pygame.SRCALPHA)
        self.image.fill((58, 62, 74))
        pygame.draw.rect(self.image, (88, 94, 108), (0, 0, w, 10))
        pygame.draw.rect(self.image, (34, 36, 46), (0, ROCK_H - 8, w, 8))
        for _ in range(max(1, w // 12)):
            px, py = rng.randint(0, max(0, w - 1)), rng.randint(12, ROCK_H - 12)
            shade = rng.choice([(46, 50, 60), (72, 78, 90), (40, 42, 52)])
            pygame.draw.circle(self.image, shade, (px, py), rng.randint(2, 5))
        self.rect = self.image.get_rect(topleft=(x, -ROCK_H))
        self.gap_center = gap_center
        self.clear_bonus = 0


class ReefRow:
    """One row of a passage: an open gap, and optionally a coral plug hiding a reward."""

    def __init__(self, gap_x, gap_w, plug_x=None, has_fish=False, is_last=False, rng=random):
        self.gap_x = gap_x
        self.gap_w = gap_w
        self.plug_x = plug_x
        self.has_fish = has_fish
        self.is_last = is_last
        self.rng = rng

    @property
    def gap_center(self):
        return self.gap_x + self.gap_w // 2

    def rock_spans(self):
        """The (x, width) stretches of solid rock in this row."""
        holes = [(self.gap_x, self.gap_w)]
        if self.plug_x is not None:
            holes.append((self.plug_x, PLUG_WIDTH))
        spans, x = [], 0
        for hole_x, hole_w in sorted(holes):
            if hole_x > x:
                spans.append((x, hole_x - x))
            x = hole_x + hole_w
        if x < SCREEN_W:
            spans.append((x, SCREEN_W - x))
        return spans

    def build(self):
        """Create this row's sprites, returned as (rocks, plugs, foods, rewards)."""
        rocks = [RockWall(x, w, self.gap_center, self.rng) for x, w in self.rock_spans()]
        if self.is_last:
            rocks[0].clear_bonus = CLEAR_BONUS
        plugs, rewards, foods = [], [], []
        if self.plug_x is not None:
            plugs.append(ReefSegment(self.plug_x, PLUG_WIDTH))
            reward = self.rng.choice([MissilePowerup, TorpedoPowerup])
            rewards.append(reward(self.plug_x + PLUG_WIDTH // 2, -ROCK_H - 90))
        if self.has_fish:
            foods.append(SmallFish(self.gap_center, -ROCK_H - 130))
        return rocks, plugs, foods, rewards


class ReefPassageDirector:
    """Decides when a passage runs and generates a route that can always be followed."""

    def __init__(self, rng=random):
        self.rng = rng
        self.wait_ms = FIRST_PASSAGE_MS
        self.rows_left = 0
        self.clearing = False
        self.distance = 0
        self.gap_w = WIDEST_GAP
        self.gap_center = None
        self.score = 0

    @property
    def active(self):
        return self.rows_left > 0 or self.clearing

    @property
    def subs_allowed(self):
        return not self.active and self.wait_ms > SUB_CLEAR_MS

    def start(self, score=0):
        self.score = score
        self.rows_left = ROWS_PER_PASSAGE
        self.clearing = False
        self.distance = 0  # One row of open water first, so nothing overlaps the first row
        self.gap_w = max(NARROWEST_GAP, int(WIDEST_GAP - score * GAP_NARROWS_PER_SCORE))
        self.gap_center = None

    def update(self, dt, score):
        """Advance one step. Returns a new ReefRow when one is due."""
        if not self.active:
            self.wait_ms -= dt
            if self.wait_ms > 0:
                return None
            self.start(score)
        self.distance += SCROLL_PER_STEP
        if self.distance < ROW_SPACING:
            return None
        self.distance -= ROW_SPACING
        if self.rows_left == 0:
            self.clearing = False
            self.wait_ms = PASSAGE_INTERVAL_MS
            return None
        self.rows_left -= 1
        self.clearing = self.rows_left == 0
        return self._next_row()

    def _next_row(self):
        lowest = EDGE_MARGIN + self.gap_w // 2
        highest = SCREEN_W - EDGE_MARGIN - self.gap_w // 2
        if self.gap_center is None:
            center = self.rng.randint(lowest, highest)
        else:
            shift = self.rng.uniform(0.5, 1.0) * max_gap_shift(self.gap_w)
            if self.rng.random() < 0.5:
                shift = -shift
            center = self.gap_center + shift
            if not lowest <= center <= highest:
                center = self.gap_center - shift  # Bounce off the screen edge
            center = int(max(lowest, min(highest, center)))
        self.gap_center = center
        gap_x = center - self.gap_w // 2
        return ReefRow(gap_x, self.gap_w, self._plug_position(gap_x),
                       has_fish=self.rows_left % FISH_EVERY_ROWS == 0,
                       is_last=self.rows_left == 0, rng=self.rng)

    def _plug_position(self, gap_x):
        if self.rng.random() >= PLUG_CHANCE:
            return None
        clearance = 60  # Keep some rock between the plug and the open gap
        slots = []
        if gap_x - clearance - PLUG_WIDTH >= 0:
            slots.append((0, gap_x - clearance - PLUG_WIDTH))
        right = gap_x + self.gap_w + clearance
        if right + PLUG_WIDTH <= SCREEN_W:
            slots.append((right, SCREEN_W - PLUG_WIDTH))
        if not slots:
            return None
        low, high = self.rng.choice(slots)
        return self.rng.randint(low, high)
