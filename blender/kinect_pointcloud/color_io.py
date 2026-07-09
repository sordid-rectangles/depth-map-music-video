"""Read Kinect color PNG frames directly (no Blender image datablocks).

Design note (important): we deliberately do NOT use a Blender image
`source = "SEQUENCE"` datablock here. Blender keeps its own internal ImBuf
cache of decoded sequence frames; at 2560x1440 that is ~59 MB per cached frame
(RGBA float), and scrubbing/playing across thousands of frames can grow that
cache to tens of GB and thrash the pagefile. Instead we decode one PNG per
frame with OpenImageIO into a small bounded LRU. Colors for smooth playback
come from the baked point cache, not from here.
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

# Small bounded LRU of decoded color frames (keyed by absolute path).
_pixel_cache: "OrderedDict[str, tuple]" = OrderedDict()
_MAX_PIXEL_CACHE = 4


def clear_color_cache() -> None:
    _pixel_cache.clear()


def read_color_png(path: Path):
    """Return (rgb uint8 HxWx3, width, height) for a single color PNG."""
    import numpy as np
    import OpenImageIO as oiio

    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Missing color file: {path}")

    key = str(path)
    cached = _pixel_cache.get(key)
    if cached is not None:
        _pixel_cache.move_to_end(key)
        return cached

    inp = oiio.ImageInput.open(key)
    if inp is None:
        raise RuntimeError(f"Could not open color PNG:\n  {path}")
    try:
        spec = inp.spec()
        w, h = spec.width, spec.height
        buf = inp.read_image(format=oiio.UINT8)
    finally:
        inp.close()

    arr = np.asarray(buf)
    if arr.ndim == 2:
        rgb = np.stack([arr, arr, arr], axis=2)
    elif arr.shape[2] >= 3:
        rgb = arr[:, :, :3]
    else:
        rgb = np.stack([arr[:, :, 0]] * 3, axis=2)

    result = (np.ascontiguousarray(rgb, dtype=np.uint8), w, h)
    _pixel_cache[key] = result
    if len(_pixel_cache) > _MAX_PIXEL_CACHE:
        _pixel_cache.popitem(last=False)
    return result


def probe_color_size(first_png: Path) -> tuple[int, int]:
    """Read image dimensions without decoding pixels."""
    import OpenImageIO as oiio

    inp = oiio.ImageInput.open(str(Path(first_png).resolve()))
    if inp is None:
        raise RuntimeError(f"Could not probe color image size: {first_png}")
    try:
        spec = inp.spec()
        return spec.width, spec.height
    finally:
        inp.close()
