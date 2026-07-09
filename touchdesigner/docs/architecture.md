# Architecture — `pointcloud_viewer`

## Design principle: flat network

Early v3 used nested sub-COMPs (`io/`, `reconstruct/`, `render/`). **TOP wires across nested `baseCOMP` boundaries did not stick** via MCP, and debugging was painful.

v4/v5 use a **single flat** `baseCOMP` at `/project1/pointcloud_viewer` with all operators as direct children.

## v5 GPU pipeline (current)

v4 used a CPU `scriptCHOP` unproject + CHOP instancing. **v5 replaces that with TOP → POP** on the GPU.

```
depth_in → depth_null → depth_mono → depth_m (×0.001 mm→m)
                                              ↓
geo1:  topto (TOP to POP) ← depth_m           lookup_color ← color_null ← color_in
              ↓                                      ↓
           xform (transformattr) ←───────────────────┘
              ↓
           null_pop → render1 → out1
```

| Node | Type | Role |
|------|------|------|
| `depth_in` | moviefileinTOP | Per-frame `depth_aligned/frame_XXXXXX.exr` |
| `color_in` | moviefileinTOP | Per-frame `color/frame_XXXXXX.png` |
| `depth_null` | nullTOP | **FX insertion point** before depth processing |
| `color_null` | nullTOP | **FX insertion point** before color lookup |
| `depth_mono` | monochromeTOP | Routes depth to alpha (`rgb=alpha`) |
| `depth_m` | mathTOP | Scale mm → meters (`×0.001`) |
| `depth_cam` | cameraCOMP | Fixed at origin; drives TOP to POP intrinsics only |
| `geo1/topto` | TOP to POP | Unprojects depth TOP to point positions |
| `geo1/lookup_color` | lookupPOP | Samples `color_null` at point UVs |
| `geo1/xform` | transformPOP | `transformattr` on `P` (no Y flip — see pitfalls) |
| `geo1/null_pop` | nullPOP | Render geometry output |
| `geo1/linemat` | lineMAT | Point draw (size from `Pointsize` parm) |
| `cam1` | cameraCOMP | View / orbit camera |
| `cloud_target` | nullCOMP | Orbit look-at pivot |
| `render1` | renderTOP | 1280×720 render |
| `calib_const` | constantCHOP | Scaled intrinsics + `width`, `height`, `frame_count` |

### TOP to POP intrinsics

Set on `geo1/topto` with `viewanglemethod = focallengths`:

```
focallengthsx = fx / width / Widthscale
focallengthsy = fy / width        # NOT fy/height — TD normalizes both against width
centerx       = cx / width
centery       = cy / height
```

`Widthscale` (default ~1.05) fine-tunes horizontal aspect if the cloud looks squashed.

### Bypassed / legacy

| Node | Why |
|------|-----|
| `unproject` (scriptCHOP) | v4 CPU path — replaced by TOP to POP |
| `geo1/delete_zero` | Depth culling POP — bypassed; caused issues when active |
| v4 CHOP instancing (`circle1`, `ps` channel) | Replaced by lineMAT point draw |

## Control scripts

| Node | Type | Role |
|------|------|------|
| `load_take` | textDAT | `onPulse`, `setup_io`, `setup_gpu`, `update_frames`, `cook_playback`, camera helpers |
| `par_exec` | parameterExecuteDAT | Reacts to custom parm changes |
| `frame_driver` | executeDAT | `onFrameStart` — advances playback when `Play` on |

## Playback model

### What works (v5)

| Control | Mechanism |
|---------|-----------|
| Scrub | `Frame` parm → `par_exec` → `update_frames` → `cook_playback` |
| Play | `frame_driver.onFrameStart` increments `Frame`, calls `update_frames` + `cook_playback` |
| FPS | `Fps` parm → `project.cookRate` when `Play` toggled on |

`par_exec` must list every watched parm in `par.pars`, including **`Play`** and **`Cameramode`**.

While `Play` is on, `par_exec` **skips** `Frame` changes (avoids double-cooking if Frame callbacks fire).

### Frame loading — critical detail

Movie File In **can** detect folder sequences (`trueNumImages ≈ 5004` when `par.file` points at `depth_aligned/` with `imageindexing=zero`). However, **folder index + `reloadpulse` is ~2× slower** than explicit per-frame paths.

**Use explicit paths in `update_frames()`:**

```
{take}/depth_aligned/frame_{frame:06d}.exr
{take}/color/frame_{frame:06d}.png
```

Then `reloadpulse` on both inputs and cook. Do **not** rely on `par.index` alone — index changes without reload do not update pixels for EXR folder mode.

### Performance (measured Jul 2026, take-02, 1280×720)

| Stage | Time |
|-------|------|
| Depth EXR reload | ~64 ms |
| Color PNG reload | ~90 ms |
| **Full I/O (explicit paths + reload)** | **~60–65 ms** |
| Folder index + reload (old approach) | ~150 ms |
| GPU POP chain + render | **~0.3 ms** |
| Orbit camera math | ~0 ms |
| Auto camera (`poptoDAT` centroid) | **~280 ms** |

**Ceiling with raw sequences:** ~15 fps (Orbit mode). User observed ~4 fps before fixes (folder index + overhead). **30 fps requires video proxies** — see pitfalls and blender-parity docs.

### What does *not* work for fast scrub/load

| Approach | Result |
|----------|--------|
| `preload(index)` | Updates `trueIndex` but **does not load pixels** |
| `cuepulse` | Fast but **stale/wrong image data** |
| `reloadpulse` without index change | Required for actual frame swaps |
| Sequential `playmode` in a single cook loop | Does not advance (needs timeline time steps) |
| `prereadframes` | Does not speed up per-frame `reloadpulse` |
| `highperfread` | Negligible benefit for EXR folders |
| Half-res `outputresolution` | Still decodes full EXR from disk |

## FX insertion

```
depth_in → [your TOPs] → depth_null → … → topto
color_in → [your TOPs] → color_null → lookup_color
```

Frame loading still targets `depth_in` / `color_in`. Null outputs feed the GPU chain.

## Camera modes

| Mode | Behavior | Playback cost |
|------|----------|---------------|
| `Orbit` | User-controlled azimuth / elevation / distance around pivot | Cheap |
| `Auto` | Reframes from cloud centroid via `poptoDAT` each update | **Expensive** — avoid during play |

`center_orbit` pulse samples centroid once and sets orbit pivot parms.

## Critical render requirements (v5)

1. `geo1/null_pop` must have **`render=True`** (other POPs off)
2. `render1.par.camera = cam1`, `render1.par.geometry = geo1`
3. `linemat.par.drawpoints = True`
4. `depth_cam` separate from `cam1` — do not orbit the unprojection camera

## Future optimization paths

| Approach | Benefit | Status |
|----------|---------|--------|
| **HAP / ProRes proxy movies** | Hardware decode, ~30 fps playback | Not wired — top priority for real-time preview |
| Explicit file paths (not folder index) | ~2× faster than folder reload | **Done in v5** |
| FFV1 MKV for lossless depth proxy | Smaller + faster than per-file EXR | Needs ffmpeg + `preview/` folder convention |
| Pre-baked point cache (USD / PLY sequence) | No per-frame unproject | Not started |
| Re-enable `delete_zero` depth cull | Fewer points | Bypassed — needs correct wiring |

## v4 reference (superseded)

v4 used CHOP instancing from `scriptCHOP` `unproject`. See git history and `pointcloud-viewer-v4/` if needed. Do not mix v4 CHOP and v5 POP paths in the same network.
