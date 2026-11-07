"""Guitar tunings, chord formulas and cached fretboard voicing generation."""
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
import json
from pathlib import Path
import re
from songbook import CHORD, FLATS

TUNINGS = {
    'Standard': (40, 45, 50, 55, 59, 64),
    'Drop D': (38, 45, 50, 55, 59, 64),
    'Half step down': (39, 44, 49, 54, 58, 63),
    'DADGAD': (38, 45, 50, 55, 57, 62),
    'Open G': (38, 43, 50, 55, 59, 62),
    'Open D': (38, 45, 50, 54, 57, 62),
}
NOTE_NAMES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
NATURAL = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def pitch_class(note):
    return (NATURAL[note[0]] + note[1:].count('#') - note[1:].count('b')) % 12


def note_name(midi):
    return NOTE_NAMES[midi % 12] + str(midi // 12 - 1)


@dataclass(frozen=True)
class Formula:
    root: int
    tones: frozenset
    essential: frozenset
    bass: int


def chord_formula(chord):
    """Parse common international and Brazilian symbols without guessing unknown suffixes."""
    chord = chord.replace('♯', '#').replace('♭', 'b').replace('−', '-').strip()
    match = CHORD.fullmatch(chord)
    if not match:
        raise ValueError('Unrecognized chord name')
    root_name, suffix, bass_name = match.groups()
    root = pitch_class(root_name)
    suffix = suffix.replace('Δ', 'maj').replace('ø', 'm7b5').replace('°', 'dim').replace('º', 'dim')
    suffix = re.sub(r'(7|9|11|13)M', r'maj\1', suffix)
    suffix = re.sub(r'^M', 'maj', suffix)
    suffix = suffix.replace('7+', 'maj7').replace('7/4', '7sus4')
    suffix = suffix.replace('6/9', '6add9')
    if suffix == '69':
        suffix = '6add9'
    suffix = re.sub(r'[(),/\s]', '', suffix)
    if suffix.startswith('-'):
        suffix = 'm' + suffix[1:]
    if suffix.startswith('+') and not suffix.startswith('+5'):
        suffix = 'aug' + suffix[1:]
    suffix = suffix.replace('+5', '#5').replace('-5', 'b5')
    suffix = re.sub(r'(5|9|11|13)\+', r'#\1', suffix)
    suffix = re.sub(r'(5|9|11|13)-', r'b\1', suffix)
    pattern = r'maj(?:13|11|9|7)?|dim(?:7)?|aug|sus[24]?|add[#b]?(?:13|11|9|[246])|(?:no|omit)[35]|[#b](?:13|11|9|[56])|alt|m|13|11|9|7|6|5|4|2'
    tokens = re.findall(pattern, suffix)
    if ''.join(tokens) != suffix:
        raise ValueError('Unrecognized chord suffix: ' + suffix)
    degrees = {1: 0, 3: 4, 5: 7}
    required = {3}
    extra_intervals = set()
    altered_degrees = set()
    major_seventh = any(t.startswith('maj') for t in tokens)
    for token in tokens:
        if token == 'm':
            degrees[3] = 3
        elif token.startswith('dim'):
            degrees.update({3: 3, 5: 6})
            required.add(5)
            if token == 'dim7':
                degrees[7] = 9
                required.add(7)
        elif token == 'aug':
            degrees[5] = 8
            required.add(5)
        elif token.startswith('sus'):
            degrees.pop(3, None)
            required.discard(3)
            degree = int(token[-1]) if token[-1].isdigit() else 4
            degrees[degree] = 2 if degree == 2 else 5
            required.add(degree)
        elif token == '5':
            degrees.pop(3, None)
            required.discard(3)
            required.add(5)
        elif token in ('2', '4', '6'):
            degree = int(token)
            degrees[degree] = {2: 2, 4: 5, 6: 9}[degree]
            required.add(degree)
        elif token.startswith(('no', 'omit')):
            degree = int(token[-1])
            degrees.pop(degree, None)
            required.discard(degree)
        elif token == 'alt':
            degrees.update({7: 10, 5: 6, 9: 1})
            required.update((7, 5, 9))
        elif token.startswith('add') or token[0] in '#b':
            value = token.removeprefix('add')
            accidental = -1 if value.startswith('b') else 1 if value.startswith('#') else 0
            degree = int(value.lstrip('#b'))
            interval = {2: 2, 4: 5, 5: 7, 6: 9, 9: 2, 11: 5, 13: 9}[degree] + accidental
            if accidental and degree in altered_degrees:
                extra_intervals.add(degrees[degree])
            if accidental:
                altered_degrees.add(degree)
            degrees[degree] = interval
            required.add(degree)
        else:
            number = token.removeprefix('maj')
            if not number:
                continue
            extension = int(number)
            degrees[7] = 11 if major_seventh else 10
            required.add(7)
            for degree, interval in ((9, 2), (11, 5), (13, 9)):
                if extension >= degree:
                    degrees[degree] = interval
            if extension >= 9:
                required.add(extension)
    bass = pitch_class(bass_name) if bass_name else root
    tones = frozenset((root + interval) % 12 for interval in (*degrees.values(), *extra_intervals)) | {bass}
    essential = frozenset((root + degrees[d]) % 12 for d in required if d in degrees) | {(root + i) % 12 for i in extra_intervals} | {bass}
    return Formula(root, frozenset(tones), frozenset(essential), bass)


@dataclass(frozen=True)
class Voicing:
    frets: tuple
    omitted: tuple = ()
    generated: bool = False


class ChordBook:
    def __init__(self):
        data = json.loads((Path(__file__).parent / 'guitar.json').read_text())['chords']
        self.catalog = {}
        for group in data.values():
            for entry in group:
                suffix = {'major': '', 'minor': 'm'}.get(entry['suffix'], entry['suffix'])
                try:
                    formula = chord_formula(entry['key'] + suffix)
                except ValueError:
                    continue
                positions = self.catalog.setdefault(formula, [])
                for pos in entry['positions']:
                    positions.append(tuple(f if f <= 0 else f + pos['baseFret'] - 1 for f in pos['frets']))

    @lru_cache(maxsize=2048)
    def positions(self, chord, tuning='Standard'):
        try:
            formula = chord_formula(chord)
        except ValueError:
            return ()
        notes = TUNINGS[tuning]
        candidates = []
        if tuning == 'Standard':
            for frets in self.catalog.get(formula, []):
                pitches = [n + f for n, f in zip(notes, frets) if f >= 0]
                tones = {p % 12 for p in pitches}
                if tones <= formula.tones and formula.essential <= tones and min(pitches) % 12 == formula.bass:
                    candidates.append(Voicing(frets, tuple(sorted(formula.tones - tones))))
        # Search 4-fret windows. Six strings, bounded choices, no remote lookup.
        for base in range(1, 14):
            choices = []
            for note in notes:
                choices.append([-1] + ([0] if note % 12 in formula.tones else []) +
                    [f for f in range(base, base + 4) if (note + f) % 12 in formula.tones])
            for frets in product(*choices):
                pitches = [n + f for n, f in zip(notes, frets) if f >= 0]
                if len(pitches) < min(3, len(formula.tones)) or min(pitches) % 12 != formula.bass:
                    continue
                tones = {p % 12 for p in pitches}
                if not formula.essential <= tones:
                    continue
                pressed = [f for f in frets if f > 0]
                if not pressed:
                    fingers = 0
                else:
                    lowest = min(pressed)
                    barre = [i for i, f in enumerate(frets) if f == lowest]
                    can_barre = len(barre) > 1 and all(f >= lowest or f == -1 for f in frets[min(barre):max(barre) + 1])
                    fingers = len(pressed) - (len(barre) - 1 if can_barre else 0)
                if fingers > 4:
                    continue
                omitted = tuple(sorted(formula.tones - tones))
                # Only omit nonessential tones (usually fifths / inner extensions).
                candidates.append(Voicing(tuple(frets), omitted, True))
            if len(candidates) > 80:
                break
        def score(v):
            pressed = [f for f in v.frets if f > 0]
            return (len(v.omitted) * 20 + max(pressed, default=0) +
                    (max(pressed) - min(pressed) if pressed else 0) * 2 +
                    v.frets.count(-1) * 1.5 + int(v.generated) * 8)
        unique = {}
        for candidate in sorted(candidates, key=score):
            unique.setdefault(candidate.frets, candidate)
        return tuple(list(unique.values())[:8])

    def voicing(self, chord, tuning='Standard'):
        positions = self.positions(chord, tuning)
        return list(positions[0].frets) if positions else None
