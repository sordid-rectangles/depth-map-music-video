"""Verify the bake -> memmap -> playback path end to end.

Bakes the first N frames of the real take, plays them back from the cache
measuring write fps, and checks baked frame 1 matches a live unproject.

Run: blender --background --python test_bake_playback.py
"""
import sys
import time
from pathlib import Path

for n in list(sys.modules):
    if n.startswith("kinect_pointcloud"):
        del sys.modules[n]

sys.path.insert(0, r"C:\Users\bonk\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons")

import bpy
import numpy as np

bpy.ops.wm.read_factory_settings(use_empty=True)

import kinect_pointcloud as addon
from kinect_pointcloud import bake, import_take

addon.register()

TAKE = Path(r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614")
N = 30

scene = bpy.context.scene
settings = scene.kinect_take
settings.take_path = str(TAKE)
import_take.load_take(bpy.context)

# Force a small frame_count for the test bake.
settings.frame_count = N
settings.subsample = 8

print("build", addon.ADDON_BUILD)

t0 = time.perf_counter()
bake.bake_all(TAKE, settings, N)
bake_dt = time.perf_counter() - t0
print(f"bake {N} frames took {bake_dt:.2f}s ({bake_dt / N * 1000:.1f} ms/frame decode+unproject)")

manifest = bake.read_manifest(TAKE)
print("cache valid:", bake.is_cache_valid(TAKE, settings, N))
print("total points:", manifest["total_points"], "params:", manifest["params"])

# Parity check: baked frame 1 vs live unproject frame 1.
cache = bake.attach_cache(TAKE)
pos_b, col_b, dep_b = cache.frame(1)

meta = import_take.read_take_metadata(TAKE)
depth, color, w, h = import_take.load_frame_arrays(meta, 1)
intr = import_take.scaled_intrinsics(meta["calibration"]["color"], w, h, settings.width_scale)
pos_l, col_l, dep_l = import_take._unproject_numpy(
    depth, color, intr, settings.subsample, settings.near_mm, settings.far_mm
)
print("frame1 baked pts:", len(pos_b), "live pts:", len(pos_l))
print("pos match:", np.allclose(pos_b, pos_l.astype(np.float32), atol=1e-4))
print("col match:", np.array_equal(col_b, col_l.astype(np.uint8)))

# Playback fps: stream cache + write mesh for frames 1..N.
settings.use_baked_cache = True
t0 = time.perf_counter()
for f in range(1, N + 1):
    scene.frame_set(f)
dt = (time.perf_counter() - t0) / N * 1000.0
print(f"playback (cache read + mesh write + frame_set): {dt:.2f} ms/frame ({1000 / dt:.1f} fps)")
print("final verts:", len(bpy.data.objects["CloudData"].data.vertices))
print("DONE")
