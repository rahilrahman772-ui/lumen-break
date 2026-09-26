"""Reliable procedural audio for Lumen Break.

All effects and background music are generated in memory; no external audio files
are required. Audio failures are isolated so the game can still run.
"""
import io
import math
import random
import struct
import wave

import pygame


class Audio:
    SAMPLE_RATE = 44100

    def __init__(self, save):
        self.save = save
        self.enabled = False
        self.music = None
        self.music_channel = None
        self.sounds = {}

        try:
            # App normally calls pre_init() before pygame.init(). Keep this
            # fallback for running Audio independently.
            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=self.SAMPLE_RATE,
                    size=-16,
                    channels=2,
                    buffer=512,
                )
            pygame.mixer.set_num_channels(32)
            self.enabled = True
            self._build_sounds()
            self.music = self._make_music()
            self.music_channel = pygame.mixer.Channel(31)
            self.set_volume(self.save.get("volume") or 0.7)
            self.music_channel.play(self.music, loops=-1)
        except (pygame.error, OSError) as exc:
            # Keep the game playable, but print the real reason instead of
            # silently hiding an audio initialization problem.
            self.enabled = False
            print(f"[Audio] Disabled: {exc}")

    @staticmethod
    def _wav_bytes(samples, channels=1):
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav:
            wav.setnchannels(channels)
            wav.setsampwidth(2)
            wav.setframerate(Audio.SAMPLE_RATE)
            frames = b"".join(
                struct.pack("<h", max(-32768, min(32767, int(s))))
                for s in samples
            )
            wav.writeframes(frames)
        return buf.getvalue()

    @classmethod
    def _tone(cls, freq, duration, volume=0.25, slide=0.0, wave_type="sine"):
        n = max(1, int(cls.SAMPLE_RATE * duration))
        samples = []
        attack = max(1, int(cls.SAMPLE_RATE * 0.008))
        release = max(1, int(cls.SAMPLE_RATE * min(0.08, duration * 0.25)))

        for i in range(n):
            t = i / cls.SAMPLE_RATE
            f = max(1.0, freq + slide * (i / max(1, n - 1)))
            phase = 2 * math.pi * f * t

            if wave_type == "square":
                raw = 1.0 if math.sin(phase) >= 0 else -1.0
            elif wave_type == "triangle":
                raw = 2.0 * abs(2.0 * ((f * t) % 1.0) - 1.0) - 1.0
            else:
                raw = math.sin(phase)

            env = min(1.0, i / attack, (n - i) / release)
            samples.append(int(32767 * volume * raw * env))

        return cls._wav_bytes(samples)

    @classmethod
    def _noise_burst(cls, duration=0.08, volume=0.18):
        n = max(1, int(cls.SAMPLE_RATE * duration))
        samples = []
        for i in range(n):
            env = 1.0 - i / n
            samples.append(
                int(32767 * volume * random.uniform(-1, 1) * env)
            )
        return cls._wav_bytes(samples)

    @classmethod
    def _make_music(cls):
        # Short ambient stereo loop.
        notes = [110.0, 130.81, 146.83, 123.47, 110.0, 164.81, 146.83, 98.0]
        beat = 0.5
        stereo = []

        for root in notes:
            n = int(cls.SAMPLE_RATE * beat)
            for j in range(n):
                t = j / cls.SAMPLE_RATE
                env = min(1.0, j / 2500, (n - j) / 5000)
                bass = math.sin(2 * math.pi * root * t) * 0.10
                pad = math.sin(2 * math.pi * root * 2 * t) * 0.035
                shimmer = math.sin(2 * math.pi * root * 4 * t) * 0.012
                sample = (bass + pad + shimmer) * env
                stereo.extend((
                    int(32767 * sample),
                    int(32767 * sample * 0.92),
                ))

        return pygame.mixer.Sound(buffer=cls._wav_bytes(stereo, channels=2))

    def _build_sounds(self):
        definitions = {
            "click": self._tone(520, 0.055, 0.24, slide=180),
            "launch": self._tone(280, 0.12, 0.28, slide=360),
            "paddle": self._tone(190, 0.07, 0.26, slide=90),
            "brick": self._tone(620, 0.045, 0.22, slide=-100),
            "break": self._tone(760, 0.10, 0.30, slide=280),
            "powerup": self._tone(420, 0.18, 0.28, slide=520),
            "level": self._tone(330, 0.35, 0.28, slide=330),
            "life": self._noise_burst(0.16, 0.24),
            "gameover": self._tone(260, 0.45, 0.30, slide=-170),
        }
        self.sounds = {
            name: pygame.mixer.Sound(buffer=data)
            for name, data in definitions.items()
        }

    def set_volume(self, value):
        value = max(0.0, min(1.0, float(value)))
        self.save.set("volume", value)

        if not self.enabled:
            return

        # Effects and music are controlled separately.
        for sound in self.sounds.values():
            sound.set_volume(value)

        if self.music is not None:
            self.music.set_volume(value * 0.28)

    def play(self, name):
        if self.enabled:
            sound = self.sounds.get(name)
            if sound is not None:
                sound.play()

    def stop(self):
        if self.enabled and self.music_channel is not None:
            self.music_channel.stop()

    def shutdown(self):
        if self.enabled:
            pygame.mixer.stop()
            pygame.mixer.quit()
