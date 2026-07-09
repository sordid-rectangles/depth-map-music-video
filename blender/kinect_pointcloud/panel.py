import bpy

from . import compat


class KINECT_PT_main(bpy.types.Panel):
    bl_label = "Kinect Point Cloud"
    bl_idname = "KINECT_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kinect"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.kinect_take

        try:
            from . import ADDON_BUILD, bl_info

            layout.label(text=f"v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]} ({ADDON_BUILD})", icon=compat.ICON_INFO)
        except Exception:
            pass

        layout.prop(settings, "take_path")
        layout.label(text="Pick the take folder (contains calibration.json)", icon=compat.ICON_INFO)
        row = layout.row(align=True)
        row.operator("kinect.load_take", icon="FILE_FOLDER")
        row.operator("kinect.reload_take", icon="FILE_REFRESH")

        if settings.loaded_take_name:
            box = layout.box()
            box.label(text=f"Take: {settings.loaded_take_name}", icon="SEQUENCE")
            box.label(text=f"Frames: 1 – {settings.frame_count}")

        if settings.status_message:
            layout.label(text=settings.status_message, icon=compat.ICON_INFO)


class KINECT_PT_cloud(bpy.types.Panel):
    bl_label = "Point Cloud"
    bl_idname = "KINECT_PT_cloud"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kinect"
    bl_parent_id = "KINECT_PT_main"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.kinect_take

        layout.prop(settings, "data_only")
        if settings.data_only:
            layout.label(text="CloudData shown as wireframe for debugging", icon=compat.ICON_WIRE)
        else:
            layout.label(text="Look at CloudRender (mesh POINTS display crashes in 4.2)", icon=compat.ICON_MESH)

        layout.prop(settings, "subsample")
        layout.prop(settings, "near_mm")
        layout.prop(settings, "far_mm")
        layout.prop(settings, "point_size")

        layout.prop(settings, "auto_rebuild")
        row = layout.row(align=True)
        row.operator("kinect.rebuild_cloud", icon="MESH_ICOSPHERE")
        row.operator("kinect.reset_default_render", icon="LOOP_BACK")

        box = layout.box()
        box.label(text="Default CloudRender stack:", icon=compat.ICON_NODE)
        box.label(text="CloudData → Object Info → Mesh to Points")
        box.label(text="Swap Set Point Radius for Instance on Points, etc.")

        with layout.box():
            layout.label(text="Advanced", icon=compat.ICON_SETTINGS)
            layout.prop(settings, "width_scale")


class KINECT_PT_camera(bpy.types.Panel):
    bl_label = "Camera"
    bl_idname = "KINECT_PT_camera"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kinect"
    bl_parent_id = "KINECT_PT_main"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.kinect_take

        layout.prop(settings, "camera_mode")
        if settings.camera_mode == "ORBIT":
            layout.prop(settings, "orbit_distance")
            layout.prop(settings, "orbit_azimuth")
            layout.prop(settings, "orbit_elevation")
            col = layout.column(align=True)
            col.prop(settings, "orbit_pivot_x")
            col.prop(settings, "orbit_pivot_y")
            col.prop(settings, "orbit_pivot_z")
            layout.operator("kinect.frame_to_cloud", icon="VIEWZOOM")
        else:
            layout.label(text="Add and animate any camera", icon=compat.ICON_CAMERA)


class KINECT_PT_playback(bpy.types.Panel):
    bl_label = "Playback"
    bl_idname = "KINECT_PT_playback"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kinect"
    bl_parent_id = "KINECT_PT_main"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.kinect_take

        layout.prop(settings, "update_on_frame_change")
        layout.label(text=f"Current frame: {context.scene.frame_current}", icon=compat.ICON_TIME)
        if settings.frame_count > 1:
            box = layout.box()
            box.label(text="Playback is I/O heavy at full res.", icon=compat.ICON_INFO)
            box.label(text="Raise Subsample (12–16) for smoother scrubbing.")
