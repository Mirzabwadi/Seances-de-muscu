"""Soft "whoosh" for chapter transitions: filtered noise sweeping up then fading (0.7 s).

Usage: python3 whoosh.py OUT.wav
"""
import sys
import wave

import numpy as np

SR = 44100
n = int(0.7 * SR)
t = np.arange(n) / SR
rng = np.random.default_rng(11)
noise = rng.standard_normal(n)
out = np.zeros(n)
# Sweep a one-pole low-pass cutoff from 300 Hz to 6 kHz, so the noise "opens up".
y = 0.0
for i in range(n):
    fc = 300 * (20 ** (t[i] / 0.7))
    a = np.exp(-2 * np.pi * fc / SR)
    y = (1 - a) * noise[i] + a * y
    out[i] = y
env = np.sin(np.pi * np.minimum(1, t / 0.7)) ** 1.5
out = out * env
out = out / np.abs(out).max() * 0.8
stereo = np.stack([out, out * 0.9], 1)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((stereo * 32767).astype(np.int16).tobytes())
