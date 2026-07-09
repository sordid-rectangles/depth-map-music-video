# Unproject math

Pinhole unprojection for Kinect `depth_aligned` + `color` takes. Same math applies to Blender geometry nodes or a Python importer.

## Source files

From [`kinect/export/README.md`](../../kinect/export/README.md):

```
X = (px - cx) * depth / fx
Y = (py - cy) * depth / fy
Z = depth
```

- `depth` in exported EXR: **float32 millimeters**
- Use **`color`** intrinsics from `calibration.json` (not `depth`) when reading `depth_aligned/`
- `px`, `py` are **image-space** pixel coordinates (origin top-left, +Y down)

## Resolution scaling

Calibration is often for the full color sensor (e.g. 2560×1440) while exports are 1280×720.

After loading the first depth frame at actual `width` × `height`:

```python
scale = width / (cx * 2.0)
fx_s = fx * scale
fy_s = fy * scale
cx_s = cx * scale
cy_s = cy * scale
```

Store scaled values in `calib_const` (constantCHOP).

## TouchDesigner-specific adjustments

### Depth channel

`depth_null.numpyArray()` — depth is in the **alpha channel** (index 3), not red.

### Image row origin

TD `numpyArray()` row 0 is **bottom-left**. Convert to image row:

```python
py = h - 1 - y
```

### Coordinate system

| Space | Convention |
|-------|------------|
| OpenCV / export README | +Z forward, +Y down in image |
| TouchDesigner world | +Y up, camera looks down **-Z** |

```python
tx = (x - cx_s) * z_m / fx_s
ty = -(py - cy_s) * z_m / fy_s   # flip image Y to world Y
tz = -z_m                         # put cloud in front of camera
```

### Units

```python
z_m = z_mm / 1000.0   # mm → meters
```

## Subsampling

```python
req_sub = max(1, int(Subsample))
sub = req_sub
cap = 120000   # max grid cells before depth filter

while ((h + sub - 1) // sub) * ((w + sub - 1) // sub) > cap:
    sub += 1
```

Loop `for y in range(0, h, sub): for x in range(0, w, sub):`.

Do **not** hard-cap with `if len(points) >= N: break` mid-scan — that truncates to a horizontal band and looks broken.

## Depth filtering

```python
if z_mm <= 0: continue
if z_mm < near_mm: continue
if far_mm > 0 and z_mm > far_mm: continue
```

Defaults: near 300 mm, far 6000 mm.

## Output channels (scriptCHOP)

| Channel | Content |
|---------|---------|
| `tx`, `ty`, `tz` | World position (meters) |
| `r`, `g`, `b` | Color from `color_null` at same `(x,y)` |
| `ps` | `Pointsize * 0.015` — instance uniform scale |

## Color sampling

Sample color at the same subsampled `(x, y)` used for depth:

```python
r, g, b = color[y, x, 0], color[y, x, 1], color[y, x, 2]
```

Both depth and color share the same pixel grid when using `depth_aligned/` + `color/`.

## Test take

Used during development:

```
C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614
```

~5005 frames @ 30 fps, 1280×720.

## Validation checks

| Check | Expected |
|-------|----------|
| `unproject.numSamples` at subsample 8 | ~9k points (varies with clip) |
| `tz` range | Negative values (cloud in -Z) |
| Frame 1 vs 1000 mean depth | Different after `update_frames` |
| Y flip | Subject right-side up in render |
