"""
The story's words: Dr. Rask's radio taunts, and the radio box that shows them.
"""
import random

import pygame

BOX = pygame.Rect(10, 462, 430, 84)
FADED_ALPHA = 90
REVEAL_MS_PER_CHAR = 24
HOLD_MS = 3200

AREA_TAUNTS = {
    "The Reef": "Subject 13 has escaped. Send the eel. And somebody find my coffee.",
    "The Ship Graveyard": "You swim among my failures, Subject 13. You are merely the latest.",
    "The Volcanic Rift": "Boiling water, fish! How do you like my security budget now?",
    "Atlantis": "Ten thousand years of guardians. I reprogrammed them in a weekend.",
    "The Sunken Lab": "You came home! Let me show you what I built to replace you.",
    "The Lab Core": "This is MY lab! I made you! Guards! GUARDS!",
    "The Flooded City": "I had the whole city flooded for the extra lab space. Worth it.",
    "The NASA Graveyard": "I bought all this at auction. The rockets, I mean. Not the astronauts.",
}
BOSS_TAUNTS = {
    "GIANT MORAY": "My eel has been very hungry, and you are very slow.",
    "GIANT SQUID": "Eight arms! Well, four. Budget cuts. Still plenty.",
    "MAGMA CRAB": "Try biting THAT, you overgrown goldfish.",
    "ATLANTEAN GUARDIAN": "I ask only that you hold still while it crushes you.",
    "RIVAL SHARK": "Subject 14: better laser, better manners. Goodbye, 13.",
    "DR. RASK": "Very well. I shall dissect you MYSELF.",
}
BEATEN_TAUNTS = {
    "GIANT MORAY": "That eel had a name! ...It was Kevin.",
    "GIANT SQUID": "Do you know how hard it is to get a squid that size through customs?",
    "MAGMA CRAB": "Fine. Fine! I have more crabs. Probably.",
    "ATLANTEAN GUARDIAN": "That was a priceless antique, you vandal!",
    "RIVAL SHARK": "No. No no no. Subject 14 was under warranty!",
}
GRUDGES = [
    "I gave you that laser. You could at least say thank you.",
    "Stop eating my test subjects!",
    "Is that all? I've seen sturdier sardines.",
    "Security, why is the shark still alive? I'm docking your pay.",
    "You're leaking, Subject 13. Do come in for repairs.",
]
GRUDGE_EVERY_MS = 24000


def _portrait():
    image = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.rect(image, (20, 50, 44), (0, 0, 64, 64), border_radius=6)
    pygame.draw.rect(image, (240, 240, 240), (14, 46, 36, 18))  # Lab coat
    pygame.draw.circle(image, (232, 196, 164), (32, 30), 15)
    for x, y in ((14, 18), (20, 11), (32, 8), (44, 11), (50, 18)):  # Wild hair
        pygame.draw.circle(image, (228, 228, 236), (x, y), 6)
    for x in (25, 39):  # Thick glasses, and the eyes of a person who sleeps badly
        pygame.draw.circle(image, (250, 250, 250), (x, 28), 6)
        pygame.draw.circle(image, (20, 20, 30), (x, 28), 6, 2)
        pygame.draw.circle(image, (20, 20, 30), (x, 28), 2)
    pygame.draw.line(image, (120, 40, 40), (25, 39), (39, 39), 3)
    return image


class Radio:
    """Dr. Rask, talking at you. One message at a time, typed out, in a box that fades over the shark."""

    def __init__(self, blip=None):
        self.font = pygame.font.SysFont(None, 23)
        self.title = pygame.font.SysFont(None, 19).render("DR. RASK  //  OPEN CHANNEL", True, (120, 255, 170))
        self.portrait = _portrait()
        self.box = pygame.Surface(BOX.size, pygame.SRCALPHA)
        self.blip = blip
        self.reset()

    def reset(self):
        self.queue = []
        self.message = None
        self.lines = []
        self.elapsed = 0
        self.grudge_timer = 0

    def say(self, text):
        if text and text not in self.queue and text != self.message:
            self.queue.append(text)

    def _wrap(self, text):
        lines, line = [], ''
        for word in text.split():
            attempt = f'{line} {word}'.strip()
            if self.font.size(attempt)[0] > BOX.width - 88:
                lines.append(line)
                line = word
            else:
                line = attempt
        return lines + [line]

    def update(self, dt, in_fight=False):
        if self.message:
            self.elapsed += dt
            if self.elapsed > len(self.message) * REVEAL_MS_PER_CHAR + HOLD_MS:
                self.message = None
        if not self.message and self.queue:
            self.message = self.queue.pop(0)
            self.lines = self._wrap(self.message)
            self.elapsed = 0
            if self.blip:
                self.blip.play()
        if not in_fight:
            self.grudge_timer += dt
            if self.grudge_timer > GRUDGE_EVERY_MS:
                self.grudge_timer = 0
                self.say(random.choice(GRUDGES))

    def draw(self, screen, shark_rect):
        if not self.message:
            return
        box = self.box
        box.fill((0, 0, 0, 0))
        pygame.draw.rect(box, (6, 20, 24, 205), box.get_rect(), border_radius=8)
        pygame.draw.rect(box, (90, 220, 150, 150), box.get_rect(), 1, border_radius=8)
        box.blit(self.portrait, (10, 10))
        box.blit(self.title, (84, 8))
        shown = int(self.elapsed / REVEAL_MS_PER_CHAR)
        y = 27
        for line in self.lines[:3]:
            if shown > 0:
                box.blit(self.font.render(line[:shown], True, (225, 240, 230)), (84, y))
            shown -= len(line) + 1
            y += 18
        box.set_alpha(FADED_ALPHA if BOX.colliderect(shark_rect) else None)
        screen.blit(box, BOX)
