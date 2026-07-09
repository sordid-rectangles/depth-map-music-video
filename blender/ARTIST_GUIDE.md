# Artist quick start — Kinect point cloud in Blender

Brief handoff for previewing Kinect takes and playing with stylized point renders.

**Requires:** Blender **4.2 LTS** (tested on 4.2.x). No Python packages to install — the add-on uses Blender’s built-in libraries.

---

## 1. Install the add-on (once)

From the repo folder `blender/`:

1. Run `scripts/package_addon.ps1` (or use the existing `kinect_pointcloud.zip`).
2. In Blender: **Edit → Preferences → Add-ons → Install…** → pick the zip.
3. Enable **Kinect Point Cloud**.
4. **Fully quit Blender and reopen** (required after every add-on update — “Reload Scripts” is not enough).

Confirm install: **View3D sidebar (N) → Kinect tab** should show  
`v0.1.15 (2026-07-08-scale-seq)` at the top.

---

## 2. First test run (~2 minutes)

1. **File → New → General** (empty file is fine).
2. Open the **Kinect** sidebar tab.
3. **Take Folder** — browse to **one take folder**, not the whole export root, e.g.  
   `…/kinect-exports/take-02-20260623-150614`  
   (must contain `calibration.json`, `manifest.json`, `depth_aligned/`, `color/`).
4. Click **Load Take**.
5. In the viewport, look at **CloudRender** (not CloudData). You should see a colored point cloud.
6. If the camera feels off: **Kinect → Camera → Frame to Cloud**.
7. Scrub the timeline — frame 1 should update the cloud (may be slow; see pitfalls).

---

## 3. What’s in the scene

```
KINECT/
  CloudData      ← data (hidden) — position, color, depth
  CloudRender    ← what you look at — default colored points (Geometry Nodes)
  Cameras/Orbit  ← optional starter camera
```

**Stylize looks on CloudRender:** open its Geometry Nodes modifier. Default stack is  
`Object Info (CloudData) → Mesh to Points → Output`. Swap **Mesh to Points** for your own nodes (instances, noise, etc.). **Reset Default Render** in the sidebar restores the starter stack.

---

## 4. Sidebar controls (what to tweak)

| Control | Start with | Notes |
|---------|------------|--------|
| **Subsample** | 12–16 for playback, 8 for quality | Higher = fewer points, faster |
| **Near / Far (mm)** | 600 / 6000 | Depth clip |
| **Point Size** | 0.5 | Radius on CloudRender |
| **Update on Frame Change** | On | Turn **off** to pose camera on one frame without reloading |
| **Data Only Mode** | Off | On = show raw CloudData wireframe for debugging |

---

## 5. Pitfalls

| Problem | Fix |
|---------|-----|
| Old take path after reinstall | Path is saved in the `.blend` file — pick the folder again and **Load Take** |
| Add-on updated but behavior unchanged | **Quit Blender completely**, reopen |
| “Missing file” / wrong frame path | Select the **take folder** (with `calibration.json`), not a parent export folder (unless it only has one take) |
| Blank viewport | Select **CloudRender** in the outliner; CloudData is hidden on purpose |
| Playback very laggy | Expected at full res — raise **Subsample** to 16+, or turn off **Update on Frame Change** while animating the camera |
| `//` path errors | Save the `.blend` or use an **absolute** take folder path |
| Do **not** `pip install OpenEXR` into Blender | Crashes Blender; not needed |

---

## 6. Take folder layout (from export)

```
take-02-20260623-150614/
  depth_aligned/frame_000001.exr
  color/frame_000001.png
  calibration.json
  manifest.json
```

Timeline frames are **1-based** (frame 1 = `frame_000001`).

---

## 7. Known limits (this checkpoint)

- **Load + single-frame scrub:** working.
- **Playback FPS:** still low (~5–10 fps) — each frame re-reads EXR/PNG from disk. Fine for posing and look dev; real-time playback is a future improvement (proxies / prefetch).
- **Template `.blend`:** optional; empty file + Load Take is enough for now.

---

## Help / dev

- Add-on source: [`kinect_pointcloud/`](kinect_pointcloud/)
- Export contract: [`../kinect/export/README.md`](../kinect/export/README.md)
- Technical notes: [`README.md`](README.md)
