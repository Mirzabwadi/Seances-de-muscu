#!/bin/bash
# iPhone HDR (HEVC/HLG) to SDR H.264 1080x1920, so colours don't look washed out on Instagram.
# Also handles the rotation flag of portrait iPhone clips. About 2.5 min per 2 min of 4-core CPU time.
#
# Usage: hdr_to_sdr.sh IN.mov OUT.mp4
set -euo pipefail
ffmpeg -loglevel error -y -i "$1" -map 0:v:0 -map 0:a:0 \
  -vf "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,scale=1080:1920:flags=lanczos,setsar=1" \
  -c:v libx264 -preset veryfast -crf 18 -c:a aac -b:a 192k -movflags +faststart "$2"
