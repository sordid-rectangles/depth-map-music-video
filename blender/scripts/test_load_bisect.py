"""Bisect load crash — run with blender --background --python test_load_bisect.py"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ADDON = REPO / "blender" / "kinect_pointcloud"
TAKE = Path(r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614")

sys.path.insert(0, str(ADDON.parent))

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)

STEP = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 0

print("=== STEP", STEP, "===")

if STEP >= 1:
    import kinect_pointcloud as addon
    addon.register()
    print("registered")

if STEP >= 2:
    from kinect_pointcloud import depth_io, import_take
    meta = import_take.read_take_metadata(TAKE)
    depth, color, w, h = import_take.load_frame_data(meta, 1)
    print("loaded frame", w, h, depth.shape)

if STEP >= 3:
    from kinect_pointcloud import import_take
    intrinsics = import_take.scaled_intrinsics(meta["calibration"]["color"], w, h, 1.0)
    coords, colors, depth_attr = import_take._unproject_numpy(depth, color, intrinsics, 8, 600, 6000)
    print("unproject", len(coords))

if STEP >= 4:
    from kinect_pointcloud import scene_setup
    cloud_data, cloud_render = scene_setup.ensure_scene_layout(bpy.context.scene)
    print("layout ok")

if STEP >= 5:
    import numpy as np
    mesh = cloud_data.data
    n = len(coords)
    mesh.clear_geometry()
    mesh.vertices.add(n)
    mesh.vertices.foreach_set("co", np.asarray(coords, dtype=np.float64).ravel())
    mesh.update()
    print("mesh verts only", n)

if STEP >= 6:
    import_take._set_float_color_attribute(mesh, "Cd", colors)
    print("Cd attr ok")

if STEP >= 7:
    import_take._set_float_attribute(mesh, "depth_mm", depth_attr)
    print("depth_mm attr ok")

if STEP >= 8:
    from kinect_pointcloud import default_render
    default_render.setup_default_cloud_render(cloud_render, cloud_data, 0.5)
    print("GN setup ok")

print("STEP", STEP, "DONE")
