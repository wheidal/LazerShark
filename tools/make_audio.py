"""
Writes the placeholder music and sound effects into sounds/. Swap any file for a real track of the
same name and the game plays that instead. Run from the project folder: python tools/make_audio.py
"""
import array
import math
import os
import random
import wave

RATE = 22050
PEAK = 0.55
NOTE = {n: i for i, n in enumerate('C C# D D# E F F# G G# A A# B'.split())}


def freq(name, octave):
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octave - 4) - 9) / 12)


def square(phase, duty=0.5):
    return 1.0 if phase % 1.0 < duty else -1.0


def saw(phase):
    return 2.0 * (phase % 1.0) - 1.0


def add_note(buffer, start, length, hz, volume, wave_fn, decay=3.0):
    begin = int(start * RATE)
    count = int(length * RATE)
    for i in range(min(count, len(buffer) - begin)):
        t = i / RATE
        buffer[begin + i] += wave_fn(hz * t) * volume * math.exp(-decay * t)


def add_noise(buffer, start, length, volume, rng, decay=30.0):
    begin = int(start * RATE)
    for i in range(min(int(length * RATE), len(buffer) - begin)):
        buffer[begin + i] += rng.uniform(-1, 1) * volume * math.exp(-decay * i / RATE)


def add_kick(buffer, start, volume):
    begin = int(start * RATE)
    phase = 0.0
    for i in range(min(int(0.16 * RATE), len(buffer) - begin)):
        t = i / RATE
        phase += (55 + 130 * math.exp(-30 * t)) / RATE
        buffer[begin + i] += math.sin(math.tau * phase) * volume * math.exp(-14 * t)


def save(path, buffer):
    loudest = max(1e-6, max(abs(x) for x in buffer))
    samples = array.array('h', (int(x / loudest * PEAK * 32767) for x in buffer))
    with wave.open(path, 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(samples.tobytes())


# Name: beats a minute, chords as (root, minor third?), octave, kick pattern, whether it drives hard
TRACKS = {
    'title': (108, [('A', 1), ('F', 0), ('C', 0), ('G', 0)], 3, 'k...k...', False),
    'reef': (96, [('D', 0), ('A', 1), ('G', 0), ('D', 0)], 3, 'k.......', False),
    'graveyard': (84, [('E', 1), ('C', 0), ('A', 1), ('B', 1)], 2, 'k.....k.', False),
    'rift': (118, [('C', 1), ('C', 1), ('G#', 0), ('G', 1)], 2, 'k..k..k.', True),
    'atlantis': (90, [('F', 0), ('D', 1), ('A#', 0), ('C', 0)], 3, 'k...k...', False),
    'lab': (128, [('F#', 1), ('D', 0), ('A', 0), ('E', 0)], 3, 'k.k.k.k.', True),
    'core': (138, [('D', 1), ('A#', 0), ('G', 1), ('A', 1)], 2, 'k.k.kk.k', True),
    'boss': (148, [('A', 1), ('A', 1), ('F', 0), ('E', 1)], 2, 'k.k.k.kk', True),
    'final_boss': (160, [('C#', 1), ('A', 0), ('F#', 1), ('G#', 1)], 2, 'kkk.kk.k', True),
    'victory': (120, [('C', 0), ('G', 0), ('A', 1), ('F', 0)], 3, 'k...k...', False),
}
SCALES = {True: [0, 3, 7], False: [0, 4, 7]}


def make_track(name, tempo, chords, octave, kicks, hard, bars=8):
    rng = random.Random(name)
    beat = 60.0 / tempo
    eighth = beat / 2
    buffer = [0.0] * int(bars * 4 * beat * RATE)
    for bar in range(bars):
        root, minor = chords[bar % len(chords)]
        steps = SCALES[bool(minor)]
        melody_seed = rng.randrange(1000)
        for step in range(8):
            start = (bar * 4 + step / 2) * beat
            base = freq(root, octave - 1) * 2 ** (steps[0] / 12)
            add_note(buffer, start, eighth, base, 0.32, saw if hard else square, 5.0)
            if kicks[step] == 'k':
                add_kick(buffer, start, 0.6)
            if hard and step % 2 == 1:
                add_noise(buffer, start, 0.08, 0.16, rng)
            elif step % 4 == 2:
                add_noise(buffer, start, 0.05, 0.08, rng)
            arp = steps[(step + melody_seed) % 3]
            add_note(buffer, start, eighth * 0.9, freq(root, octave + 1) * 2 ** (arp / 12), 0.13,
                     lambda p: square(p, 0.25), 7.0)
        for lead in range(4):
            if rng.random() < (0.8 if hard else 0.55):
                pick = rng.choice(steps + [12])
                add_note(buffer, (bar * 4 + lead) * beat, beat * 0.9,
                         freq(root, octave + 2) * 2 ** (pick / 12), 0.16, square, 3.0)
    return buffer


def sweep(length, start_hz, end_hz, volume=0.8, fn=saw, decay=2.0):
    buffer = [0.0] * int(length * RATE)
    phase = 0.0
    for i in range(len(buffer)):
        t = i / len(buffer)
        phase += (start_hz + (end_hz - start_hz) * t) / RATE
        buffer[i] = fn(phase) * volume * math.exp(-decay * t)
    return buffer


def mix(*layers):
    longest = max(len(layer) for layer in layers)
    return [sum(layer[i] for layer in layers if i < len(layer)) for i in range(longest)]


def noise(length, volume, decay, seed=1):
    rng = random.Random(seed)
    count = int(length * RATE)
    return [rng.uniform(-1, 1) * volume * math.exp(-decay * i / count) for i in range(count)]


def scream():
    buffer = []
    phase = 0.0
    for i in range(int(1.1 * RATE)):
        t = i / RATE
        phase += (720 + 180 * math.sin(t * 34) + 200 * t) / RATE
        buffer.append(saw(phase) * 0.7 * min(1, t * 12) * math.exp(-1.2 * t))
    return buffer


EFFECTS = {
    'boss_roar': lambda: mix(sweep(1.2, 120, 45, 0.9), noise(1.2, 0.25, 2)),
    'beam_zap': lambda: sweep(0.3, 1500, 300, 0.7, square, 3),
    'radio_blip': lambda: mix(sweep(0.06, 1400, 1400, 0.4, square, 1), noise(0.14, 0.12, 3)),
    'big_blast': lambda: mix(noise(1.3, 0.9, 4), sweep(1.3, 110, 30, 0.8)),
    'chomp': lambda: mix(noise(0.22, 0.9, 8), sweep(0.22, 240, 60, 0.8, square, 6)),
    'splat': lambda: mix(noise(0.3, 0.7, 6, 5), sweep(0.3, 180, 40, 0.5)),
    'scream': scream,
    'burp': lambda: sweep(0.7, 110, 70, 0.8, square, 1),
    'victory_sting': lambda: mix(*[[0.0] * int(i * 0.14 * RATE) + sweep(0.4, f, f, 0.5, square, 3)
                                   for i, f in enumerate((523, 659, 784, 1047))]),
}


def main():
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sounds')
    os.makedirs(os.path.join(root, 'music'), exist_ok=True)
    for name, spec in TRACKS.items():
        save(os.path.join(root, 'music', f'{name}.wav'), make_track(name, *spec))
    for name, make in EFFECTS.items():
        save(os.path.join(root, f'{name}.wav'), make())


if __name__ == '__main__':
    main()
