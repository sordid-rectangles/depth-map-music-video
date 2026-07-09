import bpy

from . import import_take, scene_setup


class KINECT_OT_load_take(bpy.types.Operator):
    bl_idname = "kinect.load_take"
    bl_label = "Load Take"
    bl_description = "Load a Kinect export folder and build CloudData"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            import_take.load_take(context)
        except Exception as exc:
            context.scene.kinect_take.status_message = str(exc)
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        self.report({"INFO"}, "Kinect take loaded")
        return {"FINISHED"}


class KINECT_OT_reload_take(bpy.types.Operator):
    bl_idname = "kinect.reload_take"
    bl_label = "Reload Take"
    bl_description = "Re-read the current take folder and rebuild CloudData"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            import_take.rebuild_cloud_data(context)
        except Exception as exc:
            context.scene.kinect_take.status_message = str(exc)
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class KINECT_OT_rebuild_cloud(bpy.types.Operator):
    bl_idname = "kinect.rebuild_cloud"
    bl_label = "Rebuild Cloud"
    bl_description = "Rebuild CloudData from current parameters and timeline frame"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            import_take.rebuild_cloud_data(context)
        except Exception as exc:
            context.scene.kinect_take.status_message = str(exc)
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class KINECT_OT_frame_to_cloud(bpy.types.Operator):
    bl_idname = "kinect.frame_to_cloud"
    bl_label = "Frame to Cloud"
    bl_description = "Set orbit pivot and distance from the current cloud (one shot)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        import_take.frame_to_cloud(context)
        scene_setup.apply_orbit_camera(context.scene.kinect_take)
        return {"FINISHED"}


class KINECT_OT_reset_default_render(bpy.types.Operator):
    bl_idname = "kinect.reset_default_render"
    bl_label = "Reset Default Render"
    bl_description = "Restore CloudRender to the simple Object Info → Set Point Radius setup"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from . import default_render

        cloud_data = scene_setup.get_cloud_data()
        cloud_render = scene_setup.get_cloud_render()
        if cloud_data is None or cloud_render is None:
            self.report({"ERROR"}, "Load a take first")
            return {"CANCELLED"}

        settings = context.scene.kinect_take
        default_render.reset_default_cloud_render(cloud_render, cloud_data, settings.point_size)
        import_take.rebuild_cloud_data(context)
        self.report({"INFO"}, "Default CloudRender restored")
        return {"FINISHED"}
