import sys
from pathlib import Path
sys.path.insert(0, r"C:\Users\bonk\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons")
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)

fp = Path(r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614\color\frame_000001.png").as_posix()
img = bpy.data.images.load(fp, check_existing=False)
img.source = "SEQUENCE"
mat = bpy.data.materials.new("t")
mat.use_nodes = True
tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = img
user = tex.image_user
user.frame_start = 1
user.frame_duration = 5005

for fc in (1, 142, 1000):
    user.frame_current = fc
    r = img.filepath_from_user(image_user=user)
    if r.startswith("//"):
        r = bpy.path.abspath(r)
    img.reload()
    img.update()
    ok = img.size[0] > 0
    print(f"cur={fc} -> {Path(r).name} ok={ok} size={tuple(img.size)}")
