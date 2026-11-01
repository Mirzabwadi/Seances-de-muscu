"""Align a known text to a recording, word by word, in any of ~1100 languages (Kabyle included).

Whisper cannot transcribe Kabyle; this does forced alignment instead: the words are known
(the speaker read them), only their timing is found. Model: Meta MMS forced aligner
(MahmoudAshraf/mms-300m-1130-forced-aligner on Hugging Face, ~1.2 GB, CPU is fine).
Needs: pip install torch torchaudio transformers soundfile.

Usage: python3 align_text.py AUDIO TEXT.txt OUT_transcript.json [--lines OUT_lines.json]

TEXT.txt: what was read, in reading order. Lines starting with "N." are numbered lines;
any other non-empty line (a title read aloud) is aligned too. The output has the same shape
as `hyperframes transcribe` ({"text", "start", "end"} per word), so make_captions.py takes it.
"""
import argparse
import json
import re
import subprocess
import tempfile
import unicodedata

import soundfile as sf
import torch
import torchaudio.functional as F
from transformers import AutoProcessor, Wav2Vec2ForCTC

MODEL = "MahmoudAshraf/mms-300m-1130-forced-aligner"
SR = 16000
CHUNK_S = 20  # seconds per inference window; keeps attention memory small on CPU

p = argparse.ArgumentParser()
p.add_argument("audio")
p.add_argument("text")
p.add_argument("out")
p.add_argument("--lines")
a = p.parse_args()

# The text, line by line, words with their display form.
lines = []
for raw in open(a.text, encoding="utf-8").read().splitlines():
    raw = raw.strip()
    if not raw:
        continue
    m = re.match(r"^(\d+)\.\s*(.*)$", raw)
    lines.append({"n": int(m.group(1)) if m else 0, "text": (m.group(2) if m else raw)})


def romanize(word):
    """Map a written word onto the aligner's a-z alphabet (display text is kept as written)."""
    w = word.lower().replace("ɣ", "g").replace("ɛ", "e").replace("ə", "e").replace("ţ", "t")
    w = unicodedata.normalize("NFKD", w)
    w = "".join(c for c in w if not unicodedata.combining(c))
    return "".join(c for c in w if c in VOCAB)


proc = AutoProcessor.from_pretrained(MODEL)
model = Wav2Vec2ForCTC.from_pretrained(MODEL).eval()
vocab = proc.tokenizer.get_vocab()
VOCAB = {c for c in vocab if len(c) == 1}

# Display words with their romanized form and line. Punctuation-only tokens are glued on:
# opening ones (« ( “) to the next word, closing ones (» : ? !) to the previous one.
words = []
pending = ""
for li, line in enumerate(lines):
    for tok in line["text"].split():
        r = romanize(tok)
        if not r:
            if tok in ("«", "(", "“"):
                pending = tok + " "
            elif words and words[-1]["line"] == li:
                words[-1]["text"] += " " + tok
            continue
        words.append({"text": pending + tok, "rom": r, "line": li})
        pending = ""

# Audio -> 16 kHz mono -> frame log-probabilities.
with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.audio, "-ac", "1", "-ar", str(SR), tmp.name], check=True)
    audio, _ = sf.read(tmp.name, dtype="float32")
emissions = []
with torch.inference_mode():
    for s in range(0, len(audio), CHUNK_S * SR):
        chunk = torch.from_numpy(audio[s:s + CHUNK_S * SR])
        if len(chunk) < SR // 10:
            continue
        inputs = proc(chunk.numpy(), sampling_rate=SR, return_tensors="pt")
        emissions.append(torch.log_softmax(model(**inputs).logits[0], dim=-1))
emission = torch.cat(emissions)
frame_s = len(audio) / SR / emission.shape[0]

# Forced alignment of the character sequence, then back to words.
targets = [vocab[c] for w in words for c in w["rom"]]
blank = vocab["<blank>"]
ali, scores = F.forced_align(emission.unsqueeze(0), torch.tensor([targets], dtype=torch.int32), blank=blank)
spans = F.merge_tokens(ali[0], scores[0].exp(), blank=blank)
k = 0
out = []
for w in words:
    n = len(w["rom"])
    first, last = spans[k], spans[k + n - 1]
    k += n
    out.append({"text": w["text"], "start": round(first.start * frame_s, 3), "end": round((last.end) * frame_s, 3),
                "line": lines[w["line"]]["n"]})
for i, w in enumerate(out):
    w["id"] = f"w{i}"
json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=1)

if a.lines:
    summary = []
    for li, line in enumerate(lines):
        ws = [o for o, w in zip(out, words) if w["line"] == li]
        if ws:
            summary.append({"n": line["n"], "start": ws[0]["start"], "end": ws[-1]["end"], "text": line["text"]})
    json.dump(summary, open(a.lines, "w"), ensure_ascii=False, indent=1)
    for s in summary:
        print(f'{s["n"]:>2}  {s["start"]:6.2f} -> {s["end"]:6.2f}  {s["text"][:60]}')
print(f"{len(out)} words aligned -> {a.out}")
