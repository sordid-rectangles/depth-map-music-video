import sys
from pathlib import Path
sys.path.insert(0, r"C:\Users\bonk\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons")
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
import kinect_pointcloud.color_io as color_io
import kinect_pointcloud.import_take as import_take

TAKE = Path(r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614")
meta = import_take.read_take_metadata(TAKE)
img = None
try:
    color_io.register_color_sequence(meta["color_dir"] / "frame_000001.png", 5005, 1)
    img = bpy.data.images["kinect_color_seq"]
    user = color_io._ensure_image_user(img)
    for frame in (1, 142, 1000):
        user.frame_current = frame
        r = img.filepath_from_user(image_user=user)
        if r.startswith("//"):
            r = bpy.path.abspath(r)
        print(f"frame {frame} -> {Path(r).name} exists={Path(r).is_file()}")
    print("PATH OK")
except RuntimeError as e:
    print("FAIL", e)
