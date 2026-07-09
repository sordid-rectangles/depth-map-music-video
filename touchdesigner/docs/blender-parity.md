# Blender parity guide

What the TouchDesigner v5 viewer does, mapped to a Blender add-on / geometry-nodes workflow. Goal: same visual result from the same Kinect export takes.

**Next agent focus:** Blender **playback options** — TD proved the GPU reconstruction is cheap; the hard problem is feeding frames fast enough at 30 fps.

## Shared input contract

Read [`kinect/export/README.md`](../../kinect/export/README.md). No changes needed on the export side.

```
take/
  depth_aligned/frame_000001.exr   # float32 Z in mm, color camera grid
  color/frame_000001.png
  calibration.json                 # use color.fx/fy/cx/cy
  manifest.json                    # frame_count, fps
```

Frames are **1-based** — match Blender scene `frame_start`.

Test take: `take-02-20260623-150614` (~5005 frames, 1280×720, 30 fps).

## Feature parity checklist

| Feature | TD v5 implementation | Blender approach |
|---------|----------------------|------------------|
| Load take folder | `load_take.onPulse` | Operator: pick folder, parse JSON, set image sequences |
| Depth + color sync | Same `Frame` drives both file paths | Single timeline frame → both image sequences |
| Intrinsics scale | `scale = width / (cx*2)` | Same formula on import |
| Unproject | TOP to POP (`geo1/topto`) | GN: **Sample Image** + math, or Python batch |
| Subsample | TOP to POP `resx/resy` | Step in sample grid or decimate |
| Near/far clip | Reserved parms (cull POP bypassed) | Compare depth before unproject |
| Point color | `lookupPOP` from color TOP | Sample RGBA at pixel UV |
| Point size | Line MAT `Pointsize` | Point radius / instanced scale |
| Orbit camera | `cam1` + pivot parms | Camera rig with track-to constraint |
| Auto camera | `poptoDAT` centroid (slow) | Bounding-box framing — cache, don't recompute every frame |
| Depth FX | Nodes between `depth_in` → `depth_null` | Compositor / GN before sample |
| Color FX | Nodes between `color_in` → `color_null` | Same |
| Playback | `frame_driver` + explicit file reload | **Native image sequences** — Blender's main advantage |

## Playback & performance

### What TD learned (Jul 2026)

| Stage | TD cost | Notes |
|-------|---------|-------|
| EXR depth decode + reload | ~64 ms/frame | Per-file `reloadpulse` on Movie File In |
| PNG color decode + reload | ~90 ms/frame | Larger files than depth (~3.2 MB vs ~1.2 MB) |
| **Combined I/O (best case)** | **~60–65 ms** | Explicit paths, not folder index |
| Folder index + reload | ~150 ms | **Do not replicate this pattern** |
| GPU unproject + color lookup + render | **~0.3 ms** | Essentially free |
| Auto camera (centroid readback) | ~280 ms | Avoid per-frame in both TD and Blender |

**TD ceiling with raw EXR/PNG:** ~15 fps (Orbit camera). User saw ~4 fps before switching from folder-index to explicit paths.

**TD cannot hit 30 fps** without proxy video files (HAP / FFV1 / ProRes). ffmpeg was not on PATH during TD development — proxy generation is an open task.

### Blender opportunities (prioritize for next agent)

| Approach | Why |
|----------|-----|
| **Native image sequence nodes** | No per-frame `par.file` swap + `reloadpulse` — Blender loads sequences by frame index |
| **Persistent image cache / prefetch** | `clip_user` cache, memory cache, or manual preload of N frames ahead |
| **Proxy movies for viewport** | HAP / FFV1 for depth (lossless) + ProRes/H.264 for color viewport; keep EXR for final render |
| **Vectorized unproject** | NumPy on full grid once per frame — compare to TD's 0.3 ms GPU POP |
| **Don't recompute camera bounds every frame** | Cache centroid on play start or every N frames |
| **Point cloud cache sequence** | Bake `.ply` / `.vdb` / USD per frame for hero playback (trade disk for speed) |

### Suggested Blender playback tiers

| Tier | Viewport | Final render | Complexity |
|------|----------|--------------|------------|
| **A — Image sequences** | EXR + PNG via Image nodes, timeline scrub | Same | Low — start here |
| **B — Prefetch buffer** | Load frames N..N+k in background thread | EXR | Medium |
| **C — Video proxies** | FFV1/HAP depth + ProRes color `.mov` | EXR/PNG | Medium — needs ffmpeg bake step |
| **D — Baked point cache** | `.ply` or Blender point cache per frame | Full quality | High disk, fastest viewport |

### Proxy convention (proposed, not implemented in TD)

```
take/
  depth_aligned/…          # source
  color/…                  # source
  preview/
    depth.mov              # FFV1 gray16le or HAP Alpha — lossless-ish depth
    color.mov              # ProRes or HAP — color
```

Generate with ffmpeg (run outside Blender or as import step). TD would point Movie File In at these for 30 fps preview.

## What not to port from TD

| TD approach | Why skip in Blender |
|-------------|---------------------|
| Per-frame `par.file` path swap + `reloadpulse` | Blender image sequences work natively |
| Folder `index` + `reloadpulse` on Movie File In | 2× slower than explicit paths in TD; irrelevant in Blender |
| `preload(index)` without reload | Updates metadata only — misleading |
| `poptoDAT` centroid every playback frame | Kills performance — cache instead |
| MCP flat COMP layout | Blender uses node groups — nesting is fine |
| Separate `depth_cam` vs view camera | Blender equivalent: unproject in camera space, animate view camera separately |

## Coordinate math

See [unproject-math.md](unproject-math.md). Blender uses Z-up; TD uses Y-up with camera on +Z looking at −Z cloud.

For Blender (Z-up, typical camera):

```python
# After OpenCV unproject (meters):
x_cv = (px - cx) * z_m / fx
y_cv = (py - cy) * z_m / fy
z_cv = z_m

# Map to Blender world (verify on one frame):
x_bl = x_cv
y_bl = -y_cv
z_bl = -z_cv
```

**Validate against TD** on frame 1 and frame 1000 before batching.

### v5 TD-specific notes

- TOP to POP handles intrinsics — no manual Y flip needed after unproject.
- `focallengthsy = fy / width` (not `fy / height`).
- `Widthscale` tweaks horizontal aspect if cloud looks squashed.

## Recommended Blender architecture

```
[Image sequence: depth EXR]
[Image sequence: color PNG]
        ↓
[Scale intrinsics] ← calibration.json + image resolution
        ↓
[GN or Python: subsampled grid unproject]
        ↓
[Filter: near/far]
        ↓
[Points mesh with Cd attribute]
        ↓
[Viewport display / render]
```

### Geometry Nodes sketch

1. Drive frame from timeline (`Scene.frame_current`)
2. **Image Texture** nodes for depth and color (sequence mode)
3. Subsampled grid `(x, y)`:
   - `depth = sample(depth, x, y)` — verify EXR channel (TD uses alpha; Blender may differ)
   - Skip if outside near/far
   - `position = unproject(x, y, depth, fx, fy, cx, cy)`
   - `color = sample(color, x, y)`
4. **Set Point Radius** for point size

### Python alternative

Port unproject loop for validation, then vectorize with NumPy. Good for matching TD frame-for-frame before committing to GN.

## Parameters to expose (match TD v5)

| Parm | Blender UI |
|------|------------|
| Take path | Folder browser |
| Frame / playback | Timeline sync |
| Subsample | Int slider (1–16) |
| Near mm / Far mm | Float |
| Point size | Float |
| Camera mode | Orbit / Auto (cache Auto) |
| Orbit pivot / azimuth / elevation / distance | Floats |
| Width scale | Float (aspect fine-tune) |

## Validation workflow

1. Load `take-02-20260623-150614`
2. Frame 1, subsample 3, Orbit camera
3. Compare bounding box and point density to TD `render1`
4. Scrub frame 1 vs 1000 — motion should match
5. **Playback:** measure fps at 30 fps timeline — target ≥25 fps viewport with tier A or C

## Open questions for Blender plugin

1. **EXR channel layout in Blender** — depth in alpha vs named `Z` pass (TD uses alpha via monochrome TOP).
2. **Playback tier** — start with image sequences (tier A) or invest in proxy bake (tier C) upfront?
3. **Distortion** — export includes distortion coeffs; TD ignores them. Same for Blender v1?
4. **Point vs mesh** — point draw (TD lineMAT) vs instanced disks vs geometry nodes points.
5. **Proxy bake tooling** — add to `kinect/export/` or separate Blender-only import operator?

## Related docs

- [architecture.md](architecture.md) — TD v5 GPU network + playback model
- [pitfalls.md](pitfalls.md) — playback I/O timings, what not to do
- [parameters-and-scripts.md](parameters-and-scripts.md) — TD parms and callbacks
- [unproject-math.md](unproject-math.md) — math reference
