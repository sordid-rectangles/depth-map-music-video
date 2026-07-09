import time

import bpy

from . import bake, import_take, scene_setup


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


class KINECT_OT_look_through_orbit(bpy.types.Operator):
    bl_idname = "kinect.look_through_orbit"
    bl_label = "Look Through Orbit Cam"
    bl_description = "Make the Orbit camera active and enter camera view"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        scene_setup.ensure_scene_layout(scene)
        import_take.frame_to_cloud(context)
        scene_setup.apply_orbit_camera(scene.kinect_take)

        cam = bpy.data.objects.get(scene_setup.OBJ_ORBIT_CAM)
        if cam is None:
            self.report({"ERROR"}, "No Orbit camera found")
            return {"CANCELLED"}

        scene.camera = cam
        space = getattr(context, "space_data", None)
        if space is not None and space.type == "VIEW_3D":
            space.region_3d.view_perspective = "CAMERA"
        else:
            self.report({"INFO"}, "Orbit camera active — press Numpad 0 to look through it")
        return {"FINISHED"}


class KINECT_OT_bake_take(bpy.types.Operator):
    bl_idname = "kinect.bake_take"
    bl_label = "Bake Take"
    bl_description = (
        "Pre-compute the whole take into a point cache for fast playback. "
        "Re-bake after changing Subsample / Near / Far / Width Scale"
    )

    _iter = None
    _timer = None
    _total = 0
    _done = 0

    def execute(self, context):
        settings = context.scene.kinect_take
        if not settings.loaded_take_name:
            self.report({"ERROR"}, "Load a take first (click Load Take)")
            return {"CANCELLED"}
        take_dir = import_take._take_path(settings)
        if take_dir is None or not take_dir.is_dir():
            self.report({"ERROR"}, "Load a take first")
            return {"CANCELLED"}

        # Authoritative frame count comes from the take manifest, never the
        # (possibly stale/default) settings value.
        try:
            meta = import_take.read_take_metadata(take_dir)
            frame_count = import_take.take_frame_count(meta)
        except Exception as exc:
            self.report({"ERROR"}, f"Cannot read take manifest: {exc}")
            return {"CANCELLED"}
        if frame_count < 1:
            self.report({"ERROR"}, "Take has no frames")
            return {"CANCELLED"}

        # Preflight: refuse a runaway bake before writing anything.
        try:
            est = bake.estimate_bake(take_dir, settings, frame_count)
        except Exception as exc:
            self.report({"ERROR"}, f"Bake preflight failed: {exc}")
            return {"CANCELLED"}
        if not est["ok"]:
            settings.bake_status = est["reason"]
            self.report({"ERROR"}, est["reason"])
            return {"CANCELLED"}

        bake.detach_cache()
        self._take_dir = take_dir
        self._total = frame_count
        self._done = 0
        try:
            self._iter = bake.bake_iter(take_dir, settings, frame_count)
        except Exception as exc:
            self.report({"ERROR"}, f"Bake failed to start: {exc}")
            return {"CANCELLED"}

        gb = est["est_bytes"] / 1e9
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.05, window=context.window)
        wm.modal_handler_add(self)
        settings.bake_status = (
            f"Baking… 0/{self._total}  (~{gb:.1f} GB, {est['points_per_frame']:,} pts/frame)"
        )
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type == "ESC":
            return self._cancel(context, "Bake cancelled")
        if event.type != "TIMER":
            return {"RUNNING_MODAL"}

        settings = context.scene.kinect_take
        # Small per-tick budget keeps the UI responsive on long bakes; ESC cancels.
        deadline = time.perf_counter() + 0.08
        try:
            while time.perf_counter() < deadline:
                self._done, self._total = next(self._iter)
        except StopIteration:
            return self._finish(context)
        except Exception as exc:
            return self._cancel(context, f"Bake error: {exc}")

        pct = int(self._done / max(1, self._total) * 100)
        settings.bake_status = f"Baking… {self._done}/{self._total} ({pct}%) — ESC to cancel"
        _tag_redraw(context)
        return {"RUNNING_MODAL"}

    def _finish(self, context):
        settings = context.scene.kinect_take
        bake.attach_cache(self._take_dir)
        settings.use_baked_cache = True
        settings.bake_status = f"Baked {self._total} frames — playback is fast"
        self._cleanup(context)
        try:
            import_take.rebuild_cloud_data(context)
        except Exception:
            pass
        _tag_redraw(context)
        self.report({"INFO"}, "Bake complete")
        return {"FINISHED"}

    def _cancel(self, context, message):
        context.scene.kinect_take.bake_status = message
        self._cleanup(context)
        _tag_redraw(context)
        self.report({"WARNING"}, message)
        return {"CANCELLED"}

    def _cleanup(self, context):
        self._iter = None
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None


def _tag_redraw(context):
    if context.area is not None:
        context.area.tag_redraw()
        return
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


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
