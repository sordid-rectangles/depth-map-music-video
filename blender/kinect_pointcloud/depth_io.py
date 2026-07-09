"""Read Kinect depth EXR files (single-channel float32 Z in mm).

Uses Blender's bundled OpenImageIO (same library Blender uses for EXR I/O).
Do NOT use pip-installed OpenEXR inside Blender — it crashes (ABI mismatch).
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

_DEPTH_CACHE: OrderedDict[str, tuple] = OrderedDict()
_MAX_DEPTH_CACHE = 6


def clear_depth_cache() -> None:
    _DEPTH_CACHE.clear()


def read_depth_exr_mm(path: Path):
    """Return (depth_mm float32 HxW, width, height)."""
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Missing depth file: {path}")

    key = str(path)
    if key in _DEPTH_CACHE:
        _DEPTH_CACHE.move_to_end(key)
        depth, w, h = _DEPTH_CACHE[key]
        return depth, w, h

    errors: list[str] = []

    try:
        depth, w, h = _read_with_openimageio(path)
        if depth is not None:
            _remember_depth(key, depth, w, h)
            return depth, w, h
    except Exception as exc:
        errors.append(f"OpenImageIO: {exc}")

    try:
        depth, w, h = _read_with_blender(path)
        if depth is not None:
            _remember_depth(key, depth, w, h)
            return depth, w, h
    except Exception as exc:
        errors.append(f"Blender image: {exc}")

    detail = "\n".join(errors) if errors else "No reader returned pixel data."
    raise RuntimeError(f"Could not read depth EXR:\n  {path}\n\n{detail}")


def _remember_depth(key: str, depth, w: int, h: int) -> None:
    _DEPTH_CACHE[key] = (depth, w, h)
    if len(_DEPTH_CACHE) > _MAX_DEPTH_CACHE:
        _DEPTH_CACHE.popitem(last=False)


def _read_with_openimageio(path: Path):
    import numpy as np

    try:
        import OpenImageIO as oiio
    except ImportError as exc:
        raise ImportError("OpenImageIO not available in this Blender build") from exc

    inp = oiio.ImageInput.open(str(path))
    if inp is None:
        raise RuntimeError(f"OpenImageIO could not open {path}")

    try:
        spec = inp.spec()
        w, h = spec.width, spec.height
        buf = inp.read_image(format=oiio.FLOAT)
    finally:
        inp.close()

    arr = np.asarray(buf, dtype=np.float32)
    if arr.ndim == 3:
        depth = arr[:, :, 0]
    elif arr.ndim == 2:
        depth = arr
    else:
        depth = arr.reshape(h, w)

    return depth, w, h


def _read_with_blender(path: Path):
    import bpy
    import numpy as np

    fp = path.as_posix()
    scratch_name = "_kinect_depth_read"

    img = bpy.data.images.get(scratch_name)
    if img is None:
        img = bpy.data.images.load(fp, check_existing=False)
        img.name = scratch_name
    elif bpy.path.abspath(img.filepath) != bpy.path.abspath(fp):
        img.filepath = fp
        img.reload()

    img.source = "FILE"
    img.update()
    if img.size[0] <= 0 or img.size[1] <= 0:
        raise RuntimeError("Blender could not decode this EXR")

    w, h = img.size
    n = w * h
    rgba = np.array(img.pixels[:], dtype=np.float32).reshape(n, 4)
    depth = rgba[:, 0]
    if depth.max() <= 0:
        depth = rgba[:, 3]
    if depth.max() <= 0:
        raise RuntimeError("Blender loaded EXR but depth channel is empty")
    return depth.reshape(h, w), w, h
