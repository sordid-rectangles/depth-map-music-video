# Kinect MKV Export

Converts an Azure Kinect MKV recording into take-scoped image sequences for
Blender and TouchDesigner.

## Requirements

- [uv](https://docs.astral.sh/uv/) — no manual venv or `pip install` needed
- Azure Kinect SDK installed (same requirement as `operator.exe`) — `pyk4a`
  wraps the SDK's native `k4a` library and won't build without it

## Usage

```
uv run export.py <take.mkv> --out <export_root>
```

Multiple takes in one call:

```
uv run export.py take-01-*.mkv take-02-*.mkv --out E:\EXPORTS
```

Flags (color, depth, and depth_aligned export by default):

| Flag | Effect |
|------|--------|
| `--no-color` | Skip color frames |
| `--ir` | Include IR frames (off by default) |
| `--no-depth-aligned` | Skip color-aligned depth (also skipped automatically if the recording has no color track, e.g. the `Depth Ref` preset) |
| `--max-frames N` | Stop after N frames (quick test / partial export) |

## Output layout

```
<export_root>/
  take-01-20260622-175023/
    depth/            frame_000001.exr   raw depth, depth-camera space, float32 mm
    depth_aligned/    frame_000001.exr   depth reprojected into color-camera space
    color/            frame_000001.png
    ir/               frame_000001.exr   (only when exported with --ir)
    calibration.json
    manifest.json
```

Frame numbers start at **1** (not 0) to match Blender's default scene start
frame. Subfolders are only created for streams actually present in the
source MKV.

`depth_aligned/` is the one to use for a Blender point cloud alongside
`color/` — both share the same pixel grid and the same `color` intrinsics in
`calibration.json`, so no depth-to-color reprojection math is needed in the
Blender node group.

## `calibration.json`

```json
{
  "depth":  { "fx": ..., "fy": ..., "cx": ..., "cy": ..., "distortion": [k1, k2, p1, p2, k3, k4, k5, k6] },
  "color":  { "fx": ..., "fy": ..., "cx": ..., "cy": ..., "distortion": [k1, k2, p1, p2, k3, k4, k5, k6] }
}
```

`fx/fy/cx/cy` are the OpenCV-convention camera-matrix values needed to
unproject a depth pixel into 3D:

```
X = (px - cx) * depth / fx
Y = (py - cy) * depth / fy
Z = depth
```

## `manifest.json`

```json
{
  "source_filename": "take-01-20260622-175023.mkv",
  "source_size_bytes": 48213932032,
  "source_mtime": "2026-06-22T17:52:10+00:00",
  "exported_at": "2026-07-07T14:32:10+00:00",
  "tool_version": "1.0.0",
  "frame_count": 900,
  "fps": 30,
  "has_color": true,
  "has_ir": true,
  "has_depth_aligned": true
}
```

`source_filename` + `source_size_bytes` (not the full source path) are the
take's identity. Recordings come off an external drive that may mount under
a different path or drive letter each session, so matching by path isn't
reliable — matching by filename + size is. A take is considered **stale**
only when a file with the same name is found on the source drive with a
different size/mtime than what's recorded here (i.e. someone re-recorded
over the same take number) — a missing source file (drive unplugged, card
wiped after ingest) is expected and not an error.

`frame_count` and `fps` let a downstream tool (the planned Blender add-on,
or the `operator.exe` export session screen) set a timeline range or batch
progress bar without re-scanning the output folder.

## Progress output

Designed to be driven by another process. Progress is reported on stdout as
single-line markers:

```
TAKE take-01-20260622-175023.mkv
FRAME 1
FRAME 2
...
DONE
```

Errors are reported as `ERROR <message>` and exit with a non-zero status.

## Downstream playback notes

TouchDesigner v5 testing (Jul 2026) on raw EXR + PNG sequences:

- GPU point-cloud reconstruction is cheap (~0.3 ms/frame).
- Disk I/O dominates: ~60–65 ms/frame best case (~15 fps), not 30 fps.
- **30 fps preview** likely needs proxy video files baked from these sequences (see [`touchdesigner/docs/blender-parity.md`](../../touchdesigner/docs/blender-parity.md#playback--performance)).

Blender should use native image sequences rather than TD's per-frame file-reload pattern. Next agent work: Blender playback options.

## Status

Built and syntax-checked. **Not yet run against a real MKV** — `pyk4a` is a
C extension wrapping the Azure Kinect SDK's native `k4a` library, which only
exists on the Windows recording machine, so it can't be exercised on the dev
machine this was written on. First real test needs to happen there.
