import sys
from pathlib import Path
sys.path.insert(0, r"C:\Users\bonk\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons")
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)

TAKE = Path(r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614\color\frame_000001.png")
fp = TAKE.as_posix()
img = bpy.data.images.load(fp, check_existing=False)
img.source = "SEQUENCE"

mat = bpy.data.materials.new("t")
mat.use_nodes = True
tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = img
user = tex.image_user
user.frame_duration = 5005

for fs in (0, 1):
    for fo in (0, 1):
        for fc in (0, 1, 2):
            user.frame_start = fs
            user.frame_offset = fo
            user.frame_current = fc
            r = img.filepath_from_user(image_user=user)
            if r.startswith("//"):
                r = bpy.path.abspath(r)
            ok = Path(r).is_file()
            print(f"start={fs} off={fo} cur={fc} -> {Path(r).name} ok={ok}")
