#!/bin/bash
# Convert all .mp3 files in songs/source/ to mono 22050 Hz WAV files in songs/

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR="$PROJECT_DIR/songs/source"
OUTPUT_DIR="$PROJECT_DIR/songs"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: $SOURCE_DIR does not exist"
    exit 1
fi

count=0
for mp3 in "$SOURCE_DIR"/*.mp3; do
    [ -f "$mp3" ] || continue
    name="$(basename "$mp3" .mp3)"
    out="$OUTPUT_DIR/$name.wav"
    echo "Converting: $name.mp3 -> $name.wav"
    ffmpeg -y -i "$mp3" -ac 1 -ar 22050 "$out" -loglevel warning
    count=$((count + 1))
done

echo "Done. Converted $count file(s)."
