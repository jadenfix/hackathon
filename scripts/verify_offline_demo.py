#!/usr/bin/env python3
"""Verify recorded source, replay receipt, and fully decode demo artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "docs" / "demo"


def output(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads((DEMO / "capture.json").read_text(encoding="utf-8"))
    source = manifest["source_commit"]
    if output("git", "rev-parse", f"{source}^{{tree}}") != manifest["source_tree"]:
        raise RuntimeError("recorded source tree mismatch")
    subprocess.run(["git", "merge-base", "--is-ancestor", source, "HEAD"], cwd=ROOT, check=True)

    for path, blob in manifest["source_blobs"].items():
        if output("git", "rev-parse", f"{source}:{path}") != blob:
            raise RuntimeError(f"source blob mismatch: {path}")

    for relative, expected in manifest["artifacts"].items():
        path = ROOT / relative
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", relative], cwd=ROOT,
            check=True, stdout=subprocess.DEVNULL,
        )
        if path.stat().st_size != expected["bytes"] or digest(path) != expected["sha256"]:
            raise RuntimeError(f"artifact mismatch: {relative}")

    gif = DEMO / "offline-gridpilot.gif"
    with Image.open(gif) as image:
        frames = 0
        while True:
            image.load()
            frames += 1
            try:
                image.seek(image.tell() + 1)
            except EOFError:
                break
    if frames != manifest["frame_count"]:
        raise RuntimeError(f"GIF frame mismatch: {frames}")

    for media in (gif, DEMO / "offline-gridpilot.mp4"):
        subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(media), "-f", "null", "-"],
            check=True,
        )

    receipt = DEMO / "offline-cycle.json"
    with tempfile.TemporaryDirectory() as temporary:
        replay = Path(temporary) / "receipt.json"
        command = [
            sys.executable, "main.py", "--mode", "gridpilot", "--simulate", "1",
            "--seed", "8257", "--as-of", "2026-10-13T00:00:00Z",
            "--receipt", str(replay),
        ]
        completed = subprocess.run(
            command, cwd=ROOT, text=True, capture_output=True, timeout=90, check=True
        )
        if replay.read_bytes() != receipt.read_bytes():
            raise RuntimeError("replayed receipt differs from recorded receipt")
        if "SIMULATION - Would submit payload" not in completed.stdout:
            raise RuntimeError("replay did not traverse the fixture dispatch path")

    print(f"verified source={source} frames={frames} artifacts={len(manifest['artifacts'])}")


if __name__ == "__main__":
    main()
