"""Re-time the Kabyle Diogène Reel from a new recording.

Run after tools/reels/align_text.py has written assets/transcript.json and assets/lines.json:
  python3 retime.py
It rewrites the caption edits, the background timings in index.html, the date tag and the
outro, so a re-recorded memo only needs: align, retime, check, render.
"""
import json
import re
import subprocess

words = json.load(open("assets/transcript.json"))
lines = {l["n"]: l for l in json.load(open("assets/lines.json"))}
start = {n: l["start"] for n, l in lines.items()}
end = {n: l["end"] for n, l in lines.items()}

# Captions: the title read aloud is shown by the intro, so its words are not captioned.
drop = [i for i, w in enumerate(words) if w["line"] == 0]
fix = {}
for i, w in enumerate(words):
    t = w["text"]
    if t == "IHI,":
        fix[str(i)] = "Ihi,"
    elif t.endswith(" ,"):
        fix[str(i)] = t[:-2] + ","
accent_words = ("Diogène", "Alexandre", "lamba", "urgaz", "yiṭij", "lferḥ", "tnaflit", "tanaflit", "ilelli", "taqbuct", "teqbuct", "Athena")
accent = [i for i, w in enumerate(words) if any(w["text"].strip("«»(),.:?! ").startswith(a) for a in accent_words)]
json.dump({"fix": fix, "drop": drop, "accent": accent}, open("assets/caption-edits.json", "w"), ensure_ascii=False, indent=1)

second = next(w["start"] for w in words if w["line"] == 2 and w["text"].startswith("Yettwassen"))
intro_end = round(start[1], 2)
outro_start = round(start[11] - 0.2, 2)
total = round(end[11] + 4.3, 2)
caption_end = round(end[11] + 0.6, 2)

subprocess.run(["python3", "../tools/reels/make_captions.py", "assets/transcript.json", "compositions/captions.html",
                "--edits", "assets/caption-edits.json", "--end", str(caption_end),
                "--font", "Inter Kab", "--font-css", "../tools/reels/fonts-kab/fonts-kab.css"], check=True)

# One painting per sentence; each starts where its sentence starts.
cuts = [
    ("bg-jarre", intro_end - 0.4, start[2]),
    ("bg-ecole", start[2], second - 0.15),
    ("bg-paysage", second - 0.15, start[3]),
    ("bg-soleil", start[3], start[4]),
    ("bg-marches", start[4], start[5]),
    ("bg-bol", start[5], start[7]),
    ("bg-lanterne", start[7], start[9]),
    ("bg-alexandre", start[9], start[10]),
    ("bg-fin", start[10], outro_start + 0.4),
]
s = open("index.html").read()
for bid, a, b in cuts:
    a, b = round(a - 0.25, 2), round(b - 0.25, 2)  # the new picture lands just before the words
    s = re.sub(rf'(id="{bid}"[^>]*?data-start=")[^"]*(" data-duration=")[^"]*', rf"\g<1>{a}\g<2>{round(b - a, 2)}", s)
    s = re.sub(rf'(\["#{bid}", )[0-9.]+, [0-9.]+', rf"\g<1>{a}, {round(b - a, 2)}", s)
s = re.sub(r'(id="intro"[\s\S]*?data-duration=")[^"]*', rf"\g<1>{intro_end}", s, count=1)
s = re.sub(r'(id="titles"[\s\S]*?data-duration=")[^"]*', rf"\g<1>{outro_start}", s, count=1)
s = re.sub(r'(id="outro"[\s\S]*?data-start=")[^"]*("[\s\S]*?data-duration=")[^"]*', rf"\g<1>{outro_start}\g<2>{round(total - outro_start, 2)}", s, count=1)
s = re.sub(r'(id="captions"[\s\S]*?data-duration=")[^"]*', rf"\g<1>{caption_end}", s, count=1)
s = re.sub(r'(id="voice"[^>]*data-duration=")[^"]*', rf"\g<1>{round(end[11] + 1.2, 2)}", s)
s = re.sub(r'(id="root"[\s\S]*?data-duration=")[^"]*', rf"\g<1>{total}", s, count=1)
s = re.sub(r'(id="music"[\s\S]*?data-duration=")[^"]*', rf"\g<1>{total}", s, count=1)
q = end[11] + 0.2
s = re.sub(r'(&quot;t&quot;:)[0-9.]+(,&quot;v&quot;:0.16\}),\{&quot;t&quot;:[0-9.]+(,&quot;v&quot;:0.5\}),\{&quot;t&quot;:[0-9.]+',
           rf"\g<1>{round(q, 2)}\g<2>,{{&quot;t&quot;:{round(q + 0.7, 2)}\g<3>,{{&quot;t&quot;:{total}", s)
open("index.html", "w").write(s)

# Date tag on "Diogène d Afiluzuf..." until the second sentence.
t = open("compositions/titles.html").read()
a, b = round(start[2] + 0.3, 2), round(second - 0.3, 2)
t = re.sub(r'data-start="[0-9.]+" data-duration="[0-9.]+"', f'data-start="{a}" data-duration="{round(b - a + 0.2, 2)}"', t, count=1)
t = re.sub(r'ease: "power3.out" \}, [0-9.]+\);', f'ease: "power3.out" }}, {a});', t, count=1)
t = re.sub(r'ease: "power2.in" \}, [0-9.]+\);', f'ease: "power2.in" }}, {b});', t, count=1)
open("compositions/titles.html", "w").write(t)

# Outro: the card arrives once the closing question has been asked.
o = open("compositions/outro.html").read()
dur = round(total - outro_start, 2)
card = round(end[11] + 0.15 - outro_start, 2)
o = re.sub(r'data-start="0" data-duration="[0-9.]+"', f'data-start="0" data-duration="{dur}"', o, count=1)
o = re.sub(r"scale: 1.08, duration: [0-9.]+", f"scale: 1.08, duration: {dur}", o)
for sel, off in (("#outro-top", 0), ("#outro-q", 0.1), ("#outro-rule", 0.35), ("#outro-cta", 0.6), ("#outro-bottom", 1.1)):
    o = re.sub(rf'(tl\.fromTo\("{sel}",[^\n]*\}}, )[0-9.]+\);', rf"\g<1>{round(card + off, 2)});", o)
open("compositions/outro.html", "w").write(o)

print(f"intro 0-{intro_end}, outro {outro_start}-{total}, card at {round(outro_start + card, 2)}, tag {a}-{b}")
for bid, a, b in cuts:
    print(f"  {bid:13s} {a:6.2f} -> {b:6.2f}")
