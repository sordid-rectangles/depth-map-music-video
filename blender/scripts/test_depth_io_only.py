import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
depth_path = REPO / "blender" / "kinect_pointcloud" / "depth_io.py"

spec = importlib.util.spec_from_file_location("depth_io_new", depth_path)
depth_io = importlib.util.module_from_spec(spec)
spec.loader.exec_module(depth_io)

import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)

path = Path(r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614\depth_aligned\frame_000001.exr")
depth, w, h = depth_io.read_depth_exr_mm(path)
print("OK", w, h, depth.shape, float(depth.max()))
