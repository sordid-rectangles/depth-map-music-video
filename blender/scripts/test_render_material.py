"""Diagnose why CloudRender points show grey (no color).

Loads the take, rebuilds frame 1, evaluates CloudRender, and reports:
- material slots on the object/mesh
- the default GN node tree contents
- whether the EVALUATED geometry carries the 'Cd' color attribute + a material

Run: blender --background --python test_render_material.py
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

cr = scene_setup.get_cloud_render()
cd = scene_setup.get_cloud_data()
print("BUILD", addon.ADDON_BUILD)
print("CloudRender:", cr.name if cr else None)
print("object material slots:", [ (s.link, s.material.name if s.material else None) for s in cr.material_slots ])
print("mesh materials:", [m.name if m else None for m in cr.data.materials])

mod = cr.modifiers.get("KinectDefaultRender")
print("modifier:", mod.type if mod else None, "tree:", mod.node_group.name if mod and mod.node_group else None)
if mod and mod.node_group:
    print("nodes:", [n.bl_idname for n in mod.node_group.nodes])

# CloudData color attribute present?
print("CloudData attrs:", [a.name for a in cd.data.attributes])

print("CloudData verts:", len(cd.data.vertices))

# Append Points->Vertices so to_mesh() can reveal whether Cd propagates through
# Mesh to Points into the rendered point cloud.
tree = mod.node_group
nodes = tree.nodes
links = tree.links
out = next(n for n in nodes if n.bl_idname == "NodeGroupOutput")
m2p = next(n for n in nodes if n.bl_idname == "GeometryNodeMeshToPoints")
p2v = nodes.new("GeometryNodePointsToVertices")
# rewire m2p -> p2v -> output
for l in list(links):
    if l.from_node == m2p and l.to_node == out:
        links.remove(l)
links.new(m2p.outputs["Points"], p2v.inputs["Points"])
links.new(p2v.outputs["Mesh"], out.inputs["Geometry"])

deps = bpy.context.evaluated_depsgraph_get()
cr_eval = cr.evaluated_get(deps)
me = cr_eval.to_mesh()
print("EVAL vert count:", len(me.vertices))
print("EVAL attrs:", [(a.name, a.domain, a.data_type) for a in me.attributes])
has_cd = "Cd" in me.attributes
print("EVAL has Cd:", has_cd)
if has_cd and len(me.vertices) > 0:
    d = me.attributes["Cd"].data[0]
    print("EVAL Cd[0]:", tuple(round(c, 3) for c in d.color))
cr_eval.to_mesh_clear()

import numpy as np

n = len(cd.data.vertices)
buf = np.empty(n * 4, dtype=np.float32)
cd.data.attributes["Cd"].data.foreach_get("color", buf)
rgb = buf.reshape(n, 4)[:, :3]
mx = rgb.max(axis=1)
mn = rgb.min(axis=1)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
print("Cd mean rgb:", tuple(round(float(x), 3) for x in rgb.mean(axis=0)))
print("Cd value(max-channel) mean:", round(float(mx.mean()), 3))
print("Cd saturation mean:", round(float(sat.mean()), 3),
      "| frac sat>0.2:", round(float((sat > 0.2).mean()), 3))

print("DONE")
