import sys
from pathlib import Path
for n in list(sys.modules):
    if n.startswith("kinect_pointcloud"):
        del sys.modules[n]
sys.path.insert(0, r"C:\Users\bonk\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons")
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
import kinect_pointcloud as addon
from kinect_pointcloud import color_io, import_take
addon.register()
TAKE = Path(r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614")
bpy.context.scene.kinect_take.take_path = str(TAKE)
import_take.load_take(bpy.context)
print("build", addon.ADDON_BUILD)
print("verts", len(bpy.data.objects["CloudData"].data.vertices))
print("LOAD OK")
