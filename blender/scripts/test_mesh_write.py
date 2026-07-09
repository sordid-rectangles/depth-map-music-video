"""Headless smoke test: run with blender --background --python test_mesh_write.py"""
import site
import sys

sys.path.insert(0, site.getusersitepackages())

import bpy
import numpy as np

# Minimal scene
bpy.ops.wm.read_factory_settings(use_empty=True)
mesh = bpy.data.meshes.new("test")
obj = bpy.data.objects.new("test", mesh)
bpy.context.scene.collection.objects.link(obj)

n = 50000
coords = np.random.randn(n, 3).astype(np.float64)
colors = np.random.randint(0, 255, (n, 3), dtype=np.uint8)

mesh.clear_geometry()
mesh.vertices.add(n)
mesh.vertices.foreach_set("co", coords.ravel())

name = "Cd"
if name in mesh.attributes:
    mesh.attributes.remove(mesh.attributes[name])
mesh.attributes.new(name=name, type="FLOAT_COLOR", domain="POINT")
rgba = np.ones((n, 4), dtype=np.float32)
rgba[:, :3] = colors.astype(np.float32) / 255.0
mesh.attributes[name].data.foreach_set("color", rgba.ravel())
mesh.update()

obj.display_type = "WIRE"
print("OK", len(mesh.vertices), "verts", len(mesh.attributes[name].data))
