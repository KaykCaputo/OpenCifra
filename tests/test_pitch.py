import math
import unittest
import numpy as np
from opentuna.pitch import detect_pitch


class PitchTests(unittest.TestCase):
    def test_guitar_range_and_cents(self):
        t = np.arange(4096) / 44100
        for frequency in (73.416, 82.407, 110, 146.832, 195.998, 246.942, 329.628, 440, 880):
            with self.subTest(frequency=frequency):
                signal = .4 * np.sin(2 * np.pi * frequency * t)
                detected = detect_pitch(signal)
                self.assertGreater(detected, 0)
                self.assertLess(abs(1200 * math.log2(detected / frequency)), 3)

    def test_harmonics_and_noise(self):
        rng = np.random.default_rng(4)
        t = np.arange(4096) / 44100
        for frequency in (82.407, 110, 196, 329.628):
            signal = .2 * np.sin(2 * np.pi * frequency * t) + .35 * np.sin(4 * np.pi * frequency * t)
            signal += rng.normal(0, .004, len(t))
            detected = detect_pitch(signal)
            self.assertGreater(detected, 0)
            self.assertLess(abs(1200 * math.log2(detected / frequency)), 5)

    def test_silence_noise_and_invalid_input(self):
        for signal in (np.zeros(4096), np.ones(4096), np.full(4096, np.nan), np.ones(10), np.random.default_rng(2).normal(0, .2, 4096)):
            self.assertEqual(detect_pitch(signal), 0)
