#!/bin/bash
# Vertical 9:16 background from a landscape painting, centred on its subject,
# softened and darkened so the speaker stands out. Output 1188x2112 (10% headroom
# for a slow push-in), written next to the source as bg-<name>.jpg.
#
# Usage: crop_bg.sh IMAGE.jpg FOCAL_X [BLUR]
#   FOCAL_X: horizontal position of the subject, 0 (left) to 1 (right). Look at the
#   result and adjust: Socrates in David's painting sits at 0.60, Plato in Raphael's at 0.50.
#   BLUR: 4 (default) behind a cut-out speaker; 0 when the painting is the whole picture
#   (voice-over Reels), so the artwork stays sharp.
set -euo pipefail
in=$1 fx=$2 blur=${3:-4}
blurf=""
[ "$blur" != 0 ] && blurf="gblur=sigma=$blur,"
out="$(dirname "$in")/bg-$(basename "$in")"
ffmpeg -loglevel error -y -i "$in" -vf "crop='min(iw,ih*9/16)':ih:'max(0,min(iw-ih*9/16,iw*$fx-ih*9/32))':0,scale=1188:2112:flags=lanczos,${blurf}eq=brightness=-0.06:saturation=0.9" -q:v 3 "$out"
echo "$out"
