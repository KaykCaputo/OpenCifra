import unittest
from unittest.mock import Mock, patch
import numpy as np
from opentuna.audio_engine import AudioEngine


class AudioTests(unittest.TestCase):
    def test_silence_clears_old_pitch_without_detuning_it(self):
        engine = AudioEngine()
        signal = .3 * np.sin(2 * np.pi * 110 * np.arange(4096) / 44100)
        engine._process(signal)
        self.assertAlmostEqual(engine.current_freq, 110, delta=.1)
        before = engine.current_freq
        engine._process(np.zeros(4096))
        self.assertEqual(engine.current_freq, before)
        engine._process(np.zeros(4096))
        engine._process(np.zeros(4096))
        self.assertEqual(engine.current_freq, 0)

    def test_permission_callback_cannot_restart_after_stop(self):
        engine = AudioEngine()
        permissions = Mock()
        permissions.check_permission.return_value = False
        with patch('opentuna.audio_engine.platform', 'android'), patch(
            'opentuna.audio_engine.importlib.import_module', return_value=permissions), patch(
            'opentuna.audio_engine.Clock.schedule_once', side_effect=lambda fn, *args: fn(0)), patch.object(engine, 'start') as start:
            engine.request_permission_and_start(Mock())
            callback = permissions.request_permissions.call_args.args[1]
            engine.stop()
            callback(['microphone'], [True])
            start.assert_not_called()

    def test_stream_closes_and_worker_exits(self):
        engine = AudioEngine()
        backend = Mock()
        with patch('opentuna.audio_engine.platform', 'linux'), patch(
            'opentuna.audio_engine.importlib.import_module', return_value=backend), patch.object(engine, '_post_status'):
            engine.request_permission_and_start(Mock())
            self.assertTrue(engine.audio_enabled)
            engine.stop()
            self.assertFalse(engine.audio_enabled)
            self.assertFalse(engine._thread.is_alive())
            backend.InputStream.return_value.close.assert_called_once()
