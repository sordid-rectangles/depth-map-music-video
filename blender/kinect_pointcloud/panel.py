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

        layout.prop(settings, "take_path", text="Take")
        row = layout.row(align=True)
        row.scale_y = 1.4
        row.operator("kinect.load_take", text="Load Take", icon="FILE_FOLDER")
        row.operator("kinect.reload_take", text="", icon="FILE_REFRESH")

        if settings.loaded_take_name:
            box = layout.box()
            box.label(text=settings.loaded_take_name, icon="SEQUENCE")
            box.label(text=f"{settings.frame_count} frames")
        else:
            layout.label(text="Pick the take folder (has calibration.json)", icon=compat.ICON_INFO)

        if settings.status_message:
            layout.label(text=settings.status_message, icon=compat.ICON_INFO)


class KINECT_PT_cloud(bpy.types.Panel):
    bl_label = "Shape"
    bl_idname = "KINECT_PT_cloud"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kinect"
    bl_parent_id = "KINECT_PT_main"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.kinect_take

        col = layout.column()
        col.prop(settings, "subsample")
        col.prop(settings, "near_mm")
        col.prop(settings, "far_mm")
        col.prop(settings, "point_size")

        layout.separator()
        layout.operator("kinect.reset_default_render", text="Reset Look", icon="LOOP_BACK")
        layout.label(text="Style the look on CloudRender", icon=compat.ICON_NODE)
        layout.label(text="(its Geometry Nodes modifier).")


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

        col = layout.column()
        col.scale_y = 1.4
        col.operator("kinect.bake_take", text="Bake Take", icon="RENDER_ANIMATION")
        if settings.bake_status:
            layout.label(text=settings.bake_status, icon=compat.ICON_INFO)

        layout.prop(settings, "use_baked_cache")
        layout.prop(settings, "update_on_frame_change")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Bake once — then playback is smooth.")
        col.label(text="Re-bake if you change values above.")


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

        layout.prop(settings, "camera_mode", text="")
        if settings.camera_mode != "ORBIT":
            layout.label(text="Add and animate your own camera", icon=compat.ICON_CAMERA)
            return

        col = layout.column()
        col.scale_y = 1.4
        col.operator("kinect.look_through_orbit", text="Look Through Orbit Cam", icon="CAMERA_DATA")

        layout.prop(settings, "orbit_distance")
        layout.prop(settings, "orbit_azimuth")
        layout.prop(settings, "orbit_elevation")
        layout.label(text="Drag the sliders to orbit live", icon=compat.ICON_INFO)

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Orbit Center (shift framing)")
        col.prop(settings, "orbit_pivot_x", text="X")
        col.prop(settings, "orbit_pivot_y", text="Y")
        col.prop(settings, "orbit_pivot_z", text="Z")
        layout.operator("kinect.frame_to_cloud", text="Recenter on Cloud", icon="VIEWZOOM")


class KINECT_PT_advanced(bpy.types.Panel):
    bl_label = "Advanced"
    bl_idname = "KINECT_PT_advanced"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kinect"
    bl_parent_id = "KINECT_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.kinect_take

        layout.prop(settings, "auto_rebuild")
        layout.operator("kinect.rebuild_cloud", text="Rebuild Now", icon="MESH_ICOSPHERE")
        layout.prop(settings, "width_scale")

        layout.prop(settings, "data_only")
        if settings.data_only:
            layout.label(text="Showing raw CloudData wireframe", icon=compat.ICON_INFO)

        try:
            from . import ADDON_BUILD, bl_info

            ver = ".".join(str(v) for v in bl_info["version"])
            layout.separator()
            layout.label(text=f"v{ver}  ({ADDON_BUILD})", icon=compat.ICON_INFO)
        except Exception:
            pass
