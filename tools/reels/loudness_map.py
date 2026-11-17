"""Print loudness every 20 ms over a time window, to place a cut between two words.

Speech sits around -16 to -30 dB; a gap between words dips below about -40 dB.
Usage: python3 loudness_map.py VIDEO START END
"""
import subprocess
import sys

import numpy as np

src, start, end = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
pcm = subprocess.run(
    ["ffmpeg", "-loglevel", "error", "-ss", str(start), "-to", str(end), "-i", src,
     "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
    capture_output=True, check=True).stdout
s = np.frombuffer(pcm, dtype=np.int16).astype(float)
n = 320  # 20 ms at 16 kHz
cells = []
for i in range(0, len(s) - n, n):
    db = 20 * np.log10(np.sqrt(np.mean(s[i:i + n] ** 2)) / 32768 + 1e-9)
    cells.append(f"{start + i / 16000:.2f}:{int(db)}")
print(" ".join(cells))
