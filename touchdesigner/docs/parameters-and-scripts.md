# Parameters and scripts

## Custom parameters on `pointcloud_viewer` (v5)

| Page | Parm | Type | Default | Effect |
|------|------|------|---------|--------|
| Take | `Takepath` | str | — | Folder containing `calibration.json`, `manifest.json`, frame subdirs |
| Take | `Loadtake` | pulse | — | Runs `load_take.onPulse` |
| Playback | `Play` | toggle | off | `frame_driver` advances frames each timeline step |
| Playback | `Frame` | int | 1 | 1-based frame index |
| Playback | `Fps` | float | 30 | Sets `project.cookRate` when `Play` on |
| Cloud | `Subsample` | int | 3 | Pixel stride for TOP to POP (`resx/resy = width/sub`, `height/sub`) |
| Cloud | `Nearmm` | float | 600 | Near depth clip (mm) — reserved |
| Cloud | `Farmm` | float | 6000 | Far depth clip (mm) — reserved |
| Cloud | `Pointsize` | float | 0.5 | Line MAT point size multiplier |
| Cloud | `Widthscale` | float | 1.0 | Horizontal focal scale tweak (`focallengthsx` divisor) |
| Camera | `Cameramode` | menu | `Orbit` | `Orbit` or `Auto` |
| Camera | `Orbitx/y/z` | float | — | Orbit pivot (world meters) |
| Camera | `Orbitdist` | float | — | Orbit camera distance |
| Camera | `Orbitaz` | float | — | Azimuth (degrees) |
| Camera | `Orbitelev` | float | — | Elevation (degrees) |
| Camera | `Centerorbit` | pulse | — | Sample cloud centroid → set orbit pivot |

### `par_exec` watched parms

Must match every parm that needs a callback:

```
Loadtake Frame Subsample Pointsize Widthscale Cameramode
Orbitx Orbity Orbitz Orbitdist Orbitaz Orbitelev Centerorbit
Fps Play
```

**If a parm change does nothing, check it is in this list.**

## `load_take` (textDAT)

### `setup_io(owner)`

- Points `depth_in` / `color_in` at `frame_000001` in each subfolder (initial load).
- Sets `imageindexing=zero`, `playmode=specify`, `prereadframes=30`, `outputresolution=useinput`.
- Wires `depth_null` and `color_null`.

### `setup_gpu(owner)`

- Creates/configures `depth_cam` at origin.
- Configures `geo1/topto` intrinsics from `calib_const` + `Widthscale` / `Subsample`.
- Wires `topto → lookup_color → xform → null_pop`.
- Sets `xform` to `transformattr`, `sy=1`, `sz=1`.
- Bypasses `delete_zero`.
- Enables `null_pop` render, lineMAT point draw.

### `update_frames(owner)`

Sets explicit per-frame paths and reloads:

```python
d.par.file = f'{take}/depth_aligned/frame_{frame:06d}.exr'
c.par.file = f'{take}/color/frame_{frame:06d}.png'
d.par.reloadpulse.pulse()
c.par.reloadpulse.pulse()
```

### `set_playing(owner, playing)`

Keeps moviefilein in `specify` mode with `play=False`. Sets `project.cookRate` from `Fps` when play starts.

### `cook_playback(owner)`

Cooks `depth_in`, `color_in`, GPU POP chain, camera (Orbit or Auto), `render1`. Called after `update_frames` during scrub and play.

### `center_orbit(owner)` / `apply_orbit_camera` / `apply_auto_camera`

- **Orbit:** positions `cam1` from pivot + azimuth/elevation/distance parms.
- **Auto:** reads cloud centroid via `poptoDAT` — **slow**; avoid calling every frame during playback.

### `onPulse(par)` (Loadtake)

Full take load: read JSON, `setup_io`, `update_frames`, scale intrinsics into `calib_const`, `setup_gpu`, `center_orbit`, `apply_camera`, initial render.

## `par_exec` (parameterExecuteDAT)

```python
def onValueChange(par, prev):
    if par.name == 'Frame':
        if owner.par.Play:
            return  # frame_driver owns playback
        mod.update_frames(owner)
        mod.cook_playback(owner)
    elif par.name == 'Play':
        mod.set_playing(owner, bool(par.eval()))
        if par.eval():
            project.cookRate = float(owner.par.Fps.eval())
    # Subsample/Pointsize/Widthscale → setup_gpu + recook
    # Cameramode/orbit parms → apply_camera + render
    # Fps → project.cookRate
```

## `frame_driver` (executeDAT)

```python
def onFrameStart(frame):
    owner = parent()
    if not owner.par.Play:
        return
    owner.par.Frame = (int(owner.par.Frame) % fc) + 1
    mod.update_frames(owner)
    mod.cook_playback(owner)
```

Active: `par.active`, `par.start`, `par.framestart` all **true**.

## `calib_const` channels

| Channel | Set by |
|---------|--------|
| `fx`, `fy`, `cx`, `cy` | Scaled color intrinsics |
| `width`, `height` | Loaded depth TOP resolution |
| `frame_count` | `manifest.json` |

## Geo / render (v5)

| Setting | Value |
|---------|-------|
| Unprojection | `geo1/topto` (TOP to POP) |
| Color | `geo1/lookup_color` samples `color_null` |
| Material | `geo1/linemat` — point draw |
| View camera | `cam1` |
| Depth camera | `depth_cam` (fixed, not orbited) |
| Render | `render1` → `out1` |

## v4 scripts (legacy)

v4 used `unproject` scriptCHOP + `unproject_callbacks.onCook` + CHOP instancing on `geo1`. See `pointcloud-viewer-v4/` — do not reference for v5 work.
