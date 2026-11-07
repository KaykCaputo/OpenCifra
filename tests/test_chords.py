import unittest
from music import ChordBook, TUNINGS, chord_formula


class ChordGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.book = ChordBook()

    def test_notation_aliases(self):
        for a, b in [('C7M', 'Cmaj7'), ('C7/9', 'C9'), ('Cm7(b5)', 'Cø'),
                     ('C6/9', 'C69'), ('C7/4', 'C7sus4'), ('C°', 'Cdim')]:
            self.assertEqual(chord_formula(a), chord_formula(b), (a, b))
        self.assertNotIn(10, chord_formula('C6/9').tones)
        self.assertTrue({1, 3} <= chord_formula('C7(b9#9)').tones)

    def test_generated_voicings_across_roots_qualities_and_tunings(self):
        # 1,008 chord/tuning combinations: verify notes, bass and essential tones.
        for root in ('C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'):
            for suffix in ('', 'm', '7', 'maj7', 'm7', 'dim7', 'aug', 'sus2', 'sus4',
                           'm7b5', '7(b9)', '6/9', 'add9', '9'):
                chord = root + suffix
                formula = chord_formula(chord)
                for tuning, notes in TUNINGS.items():
                    with self.subTest(chord=chord, tuning=tuning):
                        positions = self.book.positions(chord, tuning)
                        self.assertTrue(positions)
                        for position in positions:
                            pitches = [n + f for n, f in zip(notes, position.frets) if f >= 0]
                            tones = {p % 12 for p in pitches}
                            self.assertTrue(tones <= formula.tones)
                            self.assertTrue(formula.essential <= tones)
                            self.assertEqual(min(pitches) % 12, formula.bass)
                            self.assertEqual(set(position.omitted), formula.tones - tones)

    def test_slash_bass_and_cache(self):
        for chord in ('C/E', 'G/B', 'D/F#', 'Bbmaj13(#11)', 'C7(b9#9)'):
            formula = chord_formula(chord)
            positions = self.book.positions(chord)
            self.assertTrue(positions, chord)
            for position in positions:
                pitches = [n + f for n, f in zip(TUNINGS['Standard'], position.frets) if f >= 0]
                self.assertEqual(min(pitches) % 12, formula.bass)
            self.assertIs(positions, self.book.positions(chord))

    def test_unknown_suffix_is_not_silently_changed(self):
        with self.assertRaises(ValueError):
            chord_formula('Cunknown')
        self.assertEqual(self.book.positions('Cunknown'), ())
