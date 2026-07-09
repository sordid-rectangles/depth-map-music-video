import sys
from pathlib import Path

for name in list(sys.modules):
    if name.startswith("kinect_pointcloud"):
        del sys.modules[name]

sys.path.insert(0, r"C:\Users\bonk\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons")

import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)

import kinect_pointcloud as addon
from kinect_pointcloud import import_take

addon.register()
TAKE = Path(r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614")
bpy.context.scene.kinect_take.take_path = str(TAKE)
import_take.load_take(bpy.context)

import numpy as np
obj = bpy.data.objects["CloudData"]
coords = np.array([v.co for v in obj.data.vertices])
print("build", addon.ADDON_BUILD)
print("points", len(coords))
print("centroid", coords.mean(axis=0))
print("extent X", coords[:,0].ptp(), "Y", coords[:,1].ptp(), "Z", coords[:,2].ptp())
print("Y range (depth/forward)", coords[:,1].min(), coords[:,1].max())
print("Z range (height)", coords[:,2].min(), coords[:,2].max())
