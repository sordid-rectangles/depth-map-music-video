"""
Default CloudRender setup:

    CloudData  →  Object Info  →  Mesh to Points  →  Output

Blender 4.2 mesh objects do NOT support display_type='POINTS' (that crashes).
Points are always viewed through CloudRender's geometry nodes.
"""

from __future__ import annotations

import bpy

MODIFIER_NAME = "KinectDefaultRender"
MATERIAL_NAME = "KinectDefaultPoints"


def point_size_to_radius(point_size: float) -> float:
    return max(0.0005, point_size * 0.008)


def _ensure_default_material() -> bpy.types.Material:
    mat = bpy.data.materials.get(MATERIAL_NAME)
    if mat is not None:
        return mat

    mat = bpy.data.materials.new(MATERIAL_NAME)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = 1.0
    attr = nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Cd"
    if hasattr(attr, "attribute_type"):
        attr.attribute_type = "GEOMETRY"
    links.new(attr.outputs["Color"], emit.inputs["Color"])
    links.new(emit.outputs["Emission"], output.inputs["Surface"])
    return mat


def has_default_render(cloud_render: bpy.types.Object | None) -> bool:
    if cloud_render is None:
        return False
    mod = cloud_render.modifiers.get(MODIFIER_NAME)
    return mod is not None and mod.type == "NODES" and mod.node_group is not None


def sync_render_point_size(cloud_render: bpy.types.Object, point_size: float) -> None:
    mod = cloud_render.modifiers.get(MODIFIER_NAME)
    if mod is None or mod.node_group is None:
        return
    radius = point_size_to_radius(point_size)
    for node in mod.node_group.nodes:
        if node.bl_idname in {"GeometryNodeMeshToPoints", "GeometryNodeSetPointRadius"}:
            node.inputs["Radius"].default_value = radius


def setup_default_cloud_render(
    cloud_render: bpy.types.Object,
    cloud_data: bpy.types.Object,
    point_size: float = 0.5,
) -> None:
    if cloud_data is None or len(cloud_data.data.vertices) == 0:
        return

    if has_default_render(cloud_render):
        sync_render_point_size(cloud_render, point_size)
    else:
        tree_name = f"{cloud_render.name}_{MODIFIER_NAME}"
        tree = bpy.data.node_groups.new(tree_name, "GeometryNodeTree")
        tree.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

        nodes = tree.nodes
        links = tree.links
        nodes.clear()

        output = nodes.new("NodeGroupOutput")
        output.location = (400, 0)

        obj_info = nodes.new("GeometryNodeObjectInfo")
        obj_info.location = (-300, 0)
        obj_info.transform_space = "ORIGINAL"
        obj_info.inputs["Object"].default_value = cloud_data

        mesh_to_points = nodes.new("GeometryNodeMeshToPoints")
        mesh_to_points.location = (50, 0)
        mesh_to_points.mode = "VERTICES"
        mesh_to_points.inputs["Radius"].default_value = point_size_to_radius(point_size)
        mesh_to_points.label = "Point Size (replace me for stylized looks)"

        links.new(obj_info.outputs["Geometry"], mesh_to_points.inputs["Mesh"])
        links.new(mesh_to_points.outputs["Points"], output.inputs["Geometry"])

        mod = cloud_render.modifiers.new(MODIFIER_NAME, "NODES")
        mod.node_group = tree

    finalize_cloud_render_object(cloud_render, cloud_data)


def finalize_cloud_render_object(cloud_render: bpy.types.Object, cloud_data: bpy.types.Object) -> None:
    mat = _ensure_default_material()
    if not cloud_render.data.materials:
        cloud_render.data.materials.append(mat)
    else:
        cloud_render.material_slots[0].material = mat

    cloud_render.display_type = "SOLID"
    cloud_render.hide_viewport = False
    cloud_render.hide_render = False

    mod = cloud_render.modifiers.get(MODIFIER_NAME)
    if mod is not None:
        mod.show_viewport = True
        mod.show_render = True

    cloud_data.display_type = "WIRE"
    cloud_data.hide_viewport = True
    cloud_data.hide_render = True


def reset_default_cloud_render(cloud_render: bpy.types.Object, cloud_data: bpy.types.Object, point_size: float) -> None:
    mod = cloud_render.modifiers.get(MODIFIER_NAME)
    if mod is not None:
        old_tree = mod.node_group
        cloud_render.modifiers.remove(mod)
        if old_tree and old_tree.users == 0:
            bpy.data.node_groups.remove(old_tree)
    setup_default_cloud_render(cloud_render, cloud_data, point_size=point_size)
