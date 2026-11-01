"""Opening "boom" for title cards: a low pitched-down hit, a breath of air and a soft shimmer (3 s).

Usage: python3 intro_boom.py OUT.wav
"""
import sys
import wave

import numpy as np

SR = 44100
t = np.arange(int(3.0 * SR)) / SR
rng = np.random.default_rng(3)
f = 38 + 60 * np.exp(-t * 6)
boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
noise = rng.standard_normal(len(t))
air = (noise - np.convolve(noise, np.ones(8) / 8, "same")) * np.exp(-t * 2.5) * 0.15
shimmer = sum(np.sin(2 * np.pi * fr * t) * np.exp(-t * 1.2) for fr in (880, 1318.5, 1760)) * 0.05 * np.minimum(1, t * 20)
s = np.tanh(1.4 * boom) + air + shimmer
s = s / np.abs(s).max() * 0.9
stereo = np.stack([s, s], 1)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((stereo * 32767).astype(np.int16).tobytes())
