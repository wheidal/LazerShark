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
     'obstacles': ['wreck', 'wreck', 'coral', 'mine', 'barrel', 'jellyfish'],
     'enemies': ['tuna', 'barracuda', 'piranha', 'evil_sub'],
     'lagoon_width': (620, 700),  # Room for the giant wrecks and a way round them
     'giant_wrecks': True,
     'hint': "Go around the wrecks, or through for loot"},
    {'name': "The Volcanic Rift",
     'tint': (110, 30, 0, 45),
     'reef': [(240, 120, 44), (120, 48, 32), (68, 38, 38), (44, 32, 42), (22, 20, 34)],
     'decor': ['lava_rock', 'lava_crack', 'table'],
     'obstacles': ['mine', 'mine', 'wreck', 'barrel', 'emp_jelly'],
     'enemies': ['tuna', 'tuna', 'manta', 'evil_sub'],
     'feature': 'geyser', 'feature_every_ms': 3000,
     'hint': "Glowing vents are about to erupt"},
    {'name': "Atlantis",
     'tint': (70, 60, 10, 35),
     'reef': [(232, 212, 140), (134, 134, 112), (90, 102, 112), (54, 76, 102), (26, 44, 76)],
     'decor': ['column', 'ruin', 'fan'],
     'obstacles': ['coral', 'mine', 'emp_jelly', 'jellyfish', 'barrel'],
     'enemies': ['statue', 'statue', 'tuna', 'manta', 'barracuda', 'piranha', 'evil_sub'],
     'hint': "The guardian statues are watching"},
    {'name': "The Sunken Lab",
     'tint': (0, 60, 50, 40),
     'reef': [(130, 200, 200), (74, 96, 112), (54, 66, 88), (36, 46, 70), (20, 26, 48)],
     'decor': ['pipe', 'tank', 'hull_plate'],
     'obstacles': ['barrel', 'barrel', 'mine', 'emp_jelly', 'emp_jelly'],
     'enemies': ['manta', 'manta', 'tuna', 'piranha', 'evil_sub'],
     'feature': 'gate', 'feature_every_ms': 7000,
     'hint': "Shoot a gate's green switch to shut it down"},
    {'name': "The Lab Core",
     'tint': (70, 0, 20, 45),
     'reef': [(255, 90, 90), (96, 62, 78), (62, 50, 70), (40, 36, 58), (20, 18, 36)],
     'decor': ['tank', 'pipe', 'hull_plate'],
     'obstacles': ['mine', 'mine', 'barrel', 'emp_jelly'],
     'enemies': ['statue', 'manta', 'tuna', 'barracuda', 'piranha', 'evil_sub'],
     'feature': 'gate', 'feature_every_ms': 5000,
     'hint': "He's in here somewhere"},
]


def area_for(bosses_beaten):
    return AREAS[min(bosses_beaten, len(AREAS) - 1)]
