"""OpenTuna audio backend, adapted from ../open-tuna (MIT, Kayk Caputo).

Single-slot capture queue, FFT pitch detection, and explicit microphone lifecycle.
"""
import importlib
import logging
from collections import deque
import queue
import threading

import numpy as np
from kivy.clock import Clock
from kivy.utils import platform
from .pitch import detect_pitch


class AudioEngine:
    def __init__(self, sample_rate=44100, min_detect_freq=60, max_detect_freq=1200, noise_gate=.008):
        self.sample_rate = sample_rate
        self.min_detect_freq, self.max_detect_freq = min_detect_freq, max_detect_freq
        self.noise_gate = noise_gate
        self.audio_enabled = False
        self.current_freq = 0.
        self.stream = None
        self._record = None
        self._thread = None
        self._stop = threading.Event()
        self._queue = queue.Queue(maxsize=1)
        self._frequencies = deque(maxlen=3)
        self._misses = 0
        self._generation = 0

    def _post_status(self, callback, message, generation):
        Clock.schedule_once(lambda dt: callback(message) if generation == self._generation else None)

    def request_permission_and_start(self, on_status):
        self._generation += 1
        generation = self._generation
        if platform != 'android':
            self.start(on_status)
            return
        try:
            permissions = importlib.import_module('android.permissions')
            permission = permissions.Permission.RECORD_AUDIO
            if permissions.check_permission(permission):
                self.start(on_status)
            else:
                def granted(names, grants):
                    def resume(dt):
                        if generation != self._generation:
                            return
                        if grants and all(grants):
                            self.start(on_status)
                        else:
                            on_status('Microphone permission denied. You can try again.')
                    Clock.schedule_once(resume)
                permissions.request_permissions([permission], granted)
        except Exception:
            logging.exception('Microphone permission check failed')
            self._post_status(on_status, 'Could not request microphone permission.', generation)

    def start(self, on_status):
        if self.audio_enabled:
            return
        if self._thread and self._thread.is_alive():
            self._post_status(on_status, 'Microphone is stopping. Try again.', self._generation)
            return
        self._stop.clear()
        self._frequencies.clear()
        self._misses = 0
        self._queue = queue.Queue(maxsize=1)
        generation = self._generation
        try:
            if platform == 'android':
                from jnius import autoclass
                AudioRecord = autoclass('android.media.AudioRecord')
                AudioFormat = autoclass('android.media.AudioFormat')
                channel, encoding = AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT
                minimum = AudioRecord.getMinBufferSize(self.sample_rate, channel, encoding)
                if minimum <= 0:
                    raise RuntimeError('Unsupported microphone sample rate')
                self._record = AudioRecord(1, self.sample_rate, channel, encoding, max(minimum, 16384))
                if self._record.getState() != AudioRecord.STATE_INITIALIZED:
                    raise RuntimeError('Microphone could not initialize')
                self._record.startRecording()
                target = lambda: self._android_loop(on_status, generation)
            else:
                sounddevice = importlib.import_module('sounddevice')
                self.stream = sounddevice.InputStream(channels=1, samplerate=self.sample_rate,
                    blocksize=4096, dtype='float32', callback=self.audio_callback)
                self.stream.start()
                target = lambda: self._desktop_loop(on_status, generation)
            self.audio_enabled = True
            self._thread = threading.Thread(target=target, daemon=True, name='opentuna-audio')
            self._thread.start()
            self._post_status(on_status, 'Listening locally. Pluck one string.', generation)
        except Exception:
            logging.exception('Microphone startup failed')
            self.stop()
            self._post_status(on_status, 'Microphone unavailable. Check your input device and audio dependencies.', self._generation)

    def detect_frequency_autocorr(self, data):
        # Compatibility entry point for the original OpenTuna engine.
        return detect_pitch(data, self.sample_rate, self.min_detect_freq, self.max_detect_freq, self.noise_gate)

    def _process(self, samples):
        frequency = self.detect_frequency_autocorr(samples)
        if frequency > 0:
            self._misses = 0
            if self._frequencies and abs(12 * np.log2(frequency / self._frequencies[-1])) > .7:
                self._frequencies.clear()
            self._frequencies.append(frequency)
            self.current_freq = float(np.median(self._frequencies))
        else:
            self._misses += 1
            if self._misses >= 3:
                self.current_freq = 0.
                self._frequencies.clear()

    def audio_callback(self, indata, frames, time, status):
        if self._stop.is_set():
            return
        try:
            self._queue.put_nowait(indata[:, 0].copy())
        except queue.Full:
            pass

    def _desktop_loop(self, callback, generation):
        try:
            while not self._stop.is_set():
                try:
                    self._process(self._queue.get(timeout=.2))
                except queue.Empty:
                    self.current_freq = 0.
        except Exception:
            logging.exception('Audio processing failed')
            self.stop()
            self._post_status(callback, 'Audio processing stopped. Try restarting the microphone.', self._generation)
        finally:
            self.current_freq = 0.

    def _android_loop(self, callback, generation):
        record = self._record
        try:
            # short[] read provides signed PCM samples (not ambiguous byte buffers).
            raw = [0] * 4096
            while not self._stop.is_set():
                count = int(record.read(raw, 0, len(raw)))
                if count <= 0:
                    if self._stop.is_set():
                        break
                    raise RuntimeError('Microphone read failed')
                self._process(np.asarray(raw[:count], dtype=np.float32) / 32768.)
        except Exception:
            logging.exception('Android audio capture failed')
            self.audio_enabled = False
            self._post_status(callback, 'Microphone stopped. Try again.', generation)
        finally:
            record.release()
            if self._record is record:
                self._record = None
            self.current_freq = 0.
            from jnius import detach
            detach()

    def stop(self):
        self._generation += 1
        self._stop.set()
        self.audio_enabled = False
        self.current_freq = 0.
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                logging.exception('Audio stream cleanup failed')
            self.stream = None
        if self._record:
            try:
                self._record.stop()
                if not self._thread or not self._thread.is_alive():
                    self._record.release()
                    self._record = None
            except Exception:
                logging.exception('Android microphone cleanup failed')
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=.5)
