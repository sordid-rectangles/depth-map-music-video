"""Load Kinect take metadata, image sequences, and rebuild CloudData geometry."""

from __future__ import annotations

import json
from pathlib import Path

import bpy

from . import color_io, default_render, depth_io, scene_setup

IMAGE_DEPTH = "kinect_depth_seq"
ATTR_DEPTH_MM = "depth_mm"

# Datablocks created by older add-on versions that must NOT linger in a .blend.
# The color SEQUENCE image with use_auto_refresh re-decodes a full-res frame on
# every frame change and balloons Blender's image cache in the background — the
# cause of the reboot-level lag. We no longer create these; purge any leftovers.
_STALE_IMAGE_NAMES = ("kinect_color_seq", "kinect_depth_seq", "_kinect_depth_read")
_STALE_MATERIAL_NAMES = ("_KinectColorSeqHelper",)

_meta_cache: dict[str, dict] = {}


def purge_stale_datablocks() -> list[str]:
    """Remove orphaned datablocks from old builds (color sequence image, helpers).

    Returns the names removed (for logging). Safe to call on every load.
    """
    removed: list[str] = []

    for mat_name in _STALE_MATERIAL_NAMES:
        mat = bpy.data.materials.get(mat_name)
        if mat is not None:
            bpy.data.materials.remove(mat, do_unlink=True)
            removed.append(mat_name)

    for img_name in _STALE_IMAGE_NAMES:
        img = bpy.data.images.get(img_name)
        if img is not None:
            bpy.data.images.remove(img, do_unlink=True)
            removed.append(img_name)

    # Also catch any image left in SEQUENCE mode pointing at this take's frames
    # (defensive: covers renamed leftovers from experimental builds).
    for img in list(bpy.data.images):
        if getattr(img, "source", "") == "SEQUENCE" and "kinect" in img.name.lower():
            name = img.name
            bpy.data.images.remove(img, do_unlink=True)
            removed.append(name)

    return removed


def _take_path(settings) -> Path | None:
    raw = (settings.take_path or "").strip()
    if not raw:
        return None
    return resolve_take_dir(_resolve_path(raw))


def _resolve_path(raw: str) -> Path:
    """Resolve take folder to an absolute filesystem path (never Blender // paths)."""
    if raw.startswith("//"):
        abs_raw = bpy.path.abspath(raw)
        if not abs_raw or abs_raw.startswith("//"):
            raise FileNotFoundError(
                "Take path is relative to the .blend file, but the file is not saved.\n"
                "Save the .blend or paste an absolute take folder path."
            )
        return Path(abs_raw).resolve()

    path = Path(raw)
    if not path.is_absolute():
        abs_raw = bpy.path.abspath(raw)
        if abs_raw and not abs_raw.startswith("//"):
            path = Path(abs_raw)
    return path.resolve()


def resolve_take_dir(path: Path) -> Path:
    """Resolve export take folder from user selection.

    Expected layout (from kinect/export):
      take-01-20260622-175023/
        depth_aligned/frame_000001.exr
        color/frame_000001.png
        calibration.json
        manifest.json
    """
    path = path.resolve()
    if _is_take_dir(path):
        return path

    # Export root with a single take subfolder — auto-select it.
    takes = sorted(
        p for p in path.iterdir()
        if p.is_dir() and _is_take_dir(p)
    )
    if len(takes) == 1:
        return takes[0]
    if len(takes) > 1:
        names = ", ".join(t.name for t in takes[:4])
        extra = f" (+{len(takes) - 4} more)" if len(takes) > 4 else ""
        raise FileNotFoundError(
            f"Export root contains {len(takes)} takes — pick one take folder, not the root.\n"
            f"Examples: {names}{extra}"
        )

    raise FileNotFoundError(
        "Not a Kinect take folder.\n"
        "Select the take folder that contains calibration.json, e.g.:\n"
        "  take-01-20260622-175023/\n"
        f"Got: {path}"
    )


def _is_take_dir(path: Path) -> bool:
    return (
        (path / "calibration.json").is_file()
        and (path / "manifest.json").is_file()
        and (path / "depth_aligned").is_dir()
        and (path / "color").is_dir()
    )


def get_take_metadata(take_dir: Path) -> dict:
    key = str(take_dir.resolve())
    if key not in _meta_cache:
        _meta_cache[key] = read_take_metadata(take_dir)
    return _meta_cache[key]


def clear_take_cache() -> None:
    _meta_cache.clear()
    depth_io.clear_depth_cache()
    color_io.clear_color_cache()


def read_take_metadata(take_dir: Path) -> dict:
    calib_path = take_dir / "calibration.json"
    manifest_path = take_dir / "manifest.json"
    if not calib_path.is_file():
        raise FileNotFoundError(f"Missing {calib_path.name}")
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing {manifest_path.name}")

    with calib_path.open(encoding="utf-8") as f:
        calibration = json.load(f)
    with manifest_path.open(encoding="utf-8") as f:
        manifest = json.load(f)

    depth_dir = take_dir / "depth_aligned"
    color_dir = take_dir / "color"
    if not depth_dir.is_dir():
        raise FileNotFoundError("Missing depth_aligned/ folder")
    if not color_dir.is_dir():
        raise FileNotFoundError("Missing color/ folder")

    return {
        "calibration": calibration,
        "manifest": manifest,
        "depth_dir": depth_dir,
        "color_dir": color_dir,
    }


def scaled_intrinsics(color_calib: dict, width: int, height: int, width_scale: float) -> dict:
    fx = float(color_calib["fx"])
    fy = float(color_calib["fy"])
    cx = float(color_calib["cx"])
    cy = float(color_calib["cy"])

    scale = width / (cx * 2.0)
    fx_s = fx * scale / width_scale
    fy_s = fy * scale
    cx_s = cx * scale
    cy_s = cy * scale

    return {"fx": fx_s, "fy": fy_s, "cx": cx_s, "cy": cy_s, "width": width, "height": height}


def _frame_paths(meta: dict, frame: int) -> tuple[Path, Path]:
    depth_path = meta["depth_dir"] / f"frame_{frame:06d}.exr"
    color_path = meta["color_dir"] / f"frame_{frame:06d}.png"
    if not depth_path.is_file():
        raise FileNotFoundError(f"Missing {depth_path.name}")
    if not color_path.is_file():
        raise FileNotFoundError(f"Missing {color_path.name}")
    return depth_path, color_path


def validate_take_frames(meta: dict) -> None:
    """Ensure first-frame files exist (called on Load Take)."""
    _frame_paths(meta, 1)


def load_frame_data(meta: dict, frame: int):
    """Load depth + color arrays for one timeline frame (direct decode)."""
    depth_path, color_path = _frame_paths(meta, frame)
    depth_data, w, h = depth_io.read_depth_exr_mm(depth_path)
    color_data, cw, ch = color_io.read_color_png(color_path)
    if (w, h) != (cw, ch):
        raise RuntimeError(f"Depth {w}x{h} and color {cw}x{ch} resolution mismatch")
    return depth_data, color_data, w, h


def load_frame_arrays(meta: dict, frame: int):
    """Decode depth+color for one frame directly. Used by bake (alias of load_frame_data)."""
    return load_frame_data(meta, frame)


def take_frame_count(meta: dict) -> int:
    """Authoritative frame count from the take manifest (never a stale setting)."""
    return max(1, int(meta["manifest"].get("frame_count", 1)))


def _unproject_numpy(depth, color, intrinsics, subsample: int, near_mm: float, far_mm: float):
    import numpy as np

    fx = intrinsics["fx"]
    fy = intrinsics["fy"]
    cx = intrinsics["cx"]
    cy = intrinsics["cy"]
    h, w = depth.shape

    ys = np.arange(0, h, subsample)
    xs = np.arange(0, w, subsample)
    grid_y, grid_x = np.meshgrid(ys, xs, indexing="ij")
    z_mm = depth[grid_y, grid_x]

    valid = z_mm > 0
    if near_mm > 0:
        valid &= z_mm >= near_mm
    if far_mm > 0:
        valid &= z_mm <= far_mm

    px = grid_x[valid].astype(np.float64)
    py = grid_y[valid].astype(np.float64)
    z_mm_v = z_mm[valid].astype(np.float64)
    z_m = z_mm_v / 1000.0

    x_cv = (px - cx) * z_m / fx
    y_cv = (py - cy) * z_m / fy

    # OpenCV: +X right, +Y down, +Z forward (depth).
    # Blender Z-up, default camera looks down -Y:
    x_bl = x_cv
    y_bl = -z_m
    z_bl = -y_cv

    coords = np.stack([x_bl, y_bl, z_bl], axis=1)
    colors = color[grid_y[valid], grid_x[valid]]
    depth_attr = z_mm_v
    return coords, colors, depth_attr


# Cached from last rebuild — avoids reading 100k+ verts back in Python.
_last_coords = None


def _set_float_color_attribute(mesh, name: str, colors) -> None:
    import numpy as np

    n = len(colors)
    if name in mesh.attributes:
        attr = mesh.attributes[name]
        if len(attr.data) != n:
            mesh.attributes.remove(attr)
            attr = None
    else:
        attr = None
    if attr is None:
        mesh.attributes.new(name=name, type="FLOAT_COLOR", domain="POINT")

    # Kinect PNGs are sRGB-encoded. A FLOAT_COLOR attribute is interpreted as
    # linear, so decode sRGB -> linear here; otherwise Emission + the display
    # transform push everything bright and desaturated (looks washed-out grey).
    srgb = np.asarray(colors, dtype=np.float32) / 255.0
    linear = np.where(
        srgb <= 0.04045,
        srgb / 12.92,
        ((srgb + 0.055) / 1.055) ** 2.4,
    ).astype(np.float32)

    rgba = np.ones((n, 4), dtype=np.float32)
    rgba[:, :3] = linear
    mesh.attributes[name].data.foreach_set("color", rgba.ravel())

    # Make Cd the active/render color so Solid-mode "Color: Attribute" shows it too.
    try:
        mesh.color_attributes.active_color_name = name
        mesh.color_attributes.render_color_index = mesh.color_attributes.find(name)
    except Exception:
        pass


def _set_float_attribute(mesh, name: str, values) -> None:
    import numpy as np

    n = len(values)
    if name in mesh.attributes:
        attr = mesh.attributes[name]
        if len(attr.data) != n:
            mesh.attributes.remove(attr)
            attr = None
    else:
        attr = None
    if attr is None:
        mesh.attributes.new(name=name, type="FLOAT", domain="POINT")
    mesh.attributes[name].data.foreach_set("value", np.asarray(values, dtype=np.float32))


def _rebuild_from_cache(context: bpy.types.Context) -> bool:
    """Fast playback path: stream pre-baked arrays; no decode/unproject."""
    global _last_coords
    from . import bake

    cache = bake.get_active_cache()
    if cache is None:
        return False

    scene = context.scene
    settings = scene.kinect_take
    data = cache.frame(scene.frame_current)
    if data is None:
        return False

    coords, colors, depth_attr = data
    cloud_data, cloud_render = scene_setup.ensure_scene_layout(scene)
    _last_coords = coords
    _write_mesh_from_arrays(cloud_data, coords, colors, depth_attr, settings)

    if not settings.data_only:
        if default_render.has_default_render(cloud_render):
            default_render.sync_render_point_size(cloud_render, settings.point_size)
        else:
            default_render.setup_default_cloud_render(cloud_render, cloud_data, settings.point_size)
        default_render.ensure_render_material(cloud_render)
        default_render.ensure_set_material_node(cloud_render)
    else:
        cloud_data.display_type = "WIRE"
        cloud_data.hide_viewport = False
        cloud_data.hide_render = True
        cloud_render.hide_viewport = True

    settings.status_message = (
        f"Frame {scene.frame_current}/{settings.frame_count} — "
        f"{len(coords):,} points (baked)"
    )
    return True


def rebuild_cloud_data(context: bpy.types.Context) -> None:
    global _last_coords
    scene = context.scene
    settings = scene.kinect_take
    take_dir = _take_path(settings)
    if take_dir is None or not take_dir.is_dir():
        settings.status_message = "No take loaded"
        return

    if settings.use_baked_cache and _rebuild_from_cache(context):
        return

    import numpy as np

    meta = get_take_metadata(take_dir)
    frame = scene.frame_current
    cloud_data, cloud_render = scene_setup.ensure_scene_layout(scene)

    try:
        depth_data, color_data, w, h = load_frame_data(meta, frame)
        intrinsics = scaled_intrinsics(
            meta["calibration"]["color"], w, h, settings.width_scale
        )
        coords, colors, depth_attr = _unproject_numpy(
            depth_data, color_data, intrinsics,
            settings.subsample, settings.near_mm, settings.far_mm,
        )
    except (FileNotFoundError, RuntimeError):
        coords = np.zeros((0, 3), dtype=np.float32)
        colors = np.zeros((0, 3), dtype=np.uint8)
        depth_attr = np.zeros((0,), dtype=np.float32)
    _last_coords = coords
    _write_mesh_from_arrays(cloud_data, coords, colors, depth_attr, settings)

    if not settings.data_only:
        if default_render.has_default_render(cloud_render):
            default_render.sync_render_point_size(cloud_render, settings.point_size)
        else:
            default_render.setup_default_cloud_render(
                cloud_render, cloud_data, settings.point_size
            )
        default_render.ensure_render_material(cloud_render)
        default_render.ensure_set_material_node(cloud_render)
    else:
        cloud_data.display_type = "WIRE"
        cloud_data.hide_viewport = False
        cloud_data.hide_render = True
        cloud_render.hide_viewport = True

    point_count = len(cloud_data.data.vertices)
    settings.status_message = f"Frame {frame}/{settings.frame_count} — {point_count:,} points"


def _write_mesh_from_arrays(obj, coords, colors, depth_attr, settings) -> None:
    import numpy as np

    mesh = obj.data
    n = len(coords)
    if n == 0:
        mesh.clear_geometry()
        mesh.update()
        return

    coords_flat = np.asarray(coords, dtype=np.float64).ravel()
    if len(mesh.vertices) != n:
        mesh.clear_geometry()
        mesh.vertices.add(n)
    mesh.vertices.foreach_set("co", coords_flat)
    _set_float_color_attribute(mesh, "Cd", colors)
    _set_float_attribute(mesh, ATTR_DEPTH_MM, depth_attr)
    mesh.update()


def _apply_preview_display(obj: bpy.types.Object, settings) -> None:
    # Display is handled in rebuild_cloud_data after write (CloudRender GN or data-only wire).
    pass


def apply_timeline_from_manifest(settings, manifest: dict, scene: bpy.types.Scene) -> None:
    frame_count = int(manifest.get("frame_count", 1))
    fps = float(manifest.get("fps", 30))

    settings.frame_count = frame_count
    settings.loaded_take_name = manifest.get("source_filename", "")

    scene.frame_start = 1
    scene.frame_end = max(1, frame_count)
    scene.render.fps = int(fps)


def _default_subsample_for_resolution(width: int, height: int) -> int:
    pixels = width * height
    if pixels >= 2560 * 1440:
        return 12
    if pixels >= 1920 * 1080:
        return 8
    if pixels >= 1280 * 720:
        return 4
    return 3


def load_take(context: bpy.types.Context) -> None:
    settings = context.scene.kinect_take
    take_dir = _take_path(settings)
    if take_dir is None or not take_dir.is_dir():
        raise FileNotFoundError("Choose a valid take folder")

    scene = context.scene
    scene["kinect_loading_take"] = True
    try:
        clear_take_cache()
        purge_stale_datablocks()
        meta = read_take_metadata(take_dir)
        validate_take_frames(meta)
        settings.take_path = str(take_dir.resolve())
        apply_timeline_from_manifest(settings, meta["manifest"], scene)

        depth_data, color_data, w, h = load_frame_data(meta, scene.frame_current)
        settings.subsample = _default_subsample_for_resolution(w, h)
        settings.near_mm = 600.0
        settings.far_mm = 6000.0
        settings.point_size = 0.5
        settings.width_scale = 1.0

        from . import bake

        frame_count = take_frame_count(meta)
        if bake.is_cache_valid(take_dir, settings, frame_count):
            bake.attach_cache(take_dir)
            settings.bake_status = "Baked cache loaded — playback is fast"
        else:
            bake.detach_cache()
            if bake.read_manifest(take_dir) is not None:
                settings.bake_status = "Cache is stale (params changed) — re-bake"
            else:
                settings.bake_status = "Not baked — click Bake Take for fast playback"

        scene_setup.ensure_scene_layout(scene)
        rebuild_cloud_data(context)
        frame_to_cloud(context)
    finally:
        scene.pop("kinect_loading_take", None)


def frame_to_cloud(context: bpy.types.Context) -> None:
    settings = context.scene.kinect_take
    import numpy as np

    coords = _last_coords
    if coords is None or len(coords) == 0:
        obj = scene_setup.get_cloud_data()
        if obj is None or len(obj.data.vertices) == 0:
            return
        coords = np.array([v.co for v in obj.data.vertices])

    centroid = coords.mean(axis=0)
    settings.orbit_pivot_x = float(centroid[0])
    settings.orbit_pivot_y = float(centroid[1])
    settings.orbit_pivot_z = float(centroid[2])

    extent = np.linalg.norm(coords - centroid, axis=1).max()
    settings.orbit_distance = max(1.5, float(extent) * 2.5)
    scene_setup.apply_orbit_camera(settings)
