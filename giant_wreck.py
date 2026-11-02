"""
A giant wreck lying across the channel. It can't be destroyed, like the coast. There's a safe way
round each side, or a gap straight through its broken hull, with loot and a mine inside.
"""
import random

import pygame

W, H = 290, 480
PASSAGE = (85, 205)  # Where the way through runs, across the wreck's width
MIN_GAP = 125  # Open water wanted on each side, well over the shark's 45 px
SIDE_ESCAPE = 75
SPAWN_EVERY_MS = 20000
_art = {}


def _walls():
    left = [(PASSAGE[0], 6), (42, 74), (10, 170), (4, 400), (30, 478), (PASSAGE[0], 478)]
    right = [(W - x, y) for x, y in left]
    return left, right


def _draw():
    if 'wreck' in _art:
        return _art['wreck']
    rng = random.Random(7)
    left, right = _walls()
    image = pygame.Surface((W, H), pygame.SRCALPHA)
    # The flooded insides, seen through the hole. Faint, and not part of the hit shape.
    floor = [(PASSAGE[0], 6), (PASSAGE[1], 6), (PASSAGE[1], 478), (PASSAGE[0], 478)]
    pygame.draw.polygon(image, (6, 12, 22, 95), floor)
    for y in range(26, H, 42):
        pygame.draw.line(image, (70, 56, 46, 110), (PASSAGE[0], y), (PASSAGE[1], y), 3)
    for wall in (left, right):
        pygame.draw.polygon(image, (84, 54, 42), wall)
        pygame.draw.lines(image, (14, 18, 26), True, wall, 3)
    hit = pygame.Surface((W, H), pygame.SRCALPHA)
    for wall in (left, right):
        pygame.draw.polygon(hit, (255, 255, 255), wall)
    mask = pygame.mask.from_surface(hit)
    # Planks, rust and weed, kept to the hull itself
    for y in range(40, H - 8, 14):
        for x in range(6, W - 6, 4):
            if mask.get_at((x, y)) and mask.get_at((x, y - 4)) and x % 8 == 2:
                image.set_at((x, y), (130, 92, 62))
                image.set_at((x + 1, y), (130, 92, 62))
    for _ in range(170):
        x, y = rng.randrange(W), rng.randrange(H)
        if mask.get_at((x, y)):
            color = rng.choice([(164, 86, 44), (140, 72, 40), (74, 122, 78), (96, 138, 86)])
            spot = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(spot, color, (5, 5), rng.randint(2, 4))
            image.blit(spot, (x - 5, y - 5))
    for wall_x in (44, W - 44):  # Gun decks and hatches
        for y in (150, 240, 330):
            pygame.draw.rect(image, (112, 116, 108), (wall_x - 18, y, 36, 44), border_radius=3)
            pygame.draw.rect(image, (28, 30, 38), (wall_x - 11, y + 8, 22, 14))
    for x, y in ((PASSAGE[0] - 4, 90), (PASSAGE[1] + 4, 90)):  # Warning lights mark the way in
        pygame.draw.circle(image, (255, 210, 90), (x, y), 4)
    _art['wreck'] = (image, mask)
    return _art['wreck']


class GiantWreck(pygame.sprite.Sprite):
    """Goes in with the coastline, so it blocks the shark and stops shots the same way."""

    def __init__(self, center_x):
        super().__init__()
        self.image, self.mask = _draw()
        self.rect = self.image.get_rect(midbottom=(center_x, 0))

    def escape_x(self, shark_x):
        """The nearest open water for a shark that has swum into the hull."""
        spots = (self.rect.left - SIDE_ESCAPE, self.rect.left + (PASSAGE[0] + PASSAGE[1]) // 2,
                 self.rect.right + SIDE_ESCAPE)
        return min(spots, key=lambda spot: abs(spot - shark_x))

    def passage_x(self):
        return self.rect.left + (PASSAGE[0] + PASSAGE[1]) // 2
