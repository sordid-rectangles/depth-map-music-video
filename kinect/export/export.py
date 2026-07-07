#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "pyk4a",
#   "opencv-python",
#   "numpy",
# ]
# ///
"""
Export an Azure Kinect MKV recording to take-scoped image sequences for
Blender / TouchDesigner.

    take-01-20260622-175023/
        depth/            frame_000001.exr   (raw depth, depth-camera space, float32 mm)
        depth_aligned/    frame_000001.exr   (depth reprojected into color-camera space)
        color/            frame_000001.png
        ir/               frame_000001.exr
        calibration.json
        manifest.json

Run with uv - no venv or pip install needed:

    uv run export.py <take.mkv> --out <export_root>

Designed to be driven by another process (e.g. the operator.exe TUI): progress
is reported on stdout as single-line markers so a parent process can track it:

    TOTAL <frame_count>
    FRAME <n>
    DONE
    ERROR <message>
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

# Must be set before cv2 is imported - EXR support is opt-in for security reasons.
os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")

import cv2
import numpy as np

try:
    import pyk4a
    from pyk4a import CalibrationType, FPS, PyK4APlayback
except ImportError:
    print("ERROR pyk4a not found - run with: uv run export.py ...", file=sys.stderr)
    sys.exit(1)

TOOL_VERSION = "1.0.0"
_NOMINAL_FPS = {FPS.FPS_5: 5, FPS.FPS_15: 15, FPS.FPS_30: 30}


def log(*parts) -> None:
    print(*parts, flush=True)


def export_take(mkv_path: Path, output_root: Path, want_color: bool, want_ir: bool, want_depth_aligned: bool) -> None:
    take_name = mkv_path.stem
    take_dir = output_root / take_name

    depth_dir = take_dir / "depth"
    aligned_dir = take_dir / "depth_aligned"
    color_dir = take_dir / "color"
    ir_dir = take_dir / "ir"

    pb = PyK4APlayback(str(mkv_path))
    pb.open()

    calibration = _write_calibration(take_dir, pb)
    color_track_present = bool(pb.configuration.get("color_track_enabled"))
    can_align = want_depth_aligned and want_color and color_track_present and calibration is not None

    nominal_fps = _NOMINAL_FPS.get(pb.configuration.get("camera_fps"), 30)
    if pb.length:
        log("TOTAL", round((pb.length / 1_000_000) * nominal_fps))

    frame_num = 0
    has_color = False
    has_ir = False
    has_depth_aligned = False

    while True:
        try:
            capture = pb.get_next_capture()
        except EOFError:
            break
        if capture is None:
            break

        frame_num += 1
        fname = f"frame_{frame_num:06d}"

        if capture.depth is not None:
            depth_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(depth_dir / f"{fname}.exr"), capture.depth.astype(np.float32))

        if can_align and capture.transformed_depth is not None:
            aligned_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(aligned_dir / f"{fname}.exr"), capture.transformed_depth.astype(np.float32))
            has_depth_aligned = True

        if want_color and capture.color is not None:
            color_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(color_dir / f"{fname}.png"), capture.color)
            has_color = True

        if want_ir and capture.ir is not None:
            ir_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(ir_dir / f"{fname}.exr"), capture.ir.astype(np.float32))
            has_ir = True

        log("FRAME", frame_num)

    duration_usec = pb.length
    pb.close()

    fps = None
    if duration_usec and duration_usec > 0:
        fps = round(frame_num / (duration_usec / 1_000_000))

    _write_manifest(
        take_dir, mkv_path,
        frame_count=frame_num, fps=fps,
        has_color=has_color, has_ir=has_ir, has_depth_aligned=has_depth_aligned,
    )
    log("DONE")


def _write_calibration(take_dir: Path, pb: PyK4APlayback):
    try:
        cal = pb.calibration
    except Exception as e:
        log("ERROR", f"could not read calibration: {e}")
        return None

    data = {}
    for name, cam_type in [("depth", CalibrationType.DEPTH), ("color", CalibrationType.COLOR)]:
        try:
            k = cal.get_camera_matrix(cam_type)
            dist = cal.get_distortion_coefficients(cam_type)
            data[name] = {
                "fx": float(k[0, 0]), "fy": float(k[1, 1]),
                "cx": float(k[0, 2]), "cy": float(k[1, 2]),
                "distortion": [float(v) for v in dist],
            }
        except Exception as e:
            log("ERROR", f"could not read {name} calibration: {e}")

    if not data:
        return None

    take_dir.mkdir(parents=True, exist_ok=True)
    with open(take_dir / "calibration.json", "w") as f:
        json.dump(data, f, indent=2)
    return data


def _write_manifest(take_dir: Path, mkv_path: Path, *, frame_count, fps, has_color, has_ir, has_depth_aligned) -> None:
    stat = mkv_path.stat()
    manifest = {
        "source_filename": mkv_path.name,
        "source_size_bytes": stat.st_size,
        "source_mtime": datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc).isoformat(),
        "exported_at": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
        "tool_version": TOOL_VERSION,
        "frame_count": frame_count,
        "fps": fps,
        "has_color": has_color,
        "has_ir": has_ir,
        "has_depth_aligned": has_depth_aligned,
    }
    take_dir.mkdir(parents=True, exist_ok=True)
    with open(take_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Kinect MKV recordings to image sequences")
    parser.add_argument("files", nargs="+", type=Path, help="One or more .mkv files to export")
    parser.add_argument("--out", type=Path, required=True, metavar="FOLDER", help="Export root folder")
    parser.add_argument("--no-color", action="store_true", help="Skip color export")
    parser.add_argument("--no-ir", action="store_true", help="Skip IR export")
    parser.add_argument("--no-depth-aligned", action="store_true", help="Skip color-aligned depth export")
    args = parser.parse_args()

    for mkv_path in args.files:
        if not mkv_path.exists():
            log("ERROR", f"file not found: {mkv_path}")
            continue
        try:
            log("TAKE", mkv_path.name)
            export_take(
                mkv_path, args.out,
                want_color=not args.no_color,
                want_ir=not args.no_ir,
                want_depth_aligned=not args.no_depth_aligned,
            )
        except Exception as e:
            log("ERROR", str(e))
            sys.exit(1)


if __name__ == "__main__":
    main()
