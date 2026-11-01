"""Build a HyperFrames captions sub-composition from a Whisper word transcript.

Usage:
  python3 make_captions.py TRANSCRIPT.json OUT.html [--edits EDITS.json] [--end SECONDS]

TRANSCRIPT.json is what `hyperframes transcribe --json` writes: a list of
{"text", "start", "end"} words. EDITS.json (optional) fixes what Whisper got
wrong, by word index:

  {
    "fix":       {"13": "Socrate", "110": "ciguë."},   # replacement text
    "drop":      [68, 76],                              # stray tokens to hide
    "merge_end": {"83": 84},                            # word 83 lasts until word 84 ends
    "accent":    [8, 13, 20],                           # words drawn in the accent colour
    "groups":    [[0, 1, 2], [3, 4]]                    # optional hand-made groups
  }

Without "groups", words are grouped automatically: a new group starts after a
sentence end, a pause of 150 ms or more, 5 words, or when the line would pass
MAX_CHARS (about one line at 64 px on a 1080 px wide frame).
"""
import argparse
import html
import json

MAX_CHARS = 22
MAX_WORDS = 5
PAUSE = 0.15

parser = argparse.ArgumentParser()
parser.add_argument("transcript")
parser.add_argument("out")
parser.add_argument("--edits")
parser.add_argument("--end", type=float, help="caption track length in seconds (default: last word + 1.2 s)")
args = parser.parse_args()

words = json.load(open(args.transcript))
if isinstance(words, dict):
    words = words.get("words", [])
edits = json.load(open(args.edits)) if args.edits else {}
fix = {int(k): v for k, v in edits.get("fix", {}).items()}
drop = set(edits.get("drop", []))
merge_end = {int(k): v for k, v in edits.get("merge_end", {}).items()}
accent = set(edits.get("accent", []))


def text_of(i):
    return fix.get(i, words[i]["text"])


def auto_groups():
    groups, cur = [], []
    for i, w in enumerate(words):
        if cur:
            prev = cur[-1]
            line = " ".join(text_of(j) for j in cur + [i] if j not in drop)
            sentence_end = text_of(prev).rstrip("»\" ").endswith((".", "!", "?", ":"))
            paused = w["start"] - words[prev]["end"] >= PAUSE
            if sentence_end or paused or len(cur) >= MAX_WORDS or len(line) > MAX_CHARS:
                groups.append(cur)
                cur = []
        cur.append(i)
    if cur:
        groups.append(cur)
    return groups


groups = edits.get("groups") or auto_groups()
assert [i for g in groups for i in g] == list(range(len(words))), "groups must cover every word in order"

built = []
for g in groups:
    ws = []
    for i in g:
        if i in drop:
            continue
        end = words[merge_end[i]]["end"] if i in merge_end else words[i]["end"]
        ws.append({"i": i, "text": text_of(i), "start": words[i]["start"], "end": end})
    if ws:
        built.append(ws)

last_end = args.end if args.end else built[-1][-1]["end"] + 1.2
spans = []
for n, ws in enumerate(built):
    start = max(0.15, ws[0]["start"] - 0.06)
    if n + 1 < len(built):
        nxt = max(0.15, built[n + 1][0]["start"] - 0.06)
        end = min(nxt, ws[-1]["end"] + 0.6)
    else:
        end = min(last_end, ws[-1]["end"] + 1.2)
    spans.append((start, end))

markup, script = [], []
for n, (ws, (start, end)) in enumerate(zip(built, spans)):
    gid = f"cap-g{n}"
    inner = " ".join(
        f'<span id="cap-w{w["i"]}" class="w{" acc" if w["i"] in accent else ""}">{html.escape(w["text"])}</span>'
        for w in ws
    )
    markup.append(
        f'    <div id="{gid}" class="cap clip" data-start="{start:.2f}" data-duration="{end - start:.2f}">'
        f'<div id="{gid}-in" class="cap-in">{inner}</div></div>'
    )
    script.append(
        f'    tl.fromTo("#{gid}-in", {{ y: 26, scale: 0.92, opacity: 0 }}, '
        f'{{ y: 0, scale: 1, opacity: 1, duration: 0.16, ease: "power3.out" }}, {start:.2f});'
    )
    for w in ws:
        col = "var(--cap-accent)" if w["i"] in accent else "var(--cap-ink)"
        script.append(
            f'    tl.fromTo("#cap-w{w["i"]}", {{ color: "var(--cap-dim)", scale: 1 }}, '
            f'{{ color: "{col}", scale: {1.08 if w["i"] in accent else 1}, duration: 0.08, ease: "power1.out" }}, {w["start"]:.2f});'
        )
    script.append(f'    tl.to("#{gid}-in", {{ opacity: 0, duration: 0.1, ease: "power2.in" }}, {end - 0.1:.2f});')

page = f"""<template>
  <style>
    #captions {{
      position: absolute;
      inset: 0;
      --cap-ink: #ffffff;
      --cap-dim: rgba(255, 255, 255, 0.74);
      --cap-accent: #ffd23f;
    }}
    .cap {{
      position: absolute;
      left: 0;
      right: 0;
      top: 1200px;
      height: 180px;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: visible;
    }}
    .cap-in {{
      max-width: 980px;
      text-align: center;
      font-family: "Inter", sans-serif;
      font-weight: 900;
      font-size: 64px;
      line-height: 1.08;
      letter-spacing: -0.01em;
      -webkit-text-stroke: 12px rgba(0, 0, 0, 0.9);
      paint-order: stroke fill;
      text-shadow: 0 6px 18px rgba(0, 0, 0, 0.55);
    }}
    .w {{
      display: inline-block;
      margin: 0 0.1em;
      color: var(--cap-dim);
    }}
  </style>
  <div id="captions" data-composition-id="captions" data-width="1080" data-height="1920">
{chr(10).join(markup)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(script)}
    window.__timelines["captions"] = tl;
  </script>
</template>
"""
open(args.out, "w").write(page)
print(f"{len(built)} groups -> {args.out}")
for ws in built:
    line = " ".join(w["text"] for w in ws)
    if len(line) > MAX_CHARS + 5:
        print("  long line, check it fits:", line)
