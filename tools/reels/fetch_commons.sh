#!/bin/bash
# Download Wikimedia Commons images as 1920 px thumbnails, politely, retrying on 429.
#
# Usage: fetch_commons.sh OUT_DIR LIST.txt
# LIST.txt has one image per line: <local-name>|<Commons file name>
#   mort-de-socrate|David - The Death of Socrates.jpg
#
# Check each file's licence first (public domain or CC0/CC BY/CC BY-SA, credited):
#   https://commons.wikimedia.org/wiki/File:<file name>
# The environment must allow upload.wikimedia.org (and commons.wikimedia.org for the API).
set -uo pipefail
out=$1 list=$2
UA="ReelsPhilo/1.0 (personal video project)"
mkdir -p "$out"
while IFS='|' read -r name file; do
  [ -z "$name" ] && continue
  [ -s "$out/$name.jpg" ] && { echo "$name: already there"; continue; }
  file=${file// /_}
  hash=$(printf '%s' "$file" | md5sum | cut -c1-2)
  enc=$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$file")
  url="https://upload.wikimedia.org/wikipedia/commons/thumb/${hash:0:1}/$hash/$enc/1920px-$enc"
  for wait in 20 40 80 160 300 0; do
    code=$(curl -sS --max-time 120 -A "$UA" -o "$out/$name.part" -w "%{http_code}" "$url")
    if [ "$code" = "200" ] && file "$out/$name.part" | grep -qE "JPEG|PNG"; then
      mv "$out/$name.part" "$out/$name.jpg"; echo "$name: OK"; break
    fi
    rm -f "$out/$name.part"
    [ "$wait" = 0 ] && { echo "$name: FAILED (HTTP $code)"; break; }
    echo "$name: HTTP $code, retry in ${wait}s"; sleep "$wait"
  done
  sleep 10
done < "$list"
