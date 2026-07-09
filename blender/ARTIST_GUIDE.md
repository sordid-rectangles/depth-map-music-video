# Artist quick start — Kinect point cloud in Blender

Load a Kinect take, bake it once, then play and style the point cloud smoothly.

**Requires:** Blender **4.2 LTS**. Nothing to `pip install` — the add-on uses Blender's built-in libraries.

All controls live in the **Kinect** tab of the 3D viewport sidebar (press **N** to open it).

---

## 1. Install the add-on (once)

From the repo folder `blender/`:

1. Run `scripts/package_addon.ps1` (or use the existing `kinect_pointcloud.zip`).
2. In Blender: **Edit → Preferences → Add-ons → Install…** → pick the zip.
3. Enable **Kinect Point Cloud**.
4. **Fully quit Blender and reopen** (needed after every update — “Reload Scripts” is not enough).

To confirm the version, open the **Kinect** tab → **Advanced** panel; the build is shown at the bottom (`v0.3.0 (2026-07-09-purge-stale)` or newer).

---

## 2. Load a take (~1 minute)

1. **File → New → General** (an empty file is fine).
2. Open the **Kinect** sidebar tab.
3. **Take** — browse to **one take folder** (not the whole export root), e.g.
   `…/kinect-exports/take-02-20260623-150614`.
   It must contain `calibration.json`, `manifest.json`, `depth_aligned/`, `color/`.
4. Click **Load Take**. A colored point cloud appears.
5. Scrub the timeline — the cloud follows along (slowly, until you bake — next step).

> You always look at **CloudRender**. `CloudData` is the raw data and stays hidden on purpose.

---

## 3. Bake for smooth playback (once per take)

Before baking, scrubbing decodes the files every frame (slow). Baking pre-computes the
whole take so playback runs at 100+ fps and stays memory-light.

1. In **Shape**, set **Point Spacing / Near / Far** how you want them (baking locks these in).
2. Go to **Playback → Bake Take**. A progress bar runs (~4 min for a 5000-frame take); press **ESC** to cancel.
3. When it reads **“Baked … playback is fast,”** press play.

The cache is saved next to the take in `blender_cache/` and reloads automatically next time.

- The button shows an estimate first (e.g. `~1.5 GB, 15,828 pts/frame`). If **Point Spacing** is too low the bake would be enormous, so the add-on **refuses it** and asks you to raise Point Spacing — it will never quietly fill your disk or RAM.
- **Re-bake** only after changing **Point Spacing / Near / Far / Width Scale** (the panel will say “Cache is stale — re-bake”). Look, material, and modifier changes **never** need a re-bake.

---

## 4. Style the look

You develop the look on **CloudRender** — a normal object with a **Geometry Nodes** modifier.

- Select **CloudRender**, open the **Modifier Properties** (wrench) or a Geometry Nodes editor.
- The starter stack is `Object Info (CloudData) → Mesh to Points → Set Material → Output`.
- Swap **Mesh to Points** for your own nodes (instances, meshing, noise, etc.). Keep a **Set Material** node — GN point clouds need it to show color in Blender 4.2.
- The color comes from the `Cd` point attribute (Kinect RGB). There's also a `depth_mm` attribute you can drive size/effects with.
- **Shape → Reset Look** restores the starter stack if you want to start over.

Play the timeline while you tweak — it stays smooth (playing from the bake), and look changes never require re-baking.

---

## 5. View through the orbit camera

In the **Camera** panel (mode **Orbit**):

1. Click **Look Through Orbit Cam** — it aims a camera at the cloud, makes it active, and enters camera view.
2. Drag **Distance / Azimuth / Elevation** to orbit around the cloud **live**.
3. Nudge **Orbit Center X / Y / Z** to shift the framing (X = left/right, Y = forward/back, Z = up/down).
4. **Recenter on Cloud** snaps the orbit center back to the middle of the cloud.

Prefer your own camera? Set the mode to **Free** and animate any camera you like.
(You can also just middle-mouse-drag to orbit the viewport without a camera at all.)

---

## 6. Sidebar reference

**Shape**

| Control | Start with | What it does |
|---------|------------|--------------|
| **Point Spacing** | 12–16 smooth, 8 dense | Pixels between points. Higher = fewer points, faster. Re-bake after changing |
| **Near / Far** | 600 / 6000 | Hide points closer/farther than this (mm). Re-bake after changing |
| **Point Size** | 0.5 | Dot size in the default look |
| **Reset Look** | — | Restore the starter CloudRender nodes |

**Playback**

| Control | Notes |
|---------|-------|
| **Bake Take** | Pre-compute the take for fast playback (do this once) |
| **Use Baked Cache** | Keep on. Off = force slow live decode |
| **Follow Timeline** | Update the cloud as it plays. Turn off to hold one frame while posing a camera |

**Advanced** (collapsed by default)

| Control | Notes |
|---------|-------|
| **Auto Rebuild** / **Rebuild Now** | Refresh the cloud after changing Shape values (usually automatic) |
| **Width Scale** | Fix a squashed/stretched cloud. Re-bake after changing |
| **Debug: show raw data** | Show raw CloudData wireframe (troubleshooting only) |

---

## 7. Pitfalls

| Problem | Fix |
|---------|-----|
| Playback is laggy | **Bake the take** (section 3). Live playback is slow by design |
| Baked but still slow | Make sure **Use Baked Cache** is on and status says “Baked … fast” |
| “Bake refused — cache too large” | Raise **Point Spacing** (e.g. 8–16), then bake again |
| “Load a take first” when baking | Click **Load Take** before **Bake Take** |
| Changed a Shape value, cloud looks wrong on play | Cache is stale — click **Bake Take** again |
| Blank viewport | You're probably hiding **CloudRender**; `CloudData` is hidden on purpose |
| Add-on updated but nothing changed | **Quit Blender completely** and reopen |
| “Missing file” / wrong folder | Pick the **take folder** (with `calibration.json`), not a parent export folder |
| `//` path errors | Save the `.blend`, or paste an **absolute** take folder path |
| Do **not** `pip install OpenEXR` into Blender | It crashes Blender and isn't needed |
| System-wide lag / slowdown over time | Fixed: old files could leave an auto-refreshing color sequence that ballooned memory. Opening the file now auto-purges it (check the System Console for a "purged stale datablocks" line) |

---

## 8. Take folder layout (from export)

```
take-02-20260623-150614/
  depth_aligned/frame_000001.exr
  color/frame_000001.png
  calibration.json
  manifest.json
  blender_cache/            ← created by Bake Take (safe to delete to force a re-bake)
```

Timeline frames are **1-based** (frame 1 = `frame_000001`).

---

## 9. Good to know

- **Memory stays flat.** Playback streams one frame at a time from the cache, so a 5000-frame take uses no more RAM than a short one.
- **Baking** reads the whole take once and writes a few GB to `blender_cache/`. One-time per Point Spacing / Near / Far / Width Scale setting.
- Missing/broken export frames are skipped (shown as empty) instead of stopping playback.

---

## Help / dev

- Add-on source: [`kinect_pointcloud/`](kinect_pointcloud/)
- Export contract: [`../kinect/export/README.md`](../kinect/export/README.md)
- Technical notes: [`README.md`](README.md)
