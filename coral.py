"""
Draws the coastline as living reef: bright coral at the water's edge, fading to blue with distance.
Collisions never use this art; it only decides how a bank looks.
"""
import math
import random

import pygame

ART_OVERHANG = 8  # Coral fingers reach this far past the hit shape, so a graze near the tips is free
BAND_DEPTHS = (9, 30, 72, 145)  # Where each palette colour gives way to the next, measured from the tips
PIECES_PER_PX = 1 / 90  # Coral pieces per px of bank width, per chunk
NEAR_COAST = 110  # Pieces further from the coast than this are drawn faded by distance
DEPTH_BLUE = (32, 62, 104)
PIECE_VARIANTS = 3

_piece_cache = {}


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(color, factor):
    return tuple(max(0, min(255, int(channel * factor))) for channel in color)


def _ridge(world_y):
    """Spurs and grooves: the reef grows in fingers running out from the coast. Returns -1 to 1."""
    return (math.sin(world_y * 0.19) * 0.65 + math.sin(world_y * 0.47 + 1.3) * 0.35)


def _brain(rng):
    size = rng.randint(24, 36)
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    base = rng.choice([(196, 150, 96), (170, 170, 104), (186, 120, 110)])
    center = size // 2
    pygame.draw.circle(image, shade(base, 0.6), (center, center), center)
    pygame.draw.circle(image, base, (center - 1, center - 1), center - 2)
    # Winding grooves, the look that gives brain coral its name
    for row in range(5, size - 4, 5):
        phase = rng.uniform(0, 6)
        points = [(x, row + int(math.sin(x * 0.55 + phase) * 2)) for x in range(3, size - 3, 2)]
        pygame.draw.lines(image, shade(base, 0.68), False, points, 1)
    trim = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(trim, (255, 255, 255, 255), (center, center), center)
    image.blit(trim, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return image


def _branch(image, rng, color, x, y, angle, length, width):
    end_x = x + math.cos(angle) * length
    end_y = y + math.sin(angle) * length
    pygame.draw.line(image, color, (x, y), (end_x, end_y), width)
    if length > 5:
        for turn in (-0.5, 0.45):
            _branch(image, rng, color, end_x, end_y, angle + turn + rng.uniform(-0.2, 0.2),
                    length * rng.uniform(0.6, 0.78), max(1, width - 1))


def _staghorn(rng):
    image = pygame.Surface((40, 38), pygame.SRCALPHA)
    color = rng.choice([(226, 176, 120), (214, 138, 112), (196, 186, 136)])
    for spread in (-0.65, 0, 0.65):
        _branch(image, rng, shade(color, 0.65), 21, 37, -math.pi / 2 + spread, 11, 3)
    for spread in (-0.5, 0.1, 0.6):
        _branch(image, rng, color, 20, 37, -math.pi / 2 + spread, 11, 3)
    return image


def _table(rng):
    image = pygame.Surface((42, 26), pygame.SRCALPHA)
    color = rng.choice([(156, 136, 112), (132, 150, 122), (168, 122, 124)])
    pygame.draw.rect(image, shade(color, 0.5), (18, 12, 6, 13))
    pygame.draw.ellipse(image, shade(color, 0.65), (0, 5, 42, 13))
    pygame.draw.ellipse(image, color, (2, 3, 38, 11))
    for x in range(5, 38, 4):
        pygame.draw.line(image, shade(color, 1.2), (21, 8), (x, 4 + abs(x - 21) // 5), 1)
    return image


def _fan(rng):
    image = pygame.Surface((36, 36), pygame.SRCALPHA)
    color = rng.choice([(186, 84, 136), (138, 92, 176), (204, 92, 96)])
    for i in range(13):
        angle = -math.pi / 2 + (i - 6) * 0.2
        reach = rng.randint(24, 32)
        end = (18 + math.cos(angle) * reach, 35 + math.sin(angle) * reach)
        pygame.draw.line(image, color, (18, 35), end, 1)
        middle = (18 + math.cos(angle) * reach * 0.6, 35 + math.sin(angle) * reach * 0.6)
        pygame.draw.circle(image, shade(color, 1.2), middle, 1)
    return image


def _anemone(rng):
    image = pygame.Surface((26, 26), pygame.SRCALPHA)
    color = rng.choice([(236, 136, 150), (150, 214, 176), (236, 190, 110)])
    for i in range(16):
        angle = i * math.tau / 16
        end = (13 + math.cos(angle) * 11, 13 + math.sin(angle) * 11)
        pygame.draw.line(image, color, (13, 13), end, 2)
    pygame.draw.circle(image, shade(color, 0.55), (13, 13), 4)
    return image


PIECE_MAKERS = {'brain': _brain, 'staghorn': _staghorn, 'table': _table, 'fan': _fan, 'anemone': _anemone}


def _fade_to_depth(piece, amount):
    tinted = piece.copy()
    keep = int(255 * (1 - amount))
    tinted.fill((keep, keep, keep, 255), special_flags=pygame.BLEND_RGBA_MULT)
    add = tuple(int(c * amount) for c in DEPTH_BLUE) + (0,)
    tinted.fill(add, special_flags=pygame.BLEND_RGBA_ADD)
    return tinted


def _pieces(name):
    """Pre-drawn versions of a piece: drawing them fresh for every chunk would cost too much."""
    if name not in _piece_cache:
        rng = random.Random(name)
        drawn = [PIECE_MAKERS[name](rng) for _ in range(PIECE_VARIANTS)]
        _piece_cache[name] = [(piece, _fade_to_depth(piece, 0.55)) for piece in drawn]
    return _piece_cache[name]


def _edge_at(edges, y, chunk_h):
    """A bank's x position at row y, between the samples. edges run from the bottom row up."""
    spacing = chunk_h / (len(edges) - 1)
    position = (chunk_h - y) / spacing
    index = min(len(edges) - 2, int(position))
    return edges[index] + (edges[index + 1] - edges[index]) * (position - index)


def paint_reef(image, edges, is_left, x_offset, world_y, colors_from, colors_to, chunk_h):
    """Fill image with reef, row by row.

    Everything comes from world_y, so the fingers line up across chunk joins, and colours
    move from colors_from at the bottom to colors_to at the top, so zones melt into each other.
    """
    width = image.get_width()
    for y in range(chunk_h):
        blend = (chunk_h - 1 - y) / (chunk_h - 1)
        ridge = _ridge(world_y + chunk_h - y)
        light = 1 + ridge * 0.13
        colors = [shade(lerp_color(start, end, blend), light)
                  for start, end in zip(colors_from, colors_to)]
        tip = _edge_at(edges, y, chunk_h) - x_offset + (1 if is_left else -1) * (
            ART_OVERHANG * (0.55 + 0.45 * ridge))
        # Deepest colour first, then each nearer band painted over it
        depths = [None] + [BAND_DEPTHS[i] + ridge * (5 + i * 5) for i in range(3, -1, -1)]
        for color, depth in zip(reversed(colors), depths):
            if depth is None:
                start_x, end_x = (0, tip) if is_left else (tip, width)
            elif is_left:
                start_x, end_x = tip - depth, tip
            else:
                start_x, end_x = tip, tip + depth
            pygame.draw.line(image, color, (max(0, start_x), y), (min(width - 1, end_x), y))


def scatter_pieces(image, edges, is_left, x_offset, names, rng, chunk_h):
    """Grow coral on the bank. Pieces stay inside the chunk, because art cut at a join would show."""
    width = image.get_width() - ART_OVERHANG
    for _ in range(int(width * PIECES_PER_PX + rng.random())):
        piece, far_piece = rng.choice(_pieces(rng.choice(names)))
        w, h = piece.get_size()
        if h >= chunk_h - 2:
            continue
        y = rng.randint(1, chunk_h - h - 1)
        rows = [_edge_at(edges, row, chunk_h) - x_offset for row in (y, y + h // 2, y + h - 1)]
        if is_left:
            x_range = (0, int(min(rows)) - w)
        else:
            x_range = (int(max(rows)), image.get_width() - w)
        if x_range[0] > x_range[1]:
            continue
        # Most growth clusters by the water's edge, where a real reef is liveliest
        reach = min(int(rng.expovariate(1 / 45)), x_range[1] - x_range[0])
        x = x_range[1] - reach if is_left else x_range[0] + reach
        image.blit(far_piece if reach > NEAR_COAST else piece, (x, y))
