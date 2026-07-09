"""Render the point cloud headlessly and measure output color.

Verifies (1) the default GN stack now renders the Cd color, and (2) the
auto-repair inserts Set Material into an old-style stack that lacks it.

Run: blender --background --python test_eevee_render.py
"""
import sys
from pathlib import Path

for n in list(sys.modules):
    if n.startswith("kinect_pointcloud"):
        del sys.modules[n]

sys.path.insert(0, r"C:\Users\bonk\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons")

import bpy
import numpy as np

bpy.ops.wm.read_factory_settings(use_empty=True)

import kinect_pointcloud as addon
from kinect_pointcloud import import_take, scene_setup, default_render

addon.register()

TAKE = Path(r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614")
scene = bpy.context.scene
settings = scene.kinect_take
settings.take_path = str(TAKE)
import_take.load_take(bpy.context)

bpy.ops.kinect.look_through_orbit()
cam = bpy.data.objects.get(scene_setup.OBJ_ORBIT_CAM)
scene.camera = cam
try:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
except Exception:
    scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 320
scene.render.resolution_y = 200
scene.render.image_settings.file_format = "PNG"

cr = scene_setup.get_cloud_render()


def render_stats(tag):
    out = str(Path(bpy.app.tempdir) / f"kinect_{tag}.png")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(out, check_existing=False)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)
    rgb = px[:, :3]
    lum = rgb.mean(axis=1)
    fg = rgb[lum > 0.02]
    if len(fg) == 0:
        print(tag, "-> no foreground pixels (GREY/BLACK, broken)")
        bpy.data.images.remove(img)
        return False
    mx = fg.max(axis=1); mn = fg.min(axis=1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    print(f"{tag} -> fg px {len(fg)} | mean rgb {tuple(round(float(x),3) for x in fg.mean(axis=0))} "
          f"| sat mean {round(float(sat.mean()),3)} | frac sat>0.15 {round(float((sat>0.15).mean()),3)}")
    bpy.data.images.remove(img)
    return float(sat.mean()) > 0.2


def has_setmat():
    mod = cr.modifiers.get(default_render.MODIFIER_NAME)
    return any(n.bl_idname == "GeometryNodeSetMaterial" for n in mod.node_group.nodes)


print("=== fresh default stack ===")
print("has Set Material node:", has_setmat())
ok_default = render_stats("default")

# Simulate old-style stack: remove Set Material, then run repair.
mod = cr.modifiers.get(default_render.MODIFIER_NAME)
tree = mod.node_group
sm = next((n for n in tree.nodes if n.bl_idname == "GeometryNodeSetMaterial"), None)
m2p = next(n for n in tree.nodes if n.bl_idname == "GeometryNodeMeshToPoints")
out = next(n for n in tree.nodes if n.bl_idname == "NodeGroupOutput")
if sm:
    tree.nodes.remove(sm)
    tree.links.new(m2p.outputs["Points"], out.inputs["Geometry"])
print("=== after stripping Set Material (old-style) ===")
print("has Set Material node:", has_setmat())
ok_stripped = render_stats("stripped")

default_render.ensure_set_material_node(cr)
print("=== after ensure_set_material_node repair ===")
print("has Set Material node:", has_setmat())
ok_repaired = render_stats("repaired")

print("RESULT default_ok:", ok_default, "stripped_broken:", not ok_stripped, "repaired_ok:", ok_repaired)
print("DONE")
