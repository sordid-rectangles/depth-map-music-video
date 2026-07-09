# TouchDesigner Point Cloud Viewer — Documentation

Reference for agents and developers continuing work on the Kinect depth viewer or building a Blender equivalent.

## Project files

| Path | Description |
|------|-------------|
| `touchdesigner/pointcloud-viewer-v5/pointcloud-viewer-v5.toe` | **Current** GPU POP viewer (save new versions here) |
| `touchdesigner/pointcloud-viewer-v5/Backup/` | TD auto-backups |
| `touchdesigner/pointcloud-viewer-v4/` | Prior CHOP-instancing viewer (superseded) |
| `touchdesigner/pointcloud-viewer-v3/` | Early prototype (nested sub-COMPs, abandoned) |

Network path inside the `.toe`: `/project1/pointcloud_viewer` (flat `baseCOMP`).

## Input data

Takes come from [`kinect/export/`](../../kinect/export/README.md). Use:

- `depth_aligned/frame_XXXXXX.exr` — float32 depth in **mm**, color-camera pixel grid
- `color/frame_XXXXXX.png`
- `calibration.json` — use **`color`** intrinsics with `depth_aligned`
- `manifest.json` — `frame_count`, `fps`

Frame numbers are **1-based**.

Test take used during v5 development: `take-02-20260623-150614` (~5005 frames, 1280×720, 30 fps).

## Docs index

| Doc | Read when… |
|-----|------------|
| [architecture.md](architecture.md) | Understanding the network, data flow, and design choices |
| [unproject-math.md](unproject-math.md) | Implementing or debugging pinhole unprojection / coordinate flips |
| [parameters-and-scripts.md](parameters-and-scripts.md) | Custom parms, DAT callbacks, what each script does |
| [pitfalls.md](pitfalls.md) | **Start here** if something broke — known TD gotchas from this build |
| [blender-parity.md](blender-parity.md) | Porting the viewer to a Blender add-on / geometry nodes — **next agent: playback** |

## Quick pipeline (v5 — GPU POP)

```
depth_in → depth_null → depth_mono (rgb=alpha) → depth_m (×0.001) ─┐
                                                                    ├→ geo1/topto → lookup_color → xform → null_pop → render1 → out1
color_in → color_null ──────────────────────────────────────────────┘
```

- **`depth_cam`:** fixed at origin — used only by TOP to POP unprojection
- **`cam1`:** view / orbit camera (separate from depth camera)
- **`xform`:** `transformattr` mode; `sy=1`, `sz=1` (TOP to POP already outputs −Z)

## MCP development

The viewer was built and debugged via [touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp) (`mcp_webserver_base.tox` on port **9981**).

Rules learned the hard way:

- Use **small, targeted** `execute_python_script` calls — iterating all parameters on multiple nodes crashed TD.
- Use **absolute paths** in callbacks (`op('/project1/pointcloud_viewer/...')`), not `op('..')` — use `parent()` inside same COMP when appropriate.
- Operator types as strings: `'baseCOMP'`, `'nullTOP'`, etc.
- MCP return values: **avoid nested dicts** in `result = {...}` — use flat lists.
- `poptoDAT` reads need `downloadtype='nextframe'` for reliable GPU point data.
- After MCP changes, **save the `.toe`** — unsaved work is lost on crash/restart (user saves manually; agents should not save unless asked).
- Confirm webserver is alive: Textport should show `Router initialized with 12 routes`.

## Status (v5 — Jul 2026)

### Working

- Take load from folder path (`Loadtake` pulse)
- Frame scrub via `Frame` parm
- Play toggle + `frame_driver` playback (~15 fps with EXR/PNG, Orbit camera)
- GPU TOP → POP point cloud with per-point color lookup
- Orbit camera (configurable pivot, azimuth, elevation, distance)
- Auto camera (centroid-based framing — **slow during playback**)
- Point size, subsample, width scale for aspect tuning
- Insertion nulls for depth/color FX before reconstruction

### Pinned / not yet solved

- **30 fps playback** from raw EXR + PNG sequences — I/O bound (~60 ms/frame best case). See [pitfalls.md — Playback / I/O](pitfalls.md#playback--io).
- **Proxy movie playback** (HAP / FFV1 / ProRes) — recommended path to 30 fps; not wired in v5 yet.
- Depth culling via `delete_zero` POP — bypassed; needs correct re-wire.
- Color → Line MAT styling for music-video look.

### Handoff note

Next work is **Blender playback options**. TD findings on what is fast vs slow are in [blender-parity.md](blender-parity.md#playback--performance). Blender should not replicate TD's per-frame `reloadpulse` hacks — native image sequences are the advantage.
