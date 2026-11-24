"""The high-score table: kept in a file, with arcade-style initials."""

import json
import string

import pygame

from resources import settings_path

SCORES_FILE = 'high_scores.json'
TABLE_SIZE = 10
NAME_LENGTH = 3
LETTERS = string.ascii_uppercase
TITLE_COLOR = (255, 225, 90)
ROW_COLOR = (225, 235, 240)
NEW_COLOR = (255, 90, 70)


class HighScores:
    """The best TABLE_SIZE runs, best first. A missing or damaged file is an empty table."""

    def __init__(self, filename=SCORES_FILE):
        self.path = settings_path(filename)
        self.entries = self._load()

    def _load(self):
        try:
            with open(self.path) as f:
                raw = json.load(f)
        except (OSError, ValueError):
            return []
        entries = []
        for item in raw if isinstance(raw, list) else []:
            try:
                entries.append({'name': str(item['name'])[:NAME_LENGTH].upper(),
                                'score': int(item['score']),
                                'difficulty': str(item.get('difficulty', 'normal'))})
            except (KeyError, TypeError, ValueError):
                continue  # Skip a damaged row, keep the rest
        entries.sort(key=lambda entry: -entry['score'])
        return entries[:TABLE_SIZE]

    def save(self):
        try:
            with open(self.path, 'w') as f:
                json.dump(self.entries, f, indent=2)
            return True
        except OSError as e:
            print(f"Warning: Could not save high scores: {e}")
            return False

    @property
    def best(self):
        return self.entries[0]['score'] if self.entries else 0

    def qualifies(self, score):
        """Whether this score earns a place in the table."""
        if score <= 0:
            return False
        return len(self.entries) < TABLE_SIZE or score > self.entries[-1]['score']

    def add(self, name, score, difficulty):
        """Put a run in the table and save it. Returns its place, from 0, or None if it didn't make it.

        A tie goes below the runs already there, as they got there first.
        """
        if not self.qualifies(score):
            return None
        place = sum(entry['score'] >= score for entry in self.entries)
        self.entries.insert(place, {'name': name[:NAME_LENGTH].upper(), 'score': score, 'difficulty': difficulty})
        del self.entries[TABLE_SIZE:]
        self.save()
        return place


class InitialsEntry:
    """Three letters, picked arcade-style or typed.

    Up and down change the letter, left and right move between letters, and fire or
    Enter moves on, finishing after the last letter. Backspace goes back one.
    """

    def __init__(self, keymap):
        self.keymap = keymap
        self.letters = ['A'] * NAME_LENGTH
        self.position = 0
        self.done = False

    @property
    def name(self):
        return ''.join(self.letters)

    def _turn(self, step):
        current = LETTERS.index(self.letters[self.position])
        self.letters[self.position] = LETTERS[(current + step) % len(LETTERS)]

    def _advance(self):
        if self.position == NAME_LENGTH - 1:
            self.done = True
        else:
            self.position += 1

    def handle(self, event):
        """Take one key, button or hat event. Returns True if it was used."""
        if self.done:
            return False
        if event.type == pygame.KEYDOWN:
            key = event.key
            typed = getattr(event, 'unicode', '').upper()
            if typed and typed in LETTERS and len(typed) == 1:
                self.letters[self.position] = typed
                self._advance()
            elif key in (pygame.K_UP, self.keymap.get('up')):
                self._turn(1)
            elif key in (pygame.K_DOWN, self.keymap.get('down')):
                self._turn(-1)
            elif key in (pygame.K_RIGHT, self.keymap.get('right')):
                self.position = min(NAME_LENGTH - 1, self.position + 1)
            elif key in (pygame.K_LEFT, self.keymap.get('left'), pygame.K_BACKSPACE):
                self.position = max(0, self.position - 1)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, self.keymap.get('fire')):
                self._advance()
            else:
                return False
            return True
        if event.type == pygame.JOYHATMOTION:
            x, y = event.value
            if y:
                self._turn(y)
            elif x:
                self.position = max(0, min(NAME_LENGTH - 1, self.position + x))
            return bool(x or y)
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 1:  # B on most pads goes back
                self.position = max(0, self.position - 1)
            else:
                self._advance()
            return True
        return False

    def draw(self, screen, font, center, now):
        """The letters, with the current one blinking under a cursor."""
        spacing = 46
        left = center[0] - spacing * (NAME_LENGTH - 1) / 2
        for i, letter in enumerate(self.letters):
            x = int(left + i * spacing)
            current = i == self.position and not self.done
            if current and now // 250 % 2:
                color = ROW_COLOR
            else:
                color = NEW_COLOR if current else TITLE_COLOR
            image = font.render(letter, True, color)
            screen.blit(image, image.get_rect(center=(x, center[1])))
            if current:
                pygame.draw.line(screen, NEW_COLOR, (x - 15, center[1] + 24), (x + 15, center[1] + 24), 3)


def draw_table(screen, font, scores, top, highlight=None, title="HIGH SCORES"):
    """The table, centred, starting at top. The highlight row (a place, from 0) is picked out."""
    heading = font.render(title, True, TITLE_COLOR)
    screen.blit(heading, heading.get_rect(midtop=(400, top)))
    y = top + heading.get_height() + 12
    if not scores.entries:
        empty = font.render("No scores yet. Be the first!", True, ROW_COLOR)
        screen.blit(empty, empty.get_rect(midtop=(400, y)))
        return
    for place, entry in enumerate(scores.entries):
        color = NEW_COLOR if place == highlight else ROW_COLOR
        cells = [(f"{place + 1}.", 250, 'right'), (entry['name'], 280, 'left'),
                 (str(entry['score']), 470, 'right'), (entry['difficulty'].upper(), 500, 'left')]
        for text, x, align in cells:
            image = font.render(text, True, color)
            rect = image.get_rect(topright=(x, y)) if align == 'right' else image.get_rect(topleft=(x, y))
            screen.blit(image, rect)
        y += font.get_linesize() + 2


def draw_table_over(screen, font, scores, top, highlight=None):
    """The table on a dark panel, for drawing over the moving title screen."""
    rows = max(1, len(scores.entries))
    height = font.get_height() + 12 + rows * (font.get_linesize() + 2) + 24
    rect = pygame.Rect(0, 0, 420, height)
    rect.midtop = (400, top - 12)
    backing = pygame.Surface(rect.size, pygame.SRCALPHA)
    backing.fill((0, 0, 0, 150))
    screen.blit(backing, rect)
    draw_table(screen, font, scores, top, highlight)
