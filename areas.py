"""
The stretches of the journey. Beating a boss moves the run on to the next one.
An area overrides what the channel's zones would otherwise use, so the reef overrides nothing.
"""
AREAS = [
    {'name': "The Reef"},
    {'name': "The Ship Graveyard",
     'tint': (46, 26, 6, 45),
     'reef': [(150, 132, 104), (116, 76, 50), (82, 60, 52), (52, 54, 62), (28, 34, 50)],
     'decor': ['anchor', 'hull_plate', 'ribs', 'brain'],
     'obstacles': ['wreck', 'wreck', 'coral', 'mine', 'barrel', 'jellyfish', 'net', 'net', 'boulder'],
     'enemies': ['angler', 'barracuda', 'piranha', 'evil_sub'],
     'fields': ['ink', 'sludge'],
     'lagoon_width': (620, 700),  # Room for the giant wrecks and a way round them
     'giant_wrecks': True,
     'hint': "Go around the wrecks, or through for loot"},
    {'name': "The Volcanic Rift",
     'tint': (110, 30, 0, 45),
     'reef': [(240, 120, 44), (120, 48, 32), (68, 38, 38), (44, 32, 42), (22, 20, 34)],
     'decor': ['lava_rock', 'lava_crack', 'table'],
     'obstacles': ['mine', 'mine', 'wreck', 'barrel', 'emp_jelly', 'boulder', 'tumbling_rock', 'tumbling_rock'],
     'fields': ['sludge'],
     'enemies': ['tuna', 'tuna', 'manta', 'evil_sub'],
     'feature': 'geyser', 'feature_every_ms': 3000,
     'hint': "Glowing vents are about to erupt"},
    {'name': "Atlantis",
     'tint': (70, 60, 10, 35),
     'reef': [(232, 212, 140), (134, 134, 112), (90, 102, 112), (54, 76, 102), (26, 44, 76)],
     'decor': ['column', 'ruin', 'fan'],
     'obstacles': ['coral', 'mine', 'emp_jelly', 'jellyfish', 'barrel'],
     'enemies': ['statue', 'statue', 'puffer', 'manta', 'barracuda', 'piranha', 'evil_sub'],
     'fields': ['ink', 'magnet'],
     'hint': "The guardian statues are watching"},
    {'name': "The Sunken Lab",
     'tint': (0, 60, 50, 40),
     'reef': [(130, 200, 200), (74, 96, 112), (54, 66, 88), (36, 46, 70), (20, 26, 48)],
     'decor': ['pipe', 'tank', 'hull_plate'],
     'obstacles': ['barrel', 'barrel', 'mine', 'emp_jelly', 'emp_jelly'],
     'enemies': ['manta', 'manta', 'puffer', 'hammerhead', 'piranha', 'evil_sub'],
     'fields': ['sludge', 'magnet'],
     'feature': 'gate', 'feature_every_ms': 7000,
     'hint': "Shoot a gate's green switch to shut it down"},
    {'name': "The Lab Core",
     'tint': (70, 0, 20, 45),
     'reef': [(255, 90, 90), (96, 62, 78), (62, 50, 70), (40, 36, 58), (20, 18, 36)],
     'decor': ['tank', 'pipe', 'hull_plate'],
     'obstacles': ['mine', 'mine', 'barrel', 'emp_jelly'],
     'enemies': ['statue', 'manta', 'hammerhead', 'angler', 'barracuda', 'puffer', 'evil_sub'],
     'fields': ['ink', 'magnet', 'sludge'],
     'feature': 'gate', 'feature_every_ms': 5000,
     'hint': "He's in here somewhere"},
]

# Stretches partway to a boss, reached once a run is halfway there. Keyed by the boss being headed for.
INTERLUDES = {
    1: {'name': "The Flooded City",
        'tint': (20, 40, 56, 40),
        'reef': [(170, 174, 170), (112, 116, 120), (80, 86, 96), (52, 60, 74), (28, 36, 54)],
        'decor': ['windows', 'car', 'hull_plate'],
        'obstacles': ['tower', 'tower', 'net', 'barrel', 'mine', 'boulder'],
        'enemies': ['barracuda', 'puffer', 'hammerhead', 'piranha'],
        'fields': ['sludge', 'ink'],
        'hint': "Fallen buildings block the streets"},
    4: {'name': "The NASA Graveyard",
        'tint': (20, 20, 50, 45),
        'reef': [(200, 200, 215), (106, 106, 130), (70, 72, 100), (44, 48, 76), (20, 24, 50)],
        'decor': ['solar_panel', 'capsule', 'hull_plate'],
        'obstacles': ['rocket', 'rocket', 'satellite', 'satellite', 'mine', 'emp_jelly'],
        'enemies': ['manta', 'angler', 'hammerhead', 'evil_sub'],
        'fields': ['magnet', 'magnet', 'ink'],
        'hint': "Their junk is still up to no good"},
}
INTERLUDE_AT = 0.5


def area_for(bosses_beaten, progress=0):
    """progress is how far the score has come towards the next boss, from 0 to 1."""
    if INTERLUDE_AT <= progress < 1 and bosses_beaten in INTERLUDES:
        return INTERLUDES[bosses_beaten]
    return AREAS[min(bosses_beaten, len(AREAS) - 1)]
