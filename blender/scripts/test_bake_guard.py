"""Verify authoritative frame count + bake preflight guard.

Run: blender --background --python test_bake_guard.py
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
from kinect_pointcloud import bake, import_take

addon.register()

TAKE = Path(r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614")

scene = bpy.context.scene
settings = scene.kinect_take

# Deliberately corrupt frame_count before load to prove load fixes it.
settings.frame_count = 1
settings.take_path = str(TAKE)
import_take.load_take(bpy.context)

meta = import_take.read_take_metadata(TAKE)
authoritative = import_take.take_frame_count(meta)
print("manifest frame_count:", authoritative)
print("settings.frame_count after load:", settings.frame_count)
assert settings.frame_count == authoritative == 5005, "frame_count not authoritative"

# Preflight at the loaded (sane) subsample: should be OK, and NOT tiny.
est = bake.estimate_bake(TAKE, settings, authoritative)
print("subsample", settings.subsample, "-> pts/frame", est["points_per_frame"],
      "est GB", round(est["est_bytes"] / 1e9, 2), "ok", est["ok"])
assert est["frame_count"] == 5005
assert est["ok"] is True

# Preflight at subsample=1: full-res * 5005 frames must be refused as runaway.
settings.subsample = 1
est1 = bake.estimate_bake(TAKE, settings, authoritative)
print("subsample 1 -> pts/frame", est1["points_per_frame"],
      "est GB", round(est1["est_bytes"] / 1e9, 2), "ok", est1["ok"], "|", est1["reason"])
assert est1["ok"] is False, "runaway bake was not refused"

print("GUARD OK")
