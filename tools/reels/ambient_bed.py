"""Soft ambient music bed (Am - F - C - G pads, gentle pluck), stereo, royalty-free.

Usage: python3 ambient_bed.py OUT.wav [SECONDS]   (default 60 s)
Then normalise: ffmpeg -i OUT.wav -af loudnorm=I=-16:TP=-2 -c:a libmp3lame -b:a 192k music.mp3
"""
import sys
import wave

import numpy as np

SR = 44100
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
N = int(SR * DUR)
BAR = 4.0  # seconds per chord
t_all = np.arange(N) / SR
left = np.zeros(N)
right = np.zeros(N)

def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)

# A minor, F, C, G (voiced around middle register)
chords = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 55, 60, 64], [55, 59, 62, 67]]
roots = [45, 41, 48, 43]

def pad_note(freq, length, detune):
    t = np.arange(int(length * SR)) / SR
    env = np.minimum(1, t / 1.2) * np.minimum(1, (length - t) / 1.5)
    s = sum(np.sin(2 * np.pi * freq * (1 + d) * t + p) for d, p in ((0, 0), (detune, 1.3), (-detune, 2.1)))
    s += 0.25 * np.sin(2 * np.pi * freq * 2 * t)
    return s * env / 3.5

def pluck(freq, length=1.6):
    t = np.arange(int(length * SR)) / SR
    return (np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)) * np.exp(-t * 3.2)

def add(buf, sig, start, gain):
    i = int(start * SR)
    j = min(N, i + len(sig))
    if i < N:
        buf[i:j] += sig[: j - i] * gain

n_bars = int(np.ceil(DUR / BAR))
for b in range(n_bars):
    start = b * BAR
    ch = chords[b % 4]
    for k, m in enumerate(ch):
        sig = pad_note(midi(m), BAR + 1.2, 0.003)
        pan = 0.35 + 0.1 * k
        add(left, sig, start, 0.22 * (1 - pan))
        add(right, sig, start, 0.22 * pan)
    bass = pad_note(midi(roots[b % 4]), BAR + 0.8, 0.0015)
    add(left, bass, start, 0.2)
    add(right, bass, start, 0.2)
    # arpeggio: one soft note per beat
    for beat in range(4):
        m = ch[[0, 2, 3, 1][beat]] + 12
        sig = pluck(midi(m))
        side = 0.6 if beat % 2 else 0.4
        add(left, sig, start + beat * 1.0, 0.07 * (1 - side))
        add(right, sig, start + beat * 1.0, 0.07 * side)

# simple feedback-free "room": two short delays
for buf in (left, right):
    d1, d2 = int(0.083 * SR), int(0.137 * SR)
    buf[d1:] += 0.25 * buf[:-d1].copy()
    buf[d2:] += 0.18 * buf[:-d2].copy()

fade_in, fade_out = int(1.0 * SR), int(2.5 * SR)
for buf in (left, right):
    buf[:fade_in] *= np.linspace(0, 1, fade_in)
    buf[-fade_out:] *= np.linspace(1, 0, fade_out)

peak = max(np.abs(left).max(), np.abs(right).max())
stereo = np.stack([left, right], axis=1) / peak * 0.85
pcm = (stereo * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
