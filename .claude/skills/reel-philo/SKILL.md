---
name: reel-philo
description: Turn a talking-head phone video (a philosopher, a gym session, any topic) into a finished vertical Instagram Reel 1080x1920 with HyperFrames — HDR fix, best takes, word-by-word French captions, antiquity or themed backgrounds behind the cut-out speaker, title card, end card and music. Use whenever the user sends a new video to edit, asks for a new Reel, or wants to change the Socrate one.
---

# Reel philo — the editing pipeline

The reference project is `socrate/` (the Socrate Reel, 63 s). Copy its structure for a new
subject: `index.html` (root), `compositions/intro.html`, `titles.html`, `captions.html`,
`outro.html`. Reusable scripts live in `tools/reels/`. Speak French with the user.

Run every `hyperframes` command with `NODE_USE_ENV_PROXY=1` (the session-start hook sets it);
without it, model downloads fail with `ENOTFOUND` or a proxy 403.

## 0. Get the video

- The chat often cannot take videos. Ask the user to put it on Google Drive, shared as
  "anyone with the link", and send the link. Download:
  `curl -sSL -o in.mov "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t"`
- Keep sources and renders out of git (see `socrate/.gitignore`): put the source in
  `<project>-src/` and add it to `.git/info/exclude`.
- Needed domains in the environment network settings: `drive.google.com`,
  `drive.usercontent.google.com`, `huggingface.co`, `*.hf.co`, `commons.wikimedia.org`,
  `upload.wikimedia.org`.

## 1. Normalise the footage

- `ffprobe` it. iPhone clips are HEVC HDR (`arib-std-b67`) with a -90 rotation:
  `tools/reels/hdr_to_sdr.sh in.mov sdr.mp4` (tone-maps to SDR 1080x1920; ~2.5 min).

## 2. Transcribe and pick the takes

- `hyperframes transcribe sdr.mp4 --model medium --language fr --json` (medium, not small:
  small mangles names and drifts). Read every word.
- The user re-reads lines. Keep one take per sentence: usually the last clean one, never one with
  a slip ("1400 ans", "la première fois"). Drop a title read aloud at the start (it goes on screen).
- Find cut points: `ffmpeg -i sdr.mp4 -af silencedetect=noise=-30dB:d=0.12 -f null -`, then
  `tools/reels/loudness_map.py sdr.mp4 START END` around each cut for 20 ms precision.
- `tools/reels/cut_takes.py sdr.mp4 edit.mp4 "a-b" "c-d" ... --hold 1.5`, then **re-transcribe
  edit.mp4** and read it: a stray "ou", a cut "Il", a doubled phrase means move that cut.
- Normalise the voice: `ffmpeg -i edit.mp4 -c:v copy -af "highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=9" ...`

## 3. Captions

- Copy the final transcript to `assets/transcript.json`; write the Whisper fixes in
  `assets/caption-edits.json` (format in `tools/reels/make_captions.py`; Socrate's is the example):
  spelling of names, punctuation, accent words (names, numbers, key ideas).
- `python3 tools/reels/make_captions.py assets/transcript.json compositions/captions.html --edits assets/caption-edits.json --end <talk length>`
- One line only, at most ~26 characters at 64 px: split longer groups. Captions sit at y≈1200,
  under the face, inside Instagram's safe band (168–1330 px).

## 4. Backgrounds and cut-out

- Speaker cut-out: `hyperframes remove-background assets/<video>.mp4 -o assets/<video>-cutout.webm`
  takes ~0.66 s per frame (~19 min for a minute). Start it early, in the background.
- Images: Wikimedia Commons, public domain or CC0/CC BY(-SA) only; check the licence via the API
  (`prop=imageinfo&iiprop=extmetadata`) and keep the credits for the Instagram caption.
  Download with `tools/reels/fetch_commons.sh` (1920 px thumbnails; originals get 429).
- Crop each painting vertically on its subject: `tools/reels/crop_bg.sh img.jpg FOCAL_X`, look at
  the result, adjust FOCAL_X.
- One background per part of the story, cross-faded, with a slow push-in (see `socrate/index.html`).

## 5. Title card, end card, music

- Intro (3.5 s): photo + kicker + name + one-line hook, visible on frame 0 (it is the thumbnail).
  No letter-spacing tweens (lint error): animate scale/opacity.
- Outro (≈4 s): the subject's portrait or bust, "Et toi ?" + "Réponds en commentaire 👇" on dark
  cards (text on light marble is unreadable without them).
- Music: `tools/reels/ambient_bed.py music.wav <seconds>` (calm) or `gym_beat.py` (energetic),
  then `loudnorm=I=-16`. Bed at volume 0.16 under the voice, 0.5 on intro/outro (automation lane).
  `tools/reels/intro_boom.py` for the title hit.
- Load GSAP from `assets/vendor/gsap.min.js`, never the CDN: the render browser cannot reach it.

## 6. Check, render, deliver

- `hyperframes check` must show 0 errors; then `hyperframes snapshot --at ...` on intro, each
  background, a long caption, outro — and look at the frames.
- `hyperframes render -o renders/<name>.mp4` (~7 min for a minute), then the Instagram file:
  `ffmpeg -i in.mp4 -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -af "loudnorm=I=-14:TP=-1:LRA=9" -ar 48000 -c:a aac -b:a 192k -movflags +faststart out-insta.mp4`
  (~30 MB, about -15 LUFS). Extract a few frames from the final file to confirm the cut-out rendered.
- Send the file with SendUserFile. Say honestly what was checked and that you cannot listen to it.
- Commit the project (not the renders, cut-out, source or `.transcode-cache/`) and push.

## Timings to quote

Download + HDR ≈ 4 min · transcription ≈ 4 min · takes ≈ 10 min · cut-out ≈ 19 min per minute of
video · render ≈ 7 min. Total ≈ 45–60 min for a one-minute Reel.
