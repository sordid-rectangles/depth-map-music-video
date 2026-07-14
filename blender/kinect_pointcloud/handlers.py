import bpy
from bpy.app.handlers import persistent


def _ensure_frame_handler():
    # Re-append the frame-change handler if it is missing. Blender strips all
    # non-persistent app handlers on every file load; @persistent keeps ours in
    # place, but this guard also protects against double-registration and any
    # path that clears the list.
    if _on_frame_change not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(_on_frame_change)


@persistent
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


@persistent
def _on_load_post(_file_path):
    # Clean orphaned datablocks from old builds (e.g. an auto-refreshing color
    # SEQUENCE image) as soon as a .blend opens, before any frame change can
    # trigger its background image-cache balloon.
    try:
        from . import import_take

        removed = import_take.purge_stale_datablocks()
        if removed:
            print(f"[kinect] purged stale datablocks on load: {removed}")
    except Exception:
        pass

    # Belt-and-suspenders: @persistent should keep the frame handler across file
    # loads, but re-arm it here too so playback can never end up silently static.
    _ensure_frame_handler()


def register():
    _ensure_frame_handler()
    bpy.app.handlers.load_post.append(_on_load_post)


def unregister():
    if _on_frame_change in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(_on_frame_change)
    if _on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load_post)
