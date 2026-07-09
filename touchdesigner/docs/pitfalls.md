# Pitfalls — lessons from building v4/v5

Read this before making MCP changes or debugging a "broken" viewer.

## TouchDesigner crashes / hangs

| Cause | Fix |
|-------|-----|
| Heavy MCP script iterating all `pars()` on multiple nodes | Small targeted scripts only |
| Broken MCP tox (routes not registered) | Re-import `mcp_webserver_base.tox`; Textport must show `Router initialized with 12 routes` |
| Unsaved `.toe` after MCP edits | User saves manually; agents should not save unless asked |

## Depth / EXR

| Symptom | Cause | Fix |
|---------|-------|-----|
| Cloud empty or flat | Depth in wrong channel | Kinect EXR `Z` loads as **alpha (index 3)** in Movie File In — use `depth_mono` with `rgb=alpha` |
| `index` changes but image doesn't | Folder/index mode without reload | Use **explicit `par.file` paths** + `reloadpulse` |
| `preload(index)` shows wrong frame | Preload updates index metadata only | Do not use for scrub — use `reloadpulse` |
| `cuepulse` fast but wrong pixels | Cue does not reload file data | Use `reloadpulse` |
| `file` parm has default expression | e.g. `app.samplesFolder+'/Map/Banana.tif'` | Clear `par.file.expr = ''` on load |
| Calibration wrong scale | `calibration.json` color intrinsics are for full sensor (~2560×1440), export is 1280×720 | `scale = width / (cx * 2)` then multiply `fx,fy,cx,cy` |

## Playback / I/O

**GPU is solved (~0.3 ms). Disk I/O is the bottleneck.**

| Symptom | Cause | Fix |
|---------|-------|-----|
| ~4 fps playback | Folder `index` + `reloadpulse` (~150 ms/frame) + possible Auto camera | Switch to **explicit per-frame file paths** (~60 ms/frame) |
| Play toggle does nothing | `Play` not in `par_exec.par.pars` | Add `Play` to watched parm list |
| Play toggle does nothing | `frame_driver` inactive | `active`, `start`, `framestart` all true |
| Play toggle does nothing | Project timeline paused | Timeline must be running (Realtime on) |
| Frames stuck / wrong | Sequential `playmode` in script loop | Sequential only advances across timeline time steps — use explicit paths + `frame_driver` instead |
| Double cook / extra slow | `par_exec` and `frame_driver` both handle Frame | `par_exec` skips `Frame` when `Play` is on |
| ~5 fps even after path fix | `Cameramode = Auto` during play | Auto runs `poptoDAT` centroid every frame (~280 ms). Use **Orbit** for playback preview |
| Can't hit 30 fps | EXR decode ~60 ms/frame minimum | Need **proxy movies** (HAP / FFV1 / ProRes) — raw sequences won't reach 30 fps |

### Measured timings (take-02, 1280×720, Jul 2026)

| Method | ms/frame | ~fps |
|--------|----------|------|
| Folder index + reload (depth + color) | ~150 | 6–7 |
| Explicit paths + reload (depth + color) | **~60–65** | **~15** |
| Depth reload only | ~64 | — |
| Color reload only | ~90 | — |
| Full pipeline + Orbit camera | ~65 | ~15 |
| Full pipeline + Auto camera | ~340 | ~3 |

### Recommended loading pattern (`update_frames`)

```python
take = owner.par.Takepath.eval().replace('\\\\', '/')
frame = int(owner.par.Frame)
d.par.file = f'{take}/depth_aligned/frame_{frame:06d}.exr'
c.par.file = f'{take}/color/frame_{frame:06d}.png'
d.par.reloadpulse.pulse()
c.par.reloadpulse.pulse()
```

**Note:** `load_take` Python strings must use `'\\\\'` in `.replace()` — a single backslash breaks module compilation.

## v5 GPU POP / TOP to POP

| Symptom | Cause | Fix |
|---------|-------|-----|
| Blank render | Wrong xform mode | `xform.par.mode = 'transformattr'` |
| Upside-down cloud | Manual Y flip on xform | `sy=1` — TOP to POP already outputs −Z |
| Squashed horizontally | `focallengthsy = fy/h` | Use `focallengthsy = fy/w` + tune `Widthscale` |
| Cloud at wrong world position | Orbiting `depth_cam` | Keep `depth_cam` at origin; orbit `cam1` only |
| No points | `delete_zero` active | Bypass `delete_zero` until culling is re-wired |
| `poptoDAT` empty/wrong | Default download timing | `downloadtype = 'nextframe'` |

## v4 CHOP path (legacy — v4 only)

| Symptom | Cause | Fix |
|---------|-------|-----|
| Spiderweb lines | choptoSOP / scriptSOP single polyline | Use CHOP instancing (v4) or GPU POP (v5) |
| Scale warnings `'0.015' not found` | Scale fields treat values as channel names | Use `ps` channel on unproject |
| Subsample ≤2 "breaks" cloud | Hard 50k cap truncated mid-scan | Adaptive subsample bump |

## Parameters / callbacks

| Symptom | Cause | Fix |
|---------|-------|-----|
| Load Take / parms dead | `load_take` syntax error (bad escape in `.replace('\\', '/')`) | Check Textport; validate DAT compiles |
| Parm change does nothing | Not in `par_exec.par.pars` | Add to watched list — especially `Play`, `Cameramode` |
| `executepars` / `execute` wrong names | TD version uses `pars`, executeDAT uses `framestart` | Check actual par names per operator |

## Nested COMPs (v3 — do not repeat)

- TOP connections across nested `baseCOMP` boundaries failed to persist via MCP
- Relative paths in nested callbacks broke frequently
- Flat layout is simpler and more reliable

## MCP tips

- Nested dicts in `result = {...}` can break MCP serialization — return flat lists.
- Evaluating some parameters via MCP returns nested operator objects — use `str(par.val)`.
- Avoid iterating all parameters on all nodes in one script.

## Coordinate quick reference (v5)

TOP to POP handles unprojection internally using `depth_cam` intrinsics. For manual/debug math see [unproject-math.md](unproject-math.md).

Key v5 gotcha: do **not** add an extra `sy=-1` on `xform` — cloud ends up inverted.
