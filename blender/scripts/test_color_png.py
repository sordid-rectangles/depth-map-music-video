import bpy
from pathlib import Path

bpy.ops.wm.read_factory_settings(use_empty=True)
path = Path(r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614\color\frame_000001.png")
fp = str(path).replace("\\", "/")
print("fp", fp, "exists", path.is_file())

img = bpy.data.images.load(fp, check_existing=False)
print("loaded", img.name, img.size, img.has_data, img.source, img.filepath)
img.update()
print("after update", img.has_data, img.size, len(img.pixels))
