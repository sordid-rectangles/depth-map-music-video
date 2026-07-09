"""Blender version compatibility helpers."""

from __future__ import annotations

import bpy


def blender_version() -> tuple[int, int, int]:
    return bpy.app.version


# Icons valid in Blender 4.2 UI labels (newer icon names fail at draw time).
ICON_NODE = "NODE"
ICON_MESH = "NODE"
ICON_WIRE = "NODE"
ICON_INFO = "INFO"
ICON_TIME = "NONE"
ICON_CAMERA = "NONE"
ICON_SETTINGS = "NONE"
