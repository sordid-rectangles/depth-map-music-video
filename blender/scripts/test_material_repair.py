"""Simulate an old material-less CloudRender and confirm rebuild repairs it.

Run: blender --background --python test_material_repair.py
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
from kinect_pointcloud import import_take, scene_setup, default_render

addon.register()

TAKE = Path(r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614")
scene = bpy.context.scene
settings = scene.kinect_take
settings.take_path = str(TAKE)
import_take.load_take(bpy.context)

cr = scene_setup.get_cloud_render()
print("after load, slot0:", cr.material_slots[0].material.name if cr.material_slots and cr.material_slots[0].material else None)

# Simulate the broken state: strip all materials off CloudRender.
cr.data.materials.clear()
print("stripped materials:", [m.name for m in cr.data.materials])

# A normal rebuild (as happens on scrub / reload) should repair it.
import_take.rebuild_cloud_data(bpy.context)
mat = cr.material_slots[0].material if cr.material_slots else None
print("after rebuild, slot0:", mat.name if mat else None)
assert mat is not None and mat.name == default_render.MATERIAL_NAME, "material not repaired"

# Confirm the material is an emission shader reading Cd.
nodes = mat.node_tree.nodes
kinds = {n.bl_idname for n in nodes}
attr = next((n for n in nodes if n.bl_idname == "ShaderNodeAttribute"), None)
print("has emission:", "ShaderNodeEmission" in kinds, "| attr:", attr.attribute_name if attr else None)
assert "ShaderNodeEmission" in kinds and attr and attr.attribute_name == "Cd"

print("REPAIR OK")
