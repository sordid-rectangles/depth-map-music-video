"""Bake a Kinect take into an on-disk point cache for fast, memory-bounded playback.

Playback speed is dominated by EXR/PNG decode + unproject, not the mesh write.
Baking pre-computes the unprojected positions/colors/depth once per take so
playback only streams one frame's arrays from disk and writes them to CloudData
-- no decode, no unproject, no Blender image cache in the frame loop.

Cache layout (inside the take folder):

    <take>/blender_cache/
        manifest.json     # version, frame_count, bake params, per-frame index
        positions.f32     # concatenated float32 (N_f x 3) per frame
        colors.u8         # concatenated uint8   (N_f x 3) per frame
        depth_mm.f32      # concatenated float32 (N_f)     per frame

Reads use plain buffered seek/read (not mmap) so only one frame is ever resident
in memory -- baking or playing a multi-thousand-frame take can never balloon RAM.

Changing subsample / near / far / width_scale requires a re-bake (params are
recorded in the manifest and compared on load).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

CACHE_DIRNAME = "blender_cache"
CACHE_VERSION = 1

# Per-point on-disk cost: positions 3*f32 (12) + colors 3*u8 (3) + depth f32 (4).
BYTES_PER_POINT = 19

# Module-level active cache (attached on load / after bake).
_active_cache = None


def cache_dir(take_dir: Path) -> Path:
    return Path(take_dir) / CACHE_DIRNAME


def _cache_paths(take_dir: Path):
    cdir = cache_dir(take_dir)
    return (
        cdir / "manifest.json",
        cdir / "positions.f32",
        cdir / "colors.u8",
        cdir / "depth_mm.f32",
    )


def current_params(settings) -> dict:
    return {
        "subsample": int(settings.subsample),
        "near_mm": round(float(settings.near_mm), 4),
        "far_mm": round(float(settings.far_mm), 4),
        "width_scale": round(float(settings.width_scale), 6),
    }


def read_manifest(take_dir: Path):
    mpath = cache_dir(take_dir) / "manifest.json"
    if not mpath.is_file():
        return None
    try:
        with mpath.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def is_cache_valid(take_dir: Path, settings, frame_count: int) -> bool:
    manifest = read_manifest(take_dir)
    if not manifest:
        return False
    if manifest.get("version") != CACHE_VERSION:
        return False
    if int(manifest.get("frame_count", -1)) != int(frame_count):
        return False
    if manifest.get("params") != current_params(settings):
        return False
    _, pos_p, col_p, dep_p = _cache_paths(take_dir)
    return pos_p.is_file() and col_p.is_file() and dep_p.is_file()


def estimate_bake(take_dir: Path, settings, frame_count: int) -> dict:
    """Preflight: decode frame 1, count points, and project total cache size.

    Returns a dict with points_per_frame, frame_count, est_bytes, free_bytes and
    an 'ok' flag / 'reason' so the caller can refuse a runaway bake.
    """
    from . import import_take

    take_dir = Path(take_dir)
    meta = import_take.read_take_metadata(take_dir)
    params = current_params(settings)

    depth, color, w, h = import_take.load_frame_arrays(meta, 1)
    intrinsics = import_take.scaled_intrinsics(
        meta["calibration"]["color"], w, h, params["width_scale"]
    )
    coords, _colors, _depth = import_take._unproject_numpy(
        depth, color, intrinsics,
        params["subsample"], params["near_mm"], params["far_mm"],
    )
    ppf = int(len(coords))
    est_bytes = ppf * BYTES_PER_POINT * int(frame_count)

    try:
        free_bytes = shutil.disk_usage(str(take_dir)).free
    except Exception:
        free_bytes = None

    result = {
        "points_per_frame": ppf,
        "frame_count": int(frame_count),
        "est_bytes": est_bytes,
        "free_bytes": free_bytes,
        "resolution": [w, h],
        "ok": True,
        "reason": "",
    }

    # Refuse if the cache would swallow the disk or exceed a hard ceiling.
    if free_bytes is not None and est_bytes > free_bytes * 0.85:
        result["ok"] = False
        result["reason"] = (
            f"Estimated cache {est_bytes / 1e9:.1f} GB would use most of the "
            f"{free_bytes / 1e9:.1f} GB free on this drive. "
            "Raise Subsample or free disk space."
        )
    elif est_bytes > 40 * 1e9:
        result["ok"] = False
        result["reason"] = (
            f"Estimated cache {est_bytes / 1e9:.1f} GB is very large "
            f"({ppf:,} pts/frame x {frame_count:,} frames). "
            "Raise Subsample before baking."
        )
    return result


def bake_iter(take_dir: Path, settings, frame_count: int):
    """Generator that bakes one frame per step; yields (frame, frame_count).

    Reads depth+color per frame directly and writes unprojected arrays to the
    cache files. Finalizes the manifest on the last frame. If interrupted, the
    manifest is never written, so a partial cache reads as "not baked".
    """
    import numpy as np

    from . import import_take

    take_dir = Path(take_dir)
    meta = import_take.read_take_metadata(take_dir)
    cdir = cache_dir(take_dir)
    cdir.mkdir(parents=True, exist_ok=True)
    mpath, pos_p, col_p, dep_p = _cache_paths(take_dir)

    # Drop any stale manifest up front so an interrupted bake can't look valid.
    if mpath.is_file():
        try:
            mpath.unlink()
        except OSError:
            pass

    params = current_params(settings)
    index: list[list[int]] = []
    total = 0
    resolution = None
    missing = 0

    with pos_p.open("wb") as pf, col_p.open("wb") as cf, dep_p.open("wb") as df:
        for frame in range(1, frame_count + 1):
            try:
                depth, color, w, h = import_take.load_frame_arrays(meta, frame)
                if resolution is None:
                    resolution = [w, h]
                intrinsics = import_take.scaled_intrinsics(
                    meta["calibration"]["color"], w, h, params["width_scale"]
                )
                coords, colors, depth_attr = import_take._unproject_numpy(
                    depth, color, intrinsics,
                    params["subsample"], params["near_mm"], params["far_mm"],
                )
            except (FileNotFoundError, RuntimeError):
                # Missing/broken frame (export gaps happen) -- keep the timeline
                # aligned by writing an empty frame.
                missing += 1
                coords = np.zeros((0, 3), dtype=np.float32)
                colors = np.zeros((0, 3), dtype=np.uint8)
                depth_attr = np.zeros((0,), dtype=np.float32)

            n = len(coords)
            pf.write(np.ascontiguousarray(coords, dtype=np.float32).tobytes())
            cf.write(np.ascontiguousarray(colors, dtype=np.uint8).tobytes())
            df.write(np.ascontiguousarray(depth_attr, dtype=np.float32).tobytes())
            index.append([total, n])
            total += n
            yield frame, frame_count

    manifest = {
        "version": CACHE_VERSION,
        "frame_count": int(frame_count),
        "params": params,
        "index": index,
        "total_points": total,
        "resolution": resolution,
        "missing_frames": missing,
    }
    with mpath.open("w", encoding="utf-8") as mf:
        json.dump(manifest, mf)


def bake_all(take_dir: Path, settings, frame_count: int, progress=None) -> None:
    """Run the full bake synchronously (used by tests / headless)."""
    for frame, total in bake_iter(take_dir, settings, frame_count):
        if progress is not None:
            progress(frame, total)


class BakedCache:
    """Buffered seek/read access to a baked take cache (one frame resident)."""

    def __init__(self, take_dir: Path, manifest: dict):
        self.take_dir = Path(take_dir)
        self.manifest = manifest
        self.index = manifest["index"]
        self.frame_count = int(manifest["frame_count"])
        _, pos_p, col_p, dep_p = _cache_paths(self.take_dir)

        # Keep three small buffered handles open; each read is one frame slice.
        self._pos = open(pos_p, "rb")
        self._col = open(col_p, "rb")
        self._dep = open(dep_p, "rb")

    def frame(self, frame: int):
        """Return (positions Nx3 float32, colors Nx3 uint8, depth_mm N) for 1-based frame."""
        import numpy as np

        if frame < 1 or frame > self.frame_count:
            return None
        start, n = self.index[frame - 1]
        if n == 0:
            return (
                np.zeros((0, 3), dtype=np.float32),
                np.zeros((0, 3), dtype=np.uint8),
                np.zeros((0,), dtype=np.float32),
            )

        self._pos.seek(start * 3 * 4)
        pos = np.frombuffer(self._pos.read(n * 3 * 4), dtype=np.float32).reshape(n, 3)
        self._col.seek(start * 3)
        col = np.frombuffer(self._col.read(n * 3), dtype=np.uint8).reshape(n, 3)
        self._dep.seek(start * 4)
        dep = np.frombuffer(self._dep.read(n * 4), dtype=np.float32)
        return pos, col, dep

    def close(self) -> None:
        for handle in ("_pos", "_col", "_dep"):
            fh = getattr(self, handle, None)
            if fh is not None:
                try:
                    fh.close()
                except OSError:
                    pass
                setattr(self, handle, None)


def attach_cache(take_dir: Path) -> "BakedCache | None":
    global _active_cache
    detach_cache()
    manifest = read_manifest(take_dir)
    if not manifest:
        return None
    try:
        _active_cache = BakedCache(take_dir, manifest)
    except Exception:
        _active_cache = None
    return _active_cache


def detach_cache() -> None:
    global _active_cache
    if _active_cache is not None:
        _active_cache.close()
    _active_cache = None


def get_active_cache():
    return _active_cache
