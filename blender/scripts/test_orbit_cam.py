"""Sanity-check orbit camera live update + look-through operator (headless).

Run: blender --background --python test_orbit_cam.py
"""
import sys
from pathlib import Path

for n in list(sys.modules):
    if n.startswith("kinect_pointcloud"):
        del sys.modules[n]

sys.path.insert(0, r"C:\Users\bonk\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons")

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)

import kinect_pointcloud as addon
from kinect_pointcloud import import_take, scene_setup

addon.register()

TAKE = Path(r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614")

scene = bpy.context.scene
settings = scene.kinect_take
settings.take_path = str(TAKE)
import_take.load_take(bpy.context)

cam = bpy.data.objects.get(scene_setup.OBJ_ORBIT_CAM)
print("orbit cam exists:", cam is not None)

# Live update: changing azimuth should move the camera.
loc0 = tuple(cam.location)
settings.orbit_azimuth = settings.orbit_azimuth + 1.0
loc1 = tuple(cam.location)
print("azimuth moved cam:", loc0 != loc1)
assert loc0 != loc1, "orbit sliders did not move the camera"

# Orbit center nudge: changing pivot X should shift both camera and target.
pivot_obj = bpy.data.objects.get(scene_setup.OBJ_ORBIT_PIVOT)
cam_before = tuple(cam.location)
piv_before = tuple(pivot_obj.location)
settings.orbit_pivot_x = settings.orbit_pivot_x + 0.5
print("pivot moved cam:", cam_before != tuple(cam.location),
      "| pivot obj moved:", piv_before != tuple(pivot_obj.location))
assert piv_before != tuple(pivot_obj.location), "orbit center did not shift the pivot"
assert cam_before != tuple(cam.location), "orbit center did not shift the camera"

# Look-through operator (no VIEW_3D in background, so it reports info path).
res = bpy.ops.kinect.look_through_orbit()
print("look_through result:", res)
print("scene.camera:", scene.camera.name if scene.camera else None)
assert scene.camera is cam, "orbit cam not set active"

print("ORBIT OK")
