# Kinect Point Cloud — Blender

Load exported Kinect takes into Blender for preview, fly-through cameras, and stylized
point-cloud renders. Pairs with [`kinect/export/`](../kinect/export/) — no changes needed
on the export side.

## Artist workflow

1. **Install the add-on once** — Edit → Preferences → Add-ons → Install → pick the
   `kinect_pointcloud` folder (or zip it first).
2. **Open the template** — `templates/kinect_pointcloud_v1.blend` (create once; see
   [`templates/README.md`](templates/README.md)).
3. **Load a take** — Sidebar → Kinect → choose folder → **Load Take**.
4. **Scrub the timeline** — depth + color stay in sync (1-based frames).
5. **Creative work** — animate your own camera, build GN FX on **CloudRender**, tweak
   subsample / near / far in the sidebar.

## Dual-object layout

```
KINECT/
  CloudData     ← add-on writes timed point geometry (position, Cd, depth_mm) — hidden
  CloudRender   ← default look: colored points via Geometry Nodes
  Cameras/
    Orbit       ← optional starter rig; add FlyCam or any camera you like
```

| Object | What you see |
|--------|----------------|
| **CloudRender** | Default viewport look — **start here** |
| **CloudData** | Hidden data source; unhide or use Data Only Mode to inspect |

### Default CloudRender stack (created automatically)

```
Object Info (CloudData)  →  Set Point Radius  →  Output
```

- **Point Size** in the sidebar drives the Set Point Radius node.
- To stylize: open CloudRender’s Geometry Nodes and swap **Set Point Radius** for
  **Instance on Points** (+ cube, plane, etc.).
- **Reset Default Render** restores the simple stack if something breaks.

## Data-only mode

For debugging or fully custom CloudRender setups:

- **Off (default)** — CloudData hidden; **CloudRender** shows the default colored points.
- **On** — CloudData visible as wireframe; CloudRender still works if you keep its modifier.

## Controls (sensible defaults)

| Control | Default | Notes |
|---------|---------|-------|
| Subsample | 3 | Pixel stride; lower = denser, slower |
| Near (mm) | 600 | Depth clip |
| Far (mm) | 6000 | 0 = no far clip |
| Point size | 0.5 | Drives Set Point Radius on CloudRender |
| Width scale | 1.0 | Advanced — horizontal aspect fine-tune |
| Update on frame change | On | Turn off to pose camera on a held frame |
## Take folder layout

See [`kinect/export/README.md`](../kinect/export/README.md).

```
take-02-20260623-150614/
  depth_aligned/frame_000001.exr
  color/frame_000001.png
  calibration.json
  manifest.json
```

Use **`depth_aligned/`** + **`color/`** with **`color`** intrinsics from `calibration.json`.

## Validation

Reference take: `take-02-20260623-150614` (~5005 frames, 1280×720, 30 fps). Compare
frame 1 and frame 1000 against TouchDesigner v5 (`touchdesigner/docs/blender-parity.md`).

## Development

Add-on package: [`kinect_pointcloud/`](kinect_pointcloud/)

TouchDesigner parity notes: [`../touchdesigner/docs/blender-parity.md`](../touchdesigner/docs/blender-parity.md)
