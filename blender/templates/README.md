# Template `.blend` — `kinect_pointcloud_v1.blend`

Save an empty scene after **Load Take** once, or run the setup script below. The add-on
creates the full layout automatically.

## What you see by default

The add-on builds two objects. **Look at CloudRender** — that is the picture.

```
CloudData  ──►  (add-on rebuilds points each frame — hidden in viewport)

CloudRender  ──►  Geometry Nodes:
                    Object Info (CloudData)
                         ↓
                    Set Point Radius   ← sidebar "Point Size" controls this
                         ↓
                    colored points (material reads Cd from CloudData)
```

### To stylize

Open **CloudRender → Modifiers → KinectDefaultRender → Geometry Nodes** and edit the tree:

| Goal | Replace Set Point Radius with… |
|------|--------------------------------|
| Pillars / columns | **Instance on Points** + Cube (scale Z by `depth_mm` attribute) |
| Sheets / cards | **Instance on Points** + Plane |
| Raw points debug | Enable **Data Only Mode** in sidebar — CloudData wireframe appears |

Broken the node tree? Sidebar → **Reset Default Render**.

## Scene contents (auto-created)

```
KINECT/
  CloudData       hidden — data only
  CloudRender     default look lives here
  Cameras/
    Orbit         optional starter camera
    OrbitPivot
```

Add **FlyCam** or any camera under `Cameras/` for fly-through shots. Set **Camera Mode → Free**
in the sidebar so the add-on stops moving Orbit.

## Setup script (optional)

With Blender open and the add-on enabled:

```python
import bpy
import kinect_pointcloud.scene_setup as setup

setup.ensure_scene_layout(bpy.context.scene)
```

Save as `kinect_pointcloud_v1.blend`.
