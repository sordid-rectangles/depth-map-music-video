"""Ensure KINECT / CloudData / CloudRender / Cameras layout."""

from __future__ import annotations

import bpy

COLLECTION_ROOT = "KINECT"
OBJ_CLOUD_DATA = "CloudData"
OBJ_CLOUD_RENDER = "CloudRender"
COL_CAMERAS = "Cameras"
OBJ_ORBIT_CAM = "Orbit"
OBJ_ORBIT_PIVOT = "OrbitPivot"


def _ensure_collection(parent: bpy.types.Collection | None, name: str) -> bpy.types.Collection:
    if parent is None:
        coll = bpy.data.collections.get(name)
        if coll is None:
            coll = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(coll)
        return coll

    for child in parent.children:
        if child.name == name:
            return child
    coll = bpy.data.collections.new(name)
    parent.children.link(coll)
    return coll


def _ensure_object_in_collection(
    name: str,
    collection: bpy.types.Collection,
    factory,
) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = factory(name)
        collection.objects.link(obj)
    elif obj.name not in collection.objects:
        collection.objects.link(obj)
    return obj


def _make_mesh_object(name: str) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    return bpy.data.objects.new(name, mesh)


def _make_camera_object(name: str) -> bpy.types.Object:
    cam_data = bpy.data.cameras.new(name)
    return bpy.data.objects.new(name, cam_data)


def _make_empty(name: str) -> bpy.types.Object:
    return bpy.data.objects.new(name, None)


from . import default_render


def ensure_scene_layout(scene: bpy.types.Scene) -> tuple[bpy.types.Object, bpy.types.Object]:
    """Create or find CloudData and CloudRender. Returns (cloud_data, cloud_render)."""
    root = _ensure_collection(None, COLLECTION_ROOT)
    cam_coll = _ensure_collection(root, COL_CAMERAS)

    cloud_data = _ensure_object_in_collection(OBJ_CLOUD_DATA, root, _make_mesh_object)
    cloud_render = _ensure_object_in_collection(OBJ_CLOUD_RENDER, root, _make_mesh_object)

    # Starter orbit rig — artist can ignore, delete, or add FlyCam alongside.
    pivot = _ensure_object_in_collection(OBJ_ORBIT_PIVOT, cam_coll, _make_empty)
    orbit_cam = _ensure_object_in_collection(OBJ_ORBIT_CAM, cam_coll, _make_camera_object)

    if not orbit_cam.constraints:
        track = orbit_cam.constraints.new(type="TRACK_TO")
        track.target = pivot
        track.track_axis = "TRACK_NEGATIVE_Z"
        track.up_axis = "UP_Y"

    cloud_data["kinect_role"] = "cloud_data"
    cloud_render["kinect_role"] = "cloud_render"

    scene.kinect_take.status_message = "Scene layout ready"
    return cloud_data, cloud_render


def get_cloud_data() -> bpy.types.Object | None:
    obj = bpy.data.objects.get(OBJ_CLOUD_DATA)
    if obj and obj.get("kinect_role") == "cloud_data":
        return obj
    return obj


def get_cloud_render() -> bpy.types.Object | None:
    return bpy.data.objects.get(OBJ_CLOUD_RENDER)


def apply_orbit_camera(settings) -> None:
    """Position the optional Orbit camera from sidebar parms."""
    if settings.camera_mode != "ORBIT":
        return

    cam = bpy.data.objects.get(OBJ_ORBIT_CAM)
    if cam is None:
        return

    import math

    pivot = (
        settings.orbit_pivot_x,
        settings.orbit_pivot_y,
        settings.orbit_pivot_z,
    )
    az = settings.orbit_azimuth
    el = settings.orbit_elevation
    dist = settings.orbit_distance

    # Spherical offset: camera orbits pivot (Blender Z-up).
    cx = pivot[0] + dist * math.cos(el) * math.sin(az)
    cy = pivot[1] + dist * math.cos(el) * math.cos(az)
    cz = pivot[2] + dist * math.sin(el)
    cam.location = (cx, cy, cz)

    pivot_obj = bpy.data.objects.get(OBJ_ORBIT_PIVOT)
    if pivot_obj:
        pivot_obj.location = pivot
