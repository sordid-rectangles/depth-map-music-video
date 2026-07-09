"""Decision test: is a per-frame Python mesh write fast enough for smooth
playback once decode + unproject are removed (i.e. data pre-baked)?

Measures foreach_set throughput for positions + Cd color at realistic point
counts, comparing FIXED topology (reuse verts) vs VARYING (clear+add).

Run: blender --background --python test_mesh_write_perf.py
"""
import time

import bpy
import numpy as np


def bench(n, iters=60, fixed=True):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mesh = bpy.data.meshes.new("m")
    obj = bpy.data.objects.new("m", mesh)
    bpy.context.scene.collection.objects.link(obj)

    mesh.vertices.add(n)
    mesh.attributes.new(name="Cd", type="FLOAT_COLOR", domain="POINT")

    rng = np.random.default_rng(0)
    frames = [rng.random((n, 3)).astype(np.float64) for _ in range(10)]
    cols = [rng.random((n, 4)).astype(np.float32) for _ in range(10)]

    # warmup
    mesh.vertices.foreach_set("co", frames[0].ravel())
    mesh.update()

    t0 = time.perf_counter()
    for i in range(iters):
        coords = frames[i % 10]
        rgba = cols[i % 10]
        if not fixed:
            mesh.clear_geometry()
            mesh.vertices.add(n)
            mesh.attributes.new(name="Cd", type="FLOAT_COLOR", domain="POINT")
        mesh.vertices.foreach_set("co", coords.ravel())
        mesh.attributes["Cd"].data.foreach_set("color", rgba.ravel())
        mesh.update()
    dt = (time.perf_counter() - t0) / iters * 1000.0
    return dt


for n in (57000, 160000, 230000):
    f = bench(n, fixed=True)
    v = bench(n, fixed=False)
    print(
        f"n={n:>7}  fixed={f:6.2f} ms/frame ({1000/f:5.1f} fps)   "
        f"varying(clear+add)={v:6.2f} ms/frame ({1000/v:5.1f} fps)"
    )
print("DONE")
