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
        name="Data Only Mode",
        description=(
            "Update CloudData attributes only; no add-on viewport styling. "
            "Use CloudRender for all look development"
        ),
        default=False,
        update=_rebuild_cloud,
    )

    subsample: IntProperty(
        name="Subsample",
        description="Pixel stride when building the point cloud (1 = full resolution)",
        default=3,
        min=1,
        max=16,
        update=_rebuild_cloud,
    )

    near_mm: FloatProperty(
        name="Near (mm)",
        description="Ignore depth closer than this (millimeters)",
        default=600.0,
        min=0.0,
        soft_max=3000.0,
        update=_rebuild_cloud,
    )

    far_mm: FloatProperty(
        name="Far (mm)",
        description="Ignore depth farther than this (millimeters). 0 = no far clip",
        default=6000.0,
        min=0.0,
        soft_max=12000.0,
        update=_rebuild_cloud,
    )

    point_size: FloatProperty(
        name="Point Size",
        description="Point radius on CloudRender (Set Point Radius node); raw CloudData preview if default render is removed",
        default=0.5,
        min=0.01,
        soft_max=5.0,
        update=_rebuild_cloud,
    )

    width_scale: FloatProperty(
        name="Width Scale",
        description="Fine-tune horizontal aspect if the cloud looks squashed",
        default=1.0,
        min=0.5,
        soft_max=2.0,
        update=_rebuild_cloud,
    )

    update_on_frame_change: BoolProperty(
        name="Update on Frame Change",
        description="Rebuild CloudData when the timeline frame changes",
        default=True,
    )

    auto_rebuild: BoolProperty(
        name="Auto Rebuild",
        description="Rebuild CloudData when cloud parameters change",
        default=True,
    )

    camera_mode: EnumProperty(
        name="Camera Mode",
        items=(
            ("ORBIT", "Orbit", "Manual orbit camera around a pivot"),
            ("FREE", "Free", "Do not drive any camera from the add-on"),
        ),
        default="ORBIT",
    )

    orbit_pivot_x: FloatProperty(name="Pivot X", default=0.0, unit="LENGTH")
    orbit_pivot_y: FloatProperty(name="Pivot Y", default=0.0, unit="LENGTH")
    orbit_pivot_z: FloatProperty(name="Pivot Z", default=0.0, unit="LENGTH")
    orbit_distance: FloatProperty(name="Distance", default=3.0, min=0.1, soft_max=20.0, unit="LENGTH")
    orbit_azimuth: FloatProperty(name="Azimuth", default=0.0, soft_min=-180.0, soft_max=180.0, subtype="ANGLE")
    orbit_elevation: FloatProperty(name="Elevation", default=0.785398, soft_min=-1.5708, soft_max=1.5708, subtype="ANGLE")
