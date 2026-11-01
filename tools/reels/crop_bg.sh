#!/bin/bash
# Vertical 9:16 background from a landscape painting, centred on its subject,
# softened and darkened so the speaker stands out. Output 1188x2112 (10% headroom
# for a slow push-in), written next to the source as bg-<name>.jpg.
#
# Usage: crop_bg.sh IMAGE.jpg FOCAL_X
#   FOCAL_X: horizontal position of the subject, 0 (left) to 1 (right). Look at the
#   result and adjust: Socrates in David's painting sits at 0.60, Plato in Raphael's at 0.50.
set -euo pipefail
in=$1 fx=$2
out="$(dirname "$in")/bg-$(basename "$in")"
ffmpeg -loglevel error -y -i "$in" -vf "crop='min(iw,ih*9/16)':ih:'max(0,min(iw-ih*9/16,iw*$fx-ih*9/32))':0,scale=1188:2112:flags=lanczos,gblur=sigma=4,eq=brightness=-0.06:saturation=0.9" -q:v 3 "$out"
echo "$out"
