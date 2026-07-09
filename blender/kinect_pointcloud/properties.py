import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)


def _rebuild_cloud(self, context):
    if getattr(context.scene, "kinect_loading_take", False):
        return
    if not self.auto_rebuild or not self.loaded_take_name:
        return
    from . import import_take

    import_take.rebuild_cloud_data(context)


def _apply_orbit(self, context):
    """Move the Orbit camera live when its sliders change."""
    from . import scene_setup

    try:
        scene_setup.apply_orbit_camera(self)
    except Exception:
        pass


class KinectTakeSettings(bpy.types.PropertyGroup):
    take_path: StringProperty(
        name="Take Folder",
        subtype="DIR_PATH",
        description="Folder containing calibration.json, manifest.json, and frame subdirs",
    )

    loaded_take_name: StringProperty(
        name="Loaded Take",
        default="",
        options={"HIDDEN"},
    )

    frame_count: IntProperty(name="Frame Count", default=1, options={"HIDDEN"})
    status_message: StringProperty(name="Status", default="", options={"HIDDEN"})

    data_only: BoolProperty(
        name="Debug: show raw data",
        description=(
            "Show the raw CloudData mesh as a wireframe instead of the styled "
            "CloudRender. For debugging only"
        ),
        default=False,
        update=_rebuild_cloud,
    )

    subsample: IntProperty(
        name="Point Spacing",
        description=(
            "Pixels between points. Higher = fewer points and faster playback; "
            "lower = denser cloud. 12–16 is smooth, 8 is dense. Re-bake after changing"
        ),
        default=3,
        min=1,
        max=16,
        update=_rebuild_cloud,
    )

    near_mm: FloatProperty(
        name="Near",
        description="Hide points closer than this to the camera (millimeters). Re-bake after changing",
        default=600.0,
        min=0.0,
        soft_max=3000.0,
        update=_rebuild_cloud,
    )

    far_mm: FloatProperty(
        name="Far",
        description="Hide points farther than this (millimeters). 0 = no far limit. Re-bake after changing",
        default=6000.0,
        min=0.0,
        soft_max=12000.0,
        update=_rebuild_cloud,
    )

    point_size: FloatProperty(
        name="Point Size",
        description="Dot size in the default CloudRender look",
        default=0.5,
        min=0.01,
        soft_max=5.0,
        update=_rebuild_cloud,
    )

    width_scale: FloatProperty(
        name="Width Scale",
        description="Fine-tune horizontal aspect if the cloud looks squashed or stretched. Re-bake after changing",
        default=1.0,
        min=0.5,
        soft_max=2.0,
        update=_rebuild_cloud,
    )

    update_on_frame_change: BoolProperty(
        name="Follow Timeline",
        description="Update the cloud as the timeline plays. Turn off to hold one frame while posing the camera",
        default=True,
    )

    use_baked_cache: BoolProperty(
        name="Use Baked Cache",
        description=(
            "Play back from the baked point cache when available (fast). "
            "Uncheck to force live decode + unproject from EXR/PNG"
        ),
        default=True,
        update=_rebuild_cloud,
    )

    bake_status: StringProperty(
        name="Bake Status",
        default="",
        options={"HIDDEN"},
    )

    auto_rebuild: BoolProperty(
        name="Auto Rebuild",
        description="Rebuild the cloud automatically when you change Density / Near / Far",
        default=True,
    )

    camera_mode: EnumProperty(
        name="Camera Mode",
        items=(
            ("ORBIT", "Orbit", "Manual orbit camera around a pivot"),
            ("FREE", "Free", "Do not drive any camera from the add-on"),
        ),
        default="ORBIT",
        update=_apply_orbit,
    )

    orbit_pivot_x: FloatProperty(
        name="Pivot X", description="Shift the orbit center left / right",
        default=0.0, unit="LENGTH", update=_apply_orbit,
    )
    orbit_pivot_y: FloatProperty(
        name="Pivot Y", description="Shift the orbit center forward / back (toward or away from camera)",
        default=0.0, unit="LENGTH", update=_apply_orbit,
    )
    orbit_pivot_z: FloatProperty(
        name="Pivot Z", description="Shift the orbit center up / down",
        default=0.0, unit="LENGTH", update=_apply_orbit,
    )
    orbit_distance: FloatProperty(name="Distance", default=3.0, min=0.1, soft_max=20.0, unit="LENGTH", update=_apply_orbit)
    orbit_azimuth: FloatProperty(name="Azimuth", default=0.0, soft_min=-180.0, soft_max=180.0, subtype="ANGLE", update=_apply_orbit)
    orbit_elevation: FloatProperty(name="Elevation", default=0.785398, soft_min=-1.5708, soft_max=1.5708, subtype="ANGLE", update=_apply_orbit)
