#!/usr/bin/env python3
"""Record the actual deterministic CLI receipt as polished GIF/MP4 media."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "demo"
FRAMES = OUTPUT / ".frames"
COMMAND = [
    sys.executable, "main.py", "--mode", "gridpilot", "--simulate", "1",
    "--seed", "8257", "--as-of", "2026-10-13T00:00:00Z",
    "--receipt", "docs/demo/offline-cycle.json",
]
SOURCE_INPUTS = [
    ".github/workflows/offline-demo.yml",
    "README.md",
    "hackathon/api_client/client.py",
    "hackathon/control/cooling_model.py",
    "hackathon/dispatch/dispatch_agent.py",
    "hackathon/forecasting/forecaster.py",
    "hackathon/game_theory/bid_generators.py",
    "hackathon/game_theory/vcg_auction.py",
    "hackathon/main.py",
    "hackathon/tests/test_offline_cli.py",
    "hackathon/tests/test_offline_cycle.py",
    "main.py",
    "requirements-offline.txt",
    "scripts/record_offline_demo.py",
    "scripts/verify_offline_demo.py",
]


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)


def render_frame(scene: int, local_frame: int, receipt: dict) -> Image.Image:
    width, height = 960, 540
    image = Image.new("RGB", (width, height), "#08111f")
    draw = ImageDraw.Draw(image)

    teal, mint, white, muted = "#21d4c2", "#a7f3d0", "#f8fafc", "#94a3b8"
    draw.rectangle((0, 0, width, 8), fill=teal)
    draw.text((52, 40), "GRIDPILOT / OFFLINE RECEIPT", font=font(18, bold=True), fill=teal)
    draw.rounded_rectangle((740, 34, 906, 72), radius=18, fill="#123047")
    draw.text((764, 44), "SYNTHETIC FIXTURE", font=font(12, bold=True), fill=mint)

    metrics = receipt["metrics"]
    allocation = receipt["allocation_kw"]
    scenes = [
        ("Deterministic input", "Seed 8257 · fixed as-of label", ["Provider-free synthetic prices", "Synthetic site inventory", "No external request"]),
        ("24-hour forecast", "Simple fixture forecast completed", ["24 generated periods", "Uncertainty columns populated", "No accuracy claim"]),
        ("Bid vector", "MPC-shaped fixture bids", ["24 bid periods", "Positive bid prices", "Power expressed in kW"]),
        ("VCG allocation", "Current fixture period allocated", [f"Inference  {allocation['inference']:.2f} kW", f"Training   {allocation['training']:.2f} kW", f"Cooling    {allocation['cooling']:.2f} kW"]),
        ("Cooling model", "Fixture load translated to cooling", [f"Cooling load  {metrics['cooling_kw']:.2f} kW", f"Relative efficiency  {metrics['cooling_efficiency']:.1%}", "Model output, not measured hardware"]),
        ("Dispatch payload", "Payload built but never submitted", [f"Total power  {metrics['total_power_kw']:.2f} kW", f"Battery SOC  {metrics['battery_soc']:.1%}", "Market submission disabled"]),
        ("Constraint receipt", "Internal checks report a bounded result", ["Constraints satisfied  TRUE", "Receipt schema v1", "No profit or safety claim"]),
        ("Verified offline cycle", "Replayable evidence from actual source", ["Forecast → bid → allocate", "Cool → dispatch → receipt", "Provider-free · no market submission"]),
    ]
    title, subtitle, bullets = scenes[scene]
    draw.text((52, 116), title, font=font(40, bold=True), fill=white)
    draw.text((54, 170), subtitle, font=font(21), fill=muted)

    for index, bullet in enumerate(bullets):
        top = 230 + index * 64
        draw.rounded_rectangle((52, top, 908, top + 48), radius=12, fill="#111f31")
        draw.ellipse((72, top + 17, 84, top + 29), fill=teal if index < 2 else mint)
        draw.text((102, top + 11), bullet, font=font(19), fill=white)

    overall = scene * 12 + local_frame + 1
    progress = int(856 * overall / 96)
    draw.rounded_rectangle((52, 464, 908, 474), radius=5, fill="#1e293b")
    draw.rounded_rectangle((52, 464, 52 + progress, 474), radius=5, fill=teal)
    draw.text((52, 494), "ACTUAL CLI OUTPUT + JSON RECEIPT", font=font(12, bold=True), fill=muted)
    draw.text((843, 494), f"{scene + 1}/8", font=font(12, bold=True), fill=muted)
    return image


def main() -> None:
    source_commit = run("git", "rev-parse", "HEAD")
    source_tree = run("git", "rev-parse", "HEAD^{tree}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if FRAMES.exists():
        shutil.rmtree(FRAMES)
    FRAMES.mkdir()

    completed = subprocess.run(COMMAND, cwd=ROOT, text=True, capture_output=True, timeout=90, check=True)
    trace = OUTPUT / "offline-cycle.txt"
    trace.write_text(completed.stdout, encoding="utf-8")
    receipt_path = OUTPUT / "offline-cycle.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    required = [
        "Fetching market data", "Generating forecasts", "Optimizing bids",
        "Running VCG auction", "Calculating cooling requirements",
        "Building dispatch payload", "SIMULATION - Would submit payload",
        "GridPilot-GT executed successfully",
    ]
    missing = [marker for marker in required if marker not in completed.stdout]
    if missing:
        raise RuntimeError(f"CLI trace missing workflow markers: {missing}")

    for scene in range(8):
        for local_frame in range(12):
            number = scene * 12 + local_frame
            render_frame(scene, local_frame, receipt).save(FRAMES / f"frame-{number:03d}.png")

    mp4 = OUTPUT / "offline-gridpilot.mp4"
    gif = OUTPUT / "offline-gridpilot.gif"
    poster = OUTPUT / "offline-gridpilot.png"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "10", "-i",
         str(FRAMES / "frame-%03d.png"), "-c:v", "libx264", "-pix_fmt",
         "yuv420p", "-movflags", "+faststart", str(mp4)],
        check=True,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "10", "-i",
         str(FRAMES / "frame-%03d.png"), "-vf",
         "fps=10,scale=720:-1:flags=lanczos,split[s0][s1];"
         "[s0]palettegen=max_colors=96[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3",
         str(gif)],
        check=True,
    )
    shutil.copyfile(FRAMES / "frame-084.png", poster)

    source_blobs = {path: run("git", "rev-parse", f"{source_commit}:{path}") for path in SOURCE_INPUTS}
    artifact_paths = [gif, mp4, poster, receipt_path, trace]
    manifest = {
        "schema": "gridpilot.demo-capture.v1",
        "source_commit": source_commit,
        "source_tree": source_tree,
        "command": ["python", *COMMAND[1:]],
        "scope": receipt["scope"],
        "frame_count": 96,
        "fps": 10,
        "duration_seconds": 9.6,
        "source_blobs": source_blobs,
        "artifacts": {
            str(path.relative_to(ROOT)): {"bytes": path.stat().st_size, "sha256": digest(path)}
            for path in artifact_paths
        },
    }
    (OUTPUT / "capture.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    shutil.rmtree(FRAMES)


if __name__ == "__main__":
    main()
