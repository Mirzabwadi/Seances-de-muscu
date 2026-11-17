"""Assemble the chosen takes of a talking-head video into one rough cut.

Each take gets 20/30 ms audio fades so the joins don't click, and the last frame
is held for --hold seconds (room for an end card).

Usage: python3 cut_takes.py IN.mp4 OUT.mp4 "4.80-9.30" "21.35-26.05" ... [--hold 1.5]

Then re-run `hyperframes transcribe OUT.mp4 --model medium --language fr` and read
the result: a repeated or stray word means a cut point needs moving (loudness_map.py).
"""
import argparse
import subprocess
import tempfile

p = argparse.ArgumentParser()
p.add_argument("src")
p.add_argument("out")
p.add_argument("takes", nargs="+")
p.add_argument("--hold", type=float, default=1.5)
a = p.parse_args()

segs = [tuple(float(x) for x in t.split("-")) for t in a.takes]
f, joins = [], []
for i, (s, e) in enumerate(segs):
    d = e - s
    f.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}]")
    f.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={d - 0.03:.3f}:d=0.03[a{i}]")
    joins.append(f"[v{i}][a{i}]")
f.append("".join(joins) + f"concat=n={len(segs)}:v=1:a=1[vc][ac]")
f.append(f"[vc]tpad=stop_mode=clone:stop_duration={a.hold}[v]")
f.append(f"[ac]apad=pad_dur={a.hold}[a]")

with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as script:
    script.write(";\n".join(f))
subprocess.run(
    ["ffmpeg", "-loglevel", "error", "-y", "-i", a.src, "-filter_complex_script", script.name,
     "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-r", "30",
     "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", a.out],
    check=True)

t = 0.0
print("take boundaries in the cut (use them to alternate zooms):")
for s, e in segs:
    t += e - s
    print(f"  {t:.2f}")
print(f"total {t + a.hold:.2f} s -> {a.out}")
