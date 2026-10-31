"""
The channel: the whole game is a route winding between two indestructible coastlines.
Add a new environment by adding an entry to ZONES.
"""
import random

import pygame

# --- Tuning: adjust these while playtesting ---
ZONES = {
    'lagoon': {'width': (450, 550), 'length': (1500, 2500), 'bend': (400, 800),
               'next': ['pass'], 'bank_color': (112, 98, 74)},
    'pass': {'width': (220, 280), 'length': (900, 1600), 'bend': (240, 520),
             'next': ['lagoon', 'dropoff'], 'bank_color': (58, 62, 74)},
    'dropoff': {'width': (560, 620), 'length': (1000, 1800), 'bend': (400, 800),
                'next': ['pass'], 'bank_color': (30, 40, 62), 'open_side': True},
}
NARROWEST_PASS = 180  # Reached at high scores
PASS_NARROWS_PER_SCORE = 0.2
OBSTACLE_PASS_ROOM = 110  # Open width needed on one side of an obstacle, bends included
COAST_ROUGHNESS = 4  # px the coastline wanders from its smooth line
BANK_DAMAGE = 12
BANK_INVULN_MS = 1000
BANK_PUSH = 10  # px per step, faster than the shark can swim back
ROUTE_SAFETY = 0.8  # Share of the theoretical limits a bend may use

# --- Facts about the game that limit what's fair ---
SCREEN_W = 800
SCREEN_H = 600
EDGE_MARGIN = 30
OPEN_SIDE_OVERHANG = (40, 80)  # How far an open side's bank sits off screen
SPAWN_PADDING = 16
SPAWN_SAMPLES_BELOW = 8  # Coast samples a spawned sprite can overlap: tall obstacles reach below the top
SPAWN_SAMPLES_ABOVE = 3  # Sprites start slightly above the top of the screen
SCROLL_PER_STEP = 3
SHARK_SPEED = 5
SHARK_BODY_W = 45
SHARK_BODY_H = 104
SAMPLE_SPACING = 8
SAMPLES_PER_CHUNK = 6
CHUNK_H = SAMPLE_SPACING * SAMPLES_PER_CHUNK  # A multiple of the scroll speed, so chunks join exactly
SMOOTHSTEP_PEAK_SLOPE = 1.5


def max_bend_slope(channel_w):
    """Steepest fair coastline, as px sideways per px scrolled.

    The shark never rotates, so on a diagonal its length takes up channel width.
    """
    room = channel_w - 2 * COAST_ROUGHNESS - SHARK_BODY_W
    fits = room / SHARK_BODY_H
    swimmable = SHARK_SPEED / SCROLL_PER_STEP
    return min(fits, swimmable) * ROUTE_SAFETY


def _smoothstep(t):
    return t * t * (3 - 2 * t)


class ChannelGenerator:
    """Produces the coastline forever, one (left, right, zone) sample at a time."""

    def __init__(self, rng=random):
        self.rng = rng
        self.zone = 'lagoon'
        self.zone_left = self._zone_length()
        self.center = SCREEN_W / 2
        self.width = ZONES['lagoon']['width'][1]
        self.open_side = 0
        self.left_noise = 0
        self.right_noise = 0
        self.pending = []

    def _zone_length(self):
        return self.rng.uniform(*ZONES[self.zone]['length'])

    def _width_range(self, score):
        low, high = ZONES[self.zone]['width']
        if self.zone == 'pass':
            narrowing = score * PASS_NARROWS_PER_SCORE
            low = max(NARROWEST_PASS, low - narrowing)
            high = low + (ZONES['pass']['width'][1] - ZONES['pass']['width'][0])
        return low, high

    def _next_zone(self):
        self.zone = self.rng.choice(ZONES[self.zone]['next'])
        self.zone_left = self._zone_length()
        self.open_side = self.rng.choice([-1, 1]) if ZONES[self.zone].get('open_side') else 0

    def _center_for(self, width):
        if self.open_side:
            near_edge = width / 2 - self.rng.uniform(*OPEN_SIDE_OVERHANG)
            return near_edge if self.open_side < 0 else SCREEN_W - near_edge
        low = EDGE_MARGIN + width / 2
        return self.rng.uniform(low, SCREEN_W - low)

    def _add_bend(self, score):
        if self.zone_left <= 0:
            self._next_zone()
        width = self.rng.uniform(*self._width_range(score))
        center = self._center_for(width)
        # Both changes move the banks at once, so the bend takes as long as fairness needs
        movement = abs(center - self.center) + abs(width - self.width) / 2
        needed = SMOOTHSTEP_PEAK_SLOPE * movement / max_bend_slope(min(width, self.width))
        length = max(self.rng.uniform(*ZONES[self.zone]['bend']), needed)
        steps = max(1, int(length / SAMPLE_SPACING) + 1)
        for i in range(steps):
            t = _smoothstep(i / steps)
            mid = self.center + (center - self.center) * t
            half = (self.width + (width - self.width) * t) / 2
            self.left_noise = self._wander(self.left_noise)
            self.right_noise = self._wander(self.right_noise)
            self.pending.append((int(mid - half + self.left_noise),
                                 int(mid + half + self.right_noise), self.zone))
        self.center, self.width = center, width
        self.zone_left -= length

    def _wander(self, value):
        return max(-COAST_ROUGHNESS, min(COAST_ROUGHNESS, value + self.rng.uniform(-2, 2)))

    def take(self, count, score):
        """Return the next count samples, in order of arrival."""
        while len(self.pending) < count:
            self._add_bend(score)
        samples = self.pending[:count]
        del self.pending[:count]
        return samples

    def peek(self, count, score):
        """Look at the next count samples without using them up."""
        while len(self.pending) < count:
            self._add_bend(score)
        return self.pending[:count]


class CoastBank(pygame.sprite.Sprite):
    """A slice of indestructible coastline. Knows the channel's centre, to push the shark there."""

    def __init__(self, edges, is_left, channel_center, zone, y, rng=random):
        """edges holds this bank's x position at each sample, from the chunk's bottom to its top."""
        super().__init__()
        y_at = [CHUNK_H - i * SAMPLE_SPACING for i in range(len(edges))]
        inner_most = max(edges) if is_left else min(edges)
        x_offset = 0 if is_left else inner_most
        width = inner_most if is_left else SCREEN_W - inner_most
        self.image = pygame.Surface((max(1, width), CHUNK_H), pygame.SRCALPHA)
        coast = [(edge - x_offset, y_pos) for edge, y_pos in zip(edges, y_at)]
        outer_x = 0 if is_left else width
        pygame.draw.polygon(self.image, ZONES[zone]['bank_color'],
                            coast + [(outer_x, y_at[-1]), (outer_x, y_at[0])])
        self.mask = pygame.mask.from_surface(self.image)
        self._add_detail(coast, is_left, rng)
        self.rect = self.image.get_rect(topleft=(x_offset, y))
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
    """One screen-wide slice of the channel."""

    def __init__(self, samples, rng=random):
        self.samples = samples
        self.rng = rng

    @property
    def zone(self):
        return self.samples[len(self.samples) // 2][2]

    @property
    def channel_center(self):
        left, right, _ = self.samples[len(self.samples) // 2]
        return (left + right) // 2

    def build(self, y=-CHUNK_H):
        """Create this chunk's banks at the given screen position."""
        lefts = [left for left, _, _ in self.samples]
        rights = [right for _, right, _ in self.samples]
        banks = []
        if max(lefts) > 0:
            banks.append(CoastBank(lefts, True, self.channel_center, self.zone, y, self.rng))
        if min(rights) < SCREEN_W:
            banks.append(CoastBank(rights, False, self.channel_center, self.zone, y, self.rng))
        return banks


class ChannelDirector:
    """Hands out the coastline a chunk at a time and finds safe places to spawn things."""

    def __init__(self, rng=random):
        self.rng = rng
        self.generator = ChannelGenerator(rng)
        self.distance = 0
        self.last_sample = None
        self.recent = []
        self.score = 0

    @property
    def zone(self):
        return self.last_sample[2]

    def _next_chunk(self, score):
        samples = ([self.last_sample] if self.last_sample else
                   self.generator.take(1, score)) + self.generator.take(SAMPLES_PER_CHUNK, score)
        self.last_sample = samples[-1]
        self.score = score
        self.recent = (self.recent + samples[1:])[-SPAWN_SAMPLES_BELOW:]
        return ChannelChunk(samples, self.rng)

    def prefill(self):
        """Return (chunk, y) pairs covering the screen at the start of a run."""
        # The top chunk matches one that has just spawned and scrolled for its first step
        top = -CHUNK_H + SCROLL_PER_STEP
        rows = (SCREEN_H - top) // CHUNK_H + 1
        return [(self._next_chunk(0), top + CHUNK_H * (rows - 1 - i)) for i in range(rows)]

    def update(self, score):
        """Advance one step. Returns a new ChannelChunk when one is due."""
        self.distance += SCROLL_PER_STEP
        if self.distance < CHUNK_H:
            return None
        self.distance -= CHUNK_H
        return self._next_chunk(score)

    def spawn_x(self, width, blocking=False):
        """Pick an x inside the channel at the top of the screen.

        A blocking sprite always leaves one side wide enough to swim past, or returns None
        if it can't. Anything else always gets a position, however sharp the bend.
        """
        window = self.recent + self.generator.peek(SPAWN_SAMPLES_ABOVE, self.score)
        left = max(0, max(sample[0] for sample in window))
        right = min(SCREEN_W, min(sample[1] for sample in window))
        low = left + width // 2 + SPAWN_PADDING
        high = right - width // 2 - SPAWN_PADDING
        if blocking:
            free = right - left - width
            if free < OBSTACLE_PASS_ROOM + SPAWN_PADDING:
                return None
            if free < 2 * OBSTACLE_PASS_ROOM:  # Too tight for the middle: stay near one bank
                if self.rng.random() < 0.5:
                    high = right - width // 2 - OBSTACLE_PASS_ROOM
                else:
                    low = left + width // 2 + OBSTACLE_PASS_ROOM
        if low <= high:
            return self.rng.randint(low, high)
        return None if blocking else (self.last_sample[0] + self.last_sample[1]) // 2
