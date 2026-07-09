import bpy


def _on_frame_change(scene, _depsgraph):
    if scene.get("kinect_loading_take"):
        return
    settings = scene.kinect_take
    if not settings.loaded_take_name or not settings.update_on_frame_change:
        return
    try:
        from . import import_take

        import_take.rebuild_cloud_data(bpy.context)
    except Exception:
        pass


def register():
    bpy.app.handlers.frame_change_post.append(_on_frame_change)


def unregister():
    if _on_frame_change in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(_on_frame_change)
