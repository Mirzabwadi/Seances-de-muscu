"""Energetic 120 BPM gym beat (kick, clap, hats, bass, a riser into every bar), royalty-free.

Usage: python3 gym_beat.py OUT.wav [SECONDS]   (default 6 s; one bar = 2 s)
"""
import sys
import wave

import numpy as np

SR = 44100
BPM = 120
BEAT = 60 / BPM
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
mix = np.zeros(N)


def place(sig, t, gain=1.0):
    i = int(t * SR)
    j = min(N, i + len(sig))
    mix[i:j] += sig[: j - i] * gain


def kick():
    t = np.arange(int(0.45 * SR)) / SR
    freq = 45 + 110 * np.exp(-t * 28)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    return np.tanh(2.2 * np.sin(phase) * np.exp(-t * 7))


def clap():
    t = np.arange(int(0.25 * SR)) / SR
    noise = rng.standard_normal(len(t))
    env = np.exp(-t * 22) + 0.6 * np.exp(-((t - 0.012) * 400) ** 2)
    # crude band-pass: difference of moving averages
    k1, k2 = np.ones(3) / 3, np.ones(12) / 12
    bp = np.convolve(noise, k1, "same") - np.convolve(noise, k2, "same")
    return bp * env * 2.2


def hat(open_=False):
    t = np.arange(int((0.18 if open_ else 0.05) * SR)) / SR
    noise = rng.standard_normal(len(t))
    hp = noise - np.convolve(noise, np.ones(4) / 4, "same")
    return hp * np.exp(-t * (14 if open_ else 70))


def bass(freq, length):
    t = np.arange(int(length * SR)) / SR
    env = np.minimum(1, t * 200) * np.exp(-t * 2.5)
    s = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)
    return np.tanh(1.5 * s) * env


def riser(length):
    t = np.arange(int(length * SR)) / SR
    noise = rng.standard_normal(len(t))
    hp = noise - np.convolve(noise, np.ones(6) / 6, "same")
    return hp * (t / length) ** 2


# A minor riff, one note per beat: A1, A1, C2, G1 ...
riff = [55.0, 55.0, 65.41, 49.0]
for b in range(int(DUR / BEAT)):
    t = b * BEAT
    place(kick(), t, 0.9)
    if b % 4 == 3:
        place(kick(), t + BEAT * 0.75, 0.6)
    if b % 2 == 1:
        place(clap(), t, 0.55)
    for k in range(4):
        place(hat(open_=(k == 2)), t + k * BEAT / 4, 0.18 if k % 2 else 0.12)
    place(bass(riff[b % 4], BEAT * 0.95), t, 0.45)

# risers into the scene changes at 2 s and 4 s
for change in np.arange(2.0, DUR, 2.0):
    place(riser(0.9), change - 0.9, 0.22)

# fade out over the last 0.3 s
fade = int(0.3 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)
mix /= np.max(np.abs(mix)) / 0.89

pcm = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
