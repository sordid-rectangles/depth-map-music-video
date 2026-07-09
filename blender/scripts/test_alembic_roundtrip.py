"""De-risk the bake architecture: does Blender 4.2 round-trip a vertex-only
point mesh + POINT-domain FLOAT_COLOR 'Cd' through Alembic and back via
Mesh Sequence Cache, with varying point count per frame?

Run: blender --background --python test_alembic_roundtrip.py
"""
import os
import tempfile

import bpy
import numpy as np

OUT = os.path.join(tempfile.gettempdir(), "kinect_abc_test.abc")


def make_points(obj_name, n, zoff):
    mesh = bpy.data.meshes.new(obj_name)
    obj = bpy.data.objects.new(obj_name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    rng = np.random.default_rng(0)
    coords = rng.random((n, 3)).astype(np.float64)
    coords[:, 2] += zoff
    mesh.vertices.add(n)
    mesh.vertices.foreach_set("co", coords.ravel())
    mesh.attributes.new(name="Cd", type="FLOAT_COLOR", domain="POINT")
    rgba = np.ones((n, 4), dtype=np.float32)
    rgba[:, 0] = np.linspace(0, 1, n)
    mesh.attributes["Cd"].data.foreach_set("color", rgba.ravel())
    mesh.update()
    return obj


def bake_frames(obj):
    """Vary vertex count + positions per frame via a frame_change handler."""
    counts = {1: 500, 2: 750, 3: 600}

    def handler(scene, _dg):
        f = scene.frame_current
        n = counts.get(f, 500)
        mesh = obj.data
        mesh.clear_geometry()
        rng = np.random.default_rng(f)
        coords = rng.random((n, 3)).astype(np.float64)
        coords[:, 2] += f
        mesh.vertices.add(n)
        mesh.vertices.foreach_set("co", coords.ravel())
        mesh.attributes.new(name="Cd", type="FLOAT_COLOR", domain="POINT")
        rgba = np.ones((n, 4), dtype=np.float32)
        rgba[:, 0] = np.linspace(0, 1, n)
        mesh.attributes["Cd"].data.foreach_set("color", rgba.ravel())
        mesh.update()

    bpy.app.handlers.frame_change_post.append(handler)
    return handler, counts


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 3

    obj = make_points("BakeSrc", 500, 0)
    handler, counts = bake_frames(obj)

    print("=== EXPORT ===")
    try:
        bpy.ops.wm.alembic_export(
            filepath=OUT,
            start=1,
            end=3,
            selected=False,
            flatten=False,
            export_custom_properties=True,
            evaluation_mode="RENDER",
        )
        print("export ok:", OUT, "exists", os.path.isfile(OUT))
    except Exception as exc:
        print("EXPORT FAIL:", exc)
        return

    bpy.app.handlers.frame_change_post.remove(handler)

    print("=== REIMPORT via Mesh Sequence Cache ===")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 3

    mesh = bpy.data.meshes.new("Playback")
    pobj = bpy.data.objects.new("Playback", mesh)
    scene.collection.objects.link(pobj)

    mod = pobj.modifiers.new("MeshSeq", "MESH_SEQUENCE_CACHE")
    bpy.ops.cachefile.open(filepath=OUT)
    cache_file = bpy.data.cache_files[-1]
    mod.cache_file = cache_file

    object_paths = [o.path for o in cache_file.object_paths]
    print("alembic object paths:", object_paths)
    mesh_paths = [p for p in object_paths if p.lower().rstrip("/").endswith("bakesrc") or "Bake" in p]
    mod.object_path = mesh_paths[0] if mesh_paths else (object_paths[0] if object_paths else "")
    print("using object_path:", mod.object_path)

    dg = bpy.context.evaluated_depsgraph_get()
    for f in (1, 2, 3):
        scene.frame_set(f)
        dg.update()
        ev = pobj.evaluated_get(dg)
        m = ev.data
        attr_names = [a.name for a in m.attributes]
        has_cd = "Cd" in attr_names
        cd_domain = m.attributes["Cd"].domain if has_cd else "-"
        cd_type = m.attributes["Cd"].data_type if has_cd else "-"
        print(
            f"frame {f}: verts={len(m.vertices)} (expected {counts[f]}) "
            f"attrs={attr_names} Cd={has_cd} domain={cd_domain} type={cd_type}"
        )
        if has_cd and len(m.attributes["Cd"].data) > 0:
            first = m.attributes["Cd"].data[0].color[:]
            print(f"          Cd[0]={tuple(round(c,3) for c in first)}")

    print("DONE")


main()
