"""
Reef passages: a river-like channel winding between two indestructible coastlines.
"""
import random

import pygame

from food import SmallFish

# --- Tuning: adjust these while playtesting ---
FIRST_PASSAGE_MS = 15000
PASSAGE_INTERVAL_MS = 25000
FUNNEL_LENGTH = 600  # px of scrolling for the banks to close in, and again to open out
CHANNEL_LENGTH = 1500  # px of scrolling at full channel width
WIDEST_CHANNEL = 160  # Narrowest point of the channel at score 0
NARROWEST_CHANNEL = 100  # Narrowest point of the channel at high scores
CHANNEL_NARROWS_PER_SCORE = 0.5
CHANNEL_WIDTH_VARIATION = 60  # How much wider than its narrowest point the channel can get
BEND_LENGTH = (240, 520)  # px of scrolling for one bend
WIDTH_CHANGE_LENGTH = (400, 800)
COAST_ROUGHNESS = 4  # px the coastline wanders from its smooth line
FISH_SPACING = 340
CLEAR_BONUS = 10
BANK_DAMAGE = 12
BANK_INVULN_MS = 1000
BANK_PUSH = 10  # px per step, faster than the shark can swim back
ROUTE_SAFETY = 0.8  # Share of the theoretical limits a bend may use

# --- Facts about the game that limit what's fair ---
SCREEN_W = 800
EDGE_MARGIN = 30
SCROLL_PER_STEP = 3
SHARK_SPEED = 5
SHARK_BODY_W = 45
SHARK_BODY_H = 104
SAMPLE_SPACING = 8
SAMPLES_PER_CHUNK = 6
CHUNK_H = SAMPLE_SPACING * SAMPLES_PER_CHUNK  # A multiple of the scroll speed, so chunks join exactly
FUNNEL_OPENING = 600  # Added to the half width at each end, which puts the banks off screen
SMOOTHSTEP_PEAK_SLOPE = 1.5
WIDTH_CHANGE_SLOPE = SMOOTHSTEP_PEAK_SLOPE * CHANNEL_WIDTH_VARIATION / 2 / WIDTH_CHANGE_LENGTH[0]
BONUS_AFTER_END = 500  # px from the top of the screen to the shark
SUB_CLEAR_MS = 6000  # Submarines scroll slower than the banks, so stop them before a passage


def max_bend_slope(channel_w):
    """Steepest fair bend, as px sideways per px scrolled.

    The shark never rotates, so on a diagonal its length takes up channel width.
    Part of the limit is reserved for the banks moving as the channel changes width.
    """
    room = channel_w - 2 * COAST_ROUGHNESS - SHARK_BODY_W
    fits = room / SHARK_BODY_H
    swimmable = SHARK_SPEED / SCROLL_PER_STEP
    return min(fits, swimmable) * ROUTE_SAFETY - WIDTH_CHANGE_SLOPE


def channel_width_for(score):
    return max(NARROWEST_CHANNEL, int(WIDEST_CHANNEL - score * CHANNEL_NARROWS_PER_SCORE))


def _smoothstep(t):
    return t * t * (3 - 2 * t)


def _waypoint_values(rng, count, length_range, next_value, first):
    """Sample a smooth path, one value per sample, between randomly spaced waypoints."""
    values = []
    value = first
    while len(values) < count:
        steps = max(1, int(rng.uniform(*length_range) / SAMPLE_SPACING))
        target = next_value(value, steps * SAMPLE_SPACING)
        values.extend(value + (target - value) * _smoothstep(i / steps) for i in range(steps))
        value = target
    return values[:count]


def _wander(rng, count):
    """Small smooth noise that makes a coastline look natural."""
    values, value = [], 0
    for _ in range(count):
        value = max(-COAST_ROUGHNESS, min(COAST_ROUGHNESS, value + rng.uniform(-2, 2)))
        values.append(value)
    return values


def generate_channel(rng, score):
    """Return the (left, right) bank positions, one pair per sample, in order of arrival."""
    channel_w = channel_width_for(score)
    widest = channel_w + CHANNEL_WIDTH_VARIATION
    count = (2 * FUNNEL_LENGTH + CHANNEL_LENGTH) // SAMPLE_SPACING
    lowest = EDGE_MARGIN + widest // 2
    highest = SCREEN_W - EDGE_MARGIN - widest // 2
    slope = max_bend_slope(channel_w)

    def next_center(center, length):
        shift = rng.uniform(0.5, 1.0) * slope * length / SMOOTHSTEP_PEAK_SLOPE
        if rng.random() < 0.5:
            shift = -shift
        if not lowest <= center + shift <= highest:
            shift = -shift  # Bounce off the screen edge
        return max(lowest, min(highest, center + shift))

    centers = _waypoint_values(rng, count, BEND_LENGTH, next_center, rng.uniform(lowest, highest))
    widths = _waypoint_values(rng, count, WIDTH_CHANGE_LENGTH,
                              lambda width, length: rng.uniform(channel_w, widest), widest)
    left_noise, right_noise = _wander(rng, count), _wander(rng, count)

    samples = []
    funnel_samples = FUNNEL_LENGTH // SAMPLE_SPACING
    for i in range(count):
        ends = min(i, count - 1 - i) / funnel_samples
        opening = FUNNEL_OPENING * (1 - _smoothstep(min(1, ends)))
        half = widths[i] / 2 + opening
        samples.append((int(centers[i] - half + left_noise[i]),
                        int(centers[i] + half + right_noise[i])))
    return samples


class CoastBank(pygame.sprite.Sprite):
    """A slice of indestructible coastline. Knows the channel's centre, to push the shark there."""

    def __init__(self, edges, is_left, channel_center, rng=random):
        """edges holds this bank's x position at each sample, from the chunk's bottom to its top."""
        super().__init__()
        y_at = [CHUNK_H - i * SAMPLE_SPACING for i in range(len(edges))]
        inner_most = max(edges) if is_left else min(edges)
        x_offset = 0 if is_left else inner_most
        width = inner_most if is_left else SCREEN_W - inner_most
        self.image = pygame.Surface((max(1, width), CHUNK_H), pygame.SRCALPHA)
        coast = [(edge - x_offset, y) for edge, y in zip(edges, y_at)]
        outer_x = 0 if is_left else width
        pygame.draw.polygon(self.image, (58, 62, 74),
                            coast + [(outer_x, y_at[-1]), (outer_x, y_at[0])])
        self.mask = pygame.mask.from_surface(self.image)
        self._add_detail(coast, is_left, rng)
        self.rect = self.image.get_rect(topleft=(x_offset, -CHUNK_H))
        self.channel_center = channel_center

    def _add_detail(self, coast, is_left, rng):
        inward = -1 if is_left else 1
        for _ in range(max(1, self.image.get_width() // 14)):
            x, y = rng.randint(0, self.image.get_width() - 1), rng.randint(4, CHUNK_H - 4)
            if self.mask.get_at((x, y)):
                pygame.draw.circle(self.image, rng.choice([(46, 50, 60), (72, 78, 90), (40, 42, 52)]),
                                   (x, y), rng.randint(2, 5))
        pygame.draw.lines(self.image, (34, 36, 46), False,
                          [(x + inward * 9, y) for x, y in coast], 6)
        pygame.draw.lines(self.image, (150, 132, 92), False, coast, 4)
        # Detail may spill past the coastline; collisions use the clean shape, so trim the drawing
        trim = self.mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        self.image.blit(trim, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)


class ChannelChunk:
    """One screen-wide slice of a passage."""

    def __init__(self, samples, has_fish=False, rng=random):
        self.samples = samples
        self.has_fish = has_fish
        self.rng = rng

    @property
    def channel_center(self):
        left, right = self.samples[len(self.samples) // 2]
        return (left + right) // 2

    def build(self):
        """Create this chunk's sprites, returned as (banks, foods)."""
        lefts = [left for left, _ in self.samples]
        rights = [right for _, right in self.samples]
        banks = []
        if max(lefts) > 0:
            banks.append(CoastBank(lefts, True, self.channel_center, self.rng))
        if min(rights) < SCREEN_W:
            banks.append(CoastBank(rights, False, self.channel_center, self.rng))
        foods = []
        if self.has_fish:
            foods.append(SmallFish(self.channel_center, -CHUNK_H // 2))
        return banks, foods


class ReefPassageDirector:
    """Decides when a passage runs and hands out its coastline a chunk at a time."""

    def __init__(self, rng=random):
        self.rng = rng
        self.wait_ms = FIRST_PASSAGE_MS
        self.samples = None
        self.next_sample = 0
        self.distance = 0
        self.scrolled = 0
        self.bonus_distance = None

    @property
    def active(self):
        return self.samples is not None

    @property
    def subs_allowed(self):
        return not self.active and self.wait_ms > SUB_CLEAR_MS

    def start(self, score=0):
        self.samples = generate_channel(self.rng, score)
        self.next_sample = 0
        self.distance = CHUNK_H
        self.scrolled = 0

    def update(self, dt, score):
        """Advance one step. Returns a new ChannelChunk when one is due."""
        if self.bonus_distance is not None:
            self.bonus_distance -= SCROLL_PER_STEP
        if not self.active:
            self.wait_ms -= dt
            if self.wait_ms > 0:
                return None
            self.start(score)
        self.distance += SCROLL_PER_STEP
        if self.distance < CHUNK_H:
            return None
        self.distance -= CHUNK_H
        if self.next_sample >= len(self.samples) - 1:
            self.samples = None
            self.wait_ms = PASSAGE_INTERVAL_MS
            self.bonus_distance = BONUS_AFTER_END
            return None
        first = self.next_sample
        self.next_sample = min(first + SAMPLES_PER_CHUNK, len(self.samples) - 1)
        self.scrolled += CHUNK_H
        funnel_clear = FUNNEL_LENGTH <= self.scrolled <= FUNNEL_LENGTH + CHANNEL_LENGTH
        return ChannelChunk(self.samples[first:self.next_sample + 1],
                            has_fish=funnel_clear and self.scrolled % FISH_SPACING < CHUNK_H,
                            rng=self.rng)

    def take_clear_bonus(self):
        """Score earned once the end of a passage has reached the shark, paid out once."""
        if self.bonus_distance is None or self.bonus_distance > 0:
            return 0
        self.bonus_distance = None
        return CLEAR_BONUS
