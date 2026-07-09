"""Verify stale-datablock purge (the reboot-lag cause) works.

Recreates the old-build artifacts (kinect_color_seq SEQUENCE image with
use_auto_refresh + helper material), then checks purge + load_take remove them.

Run: blender --background --python test_purge_stale.py
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
from kinect_pointcloud import import_take

addon.register()

TAKE = Path(r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614")
first_png = TAKE / "color" / "frame_000001.png"


def make_stale():
    img = bpy.data.images.load(str(first_png), check_existing=False)
    img.name = "kinect_color_seq"
    img.source = "SEQUENCE"
    mat = bpy.data.materials.new("_KinectColorSeqHelper")
    mat.use_nodes = True
    tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.image_user.use_auto_refresh = True
    tex.image_user.frame_duration = 5005


make_stale()
print("before purge: images", [i.name for i in bpy.data.images],
      "| mats", [m.name for m in bpy.data.materials])
assert bpy.data.images.get("kinect_color_seq") is not None

removed = import_take.purge_stale_datablocks()
print("purge removed:", removed)
print("after purge: images", [i.name for i in bpy.data.images],
      "| mats", [m.name for m in bpy.data.materials])
assert bpy.data.images.get("kinect_color_seq") is None
assert bpy.data.materials.get("_KinectColorSeqHelper") is None

# Recreate, then confirm load_take also purges as part of loading.
make_stale()
scene = bpy.context.scene
scene.kinect_take.take_path = str(TAKE)
import_take.load_take(bpy.context)
print("after load_take: seq image present?",
      bpy.data.images.get("kinect_color_seq") is not None)
assert bpy.data.images.get("kinect_color_seq") is None

# Confirm the load_post handler is registered.
from kinect_pointcloud import handlers
print("load_post registered:", handlers._on_load_post in bpy.app.handlers.load_post)
assert handlers._on_load_post in bpy.app.handlers.load_post

print("PURGE OK")
