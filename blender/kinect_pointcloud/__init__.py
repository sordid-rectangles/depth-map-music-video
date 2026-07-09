bl_info = {
    "name": "Kinect Point Cloud",
    "author": "depth-map-music-video",
    "version": (0, 3, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Kinect",
    "description": "Load Kinect depth takes as timed point clouds for stylized rendering",
    "category": "Import-Export",
}

# Shown in the sidebar so you can confirm Blender loaded this build after install.
ADDON_BUILD = "2026-07-09-purge-stale"

import bpy

from . import handlers, operators, panel, properties


classes = (
    properties.KinectTakeSettings,
    operators.KINECT_OT_load_take,
    operators.KINECT_OT_reload_take,
    operators.KINECT_OT_rebuild_cloud,
    operators.KINECT_OT_frame_to_cloud,
    operators.KINECT_OT_look_through_orbit,
    operators.KINECT_OT_bake_take,
    operators.KINECT_OT_reset_default_render,
    panel.KINECT_PT_main,
    panel.KINECT_PT_cloud,
    panel.KINECT_PT_playback,
    panel.KINECT_PT_camera,
    panel.KINECT_PT_advanced,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.kinect_take = bpy.props.PointerProperty(type=properties.KinectTakeSettings)
    handlers.register()


def unregister():
    handlers.unregister()
    del bpy.types.Scene.kinect_take
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
