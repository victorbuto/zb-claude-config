#!/usr/bin/env python3
"""
Converts a .whisper file (ZIP archive from WhisperKit) to a plain .txt transcript.

Usage:
    python3 convert_whisper.py <path_to_file.whisper>

Output:
    Creates a .txt file in the same directory with the same base name.
    Format: "Speaker Name: text" per line.
"""

import json
import zipfile
import sys
import os


def convert(whisper_path: str) -> str:
    out_path = os.path.splitext(whisper_path)[0] + ".txt"

    with zipfile.ZipFile(whisper_path) as z:
        with z.open("metadata.json") as f:
            data = json.load(f)

    lines = []
    for seg in data.get("transcripts", []):
        speaker = seg.get("speaker") or {}
        name = speaker.get("name", "Unknown") if isinstance(speaker, dict) else "Unknown"
        text = seg.get("text", "").strip()
        if text:
            lines.append(f"{name}: {text}")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 convert_whisper.py <file.whisper>")
        sys.exit(1)

    result = convert(sys.argv[1])
    print(f"Saved to: {result}")
