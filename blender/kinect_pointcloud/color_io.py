"""Color playback via Blender image sequence + ImageUser + scale() (Blender 4.2).

Sequence datablock + ImageUser maps timeline frames to take files efficiently.
Pixels are loaded with Image.scale(..., frame=N) — works without an OpenGL context,
unlike gl_load() which fails from add-on Python in many setups.
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

IMAGE_COLOR = "kinect_color_seq"
_HELPER_MAT = "_KinectColorSeqHelper"
_HELPER_NODE = "KinectColorSeqTex"

_image_user = None
_seq_size: tuple[int, int] = (0, 0)
_pixel_cache: OrderedDict[str, tuple] = OrderedDict()
_MAX_PIXEL_CACHE = 6


def clear_color_sequence() -> None:
    global _image_user, _seq_size
    import bpy

    _image_user = None
    _seq_size = (0, 0)
    _pixel_cache.clear()

    img = bpy.data.images.get(IMAGE_COLOR)
    if img is not None:
        bpy.data.images.remove(img, do_unlink=True)


def register_color_sequence(first_png: Path, frame_count: int, frame_start: int = 1) -> None:
    """Register take color/ as a Blender image sequence with absolute paths."""
    global _image_user, _seq_size

    first_png = Path(first_png).resolve()
    if not first_png.is_file():
        raise FileNotFoundError(f"Missing color file: {first_png}")

    fp = first_png.as_posix()
    clear_color_sequence()

    import bpy

    img = bpy.data.images.load(fp, check_existing=False)
    img.name = IMAGE_COLOR
    img.source = "SEQUENCE"

    user = _ensure_image_user(img)
    user.frame_start = frame_start
    user.frame_duration = max(1, frame_count)
    user.frame_offset = 0
    user.frame_current = frame_start
    user.use_auto_refresh = True

    _seq_size = _probe_size(first_png)
    _load_sequence_pixels(img, user, frame_start)


def read_color_sequence(frame: int):
    """Return (rgb uint8 HxWx3, width, height) for a 1-based timeline frame."""
    import bpy
    import numpy as np

    img = bpy.data.images.get(IMAGE_COLOR)
    if img is None:
        return None

    user = _ensure_image_user(img)
    resolved = _load_sequence_pixels(img, user, frame)

    if resolved in _pixel_cache:
        _pixel_cache.move_to_end(resolved)
        return _pixel_cache[resolved]

    w, h = img.size
    rgba = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    rgb = (rgba[:, :, :3] * 255.0).astype(np.uint8)
    result = (rgb, w, h)
    _pixel_cache[resolved] = result
    if len(_pixel_cache) > _MAX_PIXEL_CACHE:
        _pixel_cache.popitem(last=False)
    return result


def _ensure_image_user(img):
    global _image_user
    import bpy

    if _image_user is not None:
        tex = _get_helper_tex_node()
        if tex is not None:
            tex.image = img
        return _image_user

    mat = bpy.data.materials.get(_HELPER_MAT)
    if mat is None:
        mat = bpy.data.materials.new(_HELPER_MAT)
        mat.use_nodes = True
        mat.node_tree.nodes.clear()

    tex = mat.node_tree.nodes.get(_HELPER_NODE)
    if tex is None:
        tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.name = _HELPER_NODE

    tex.image = img
    _image_user = tex.image_user
    return _image_user


def _get_helper_tex_node():
    import bpy

    mat = bpy.data.materials.get(_HELPER_MAT)
    if mat is None or not mat.use_nodes:
        return None
    return mat.node_tree.nodes.get(_HELPER_NODE)


def _probe_size(first_png: Path) -> tuple[int, int]:
    import OpenImageIO as oiio

    inp = oiio.ImageInput.open(str(first_png))
    if inp is None:
        raise RuntimeError(f"Could not probe color image size: {first_png}")
    try:
        spec = inp.spec()
        return spec.width, spec.height
    finally:
        inp.close()


def _validate_sequence_path(img, user, timeline_frame: int) -> str:
    import bpy

    user.frame_current = timeline_frame
    resolved = img.filepath_from_user(image_user=user)
    if resolved.startswith("//"):
        resolved = bpy.path.abspath(resolved)

    if not resolved or not Path(resolved).is_file():
        raise RuntimeError(
            "Color sequence resolved to a missing file.\n"
            f"  Timeline frame: {timeline_frame}\n"
            f"  ImageUser: start={user.frame_start} current={user.frame_current} "
            f"offset={user.frame_offset}\n"
            f"  Sequence base: {img.filepath}\n"
            f"  Resolved: {resolved or '(empty)'}\n"
            "Use Load Take again — paths must stay absolute inside the take folder."
        )
    return resolved


def _load_sequence_pixels(img, user, timeline_frame: int) -> str:
    """Load sequence frame into img.pixels via scale(); return resolved filepath."""
    resolved = _validate_sequence_path(img, user, timeline_frame)
    w, h = _seq_size
    if w <= 0 or h <= 0:
        w, h = _probe_size(Path(resolved))

    candidates = (
        timeline_frame,
        max(0, timeline_frame - 1),
        max(0, timeline_frame - user.frame_start),
    )
    seen: set[int] = set()
    for fi in candidates:
        if fi in seen:
            continue
        seen.add(fi)
        try:
            img.scale(w, h, frame=fi)
            img.update()
            if img.size[0] > 0 and len(img.pixels) >= w * h * 4:
                return resolved
        except RuntimeError:
            pass

    _read_into_image_via_openimageio(img, resolved)
    return resolved


def _read_into_image_via_openimageio(img, resolved: str) -> None:
    """Populate img.pixels from disk when scale() could not decode the frame."""
    import numpy as np
    import OpenImageIO as oiio

    inp = oiio.ImageInput.open(resolved)
    if inp is None:
        raise RuntimeError(f"OpenImageIO could not open color frame:\n  {resolved}")

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

    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[:, :, :3] = rgb.astype(np.float32) / 255.0

    if img.size[0] != w or img.size[1] != h:
        img.scale(w, h)
    img.pixels.foreach_set(rgba.ravel())
    img.update()

    _pixel_cache[resolved] = (rgb.astype(np.uint8, copy=False), w, h)


def read_color_png(path: Path):
    """Fallback single-file read when sequence is not registered."""
    import numpy as np
    import OpenImageIO as oiio

    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Missing color file: {path}")

    inp = oiio.ImageInput.open(str(path))
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

    return rgb.astype(np.uint8, copy=False), w, h
