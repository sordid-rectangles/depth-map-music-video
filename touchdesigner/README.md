# TouchDesigner

Kinect depth take viewer built in TouchDesigner 099.

| Item | Path |
|------|------|
| Latest project | `pointcloud-viewer-v5/pointcloud-viewer-v5.toe` (save new versions here) |
| Prior version | `pointcloud-viewer-v4/` — CHOP instancing path, superseded by v5 GPU pipeline |
| Documentation | [`docs/`](docs/) |

Open the `.toe`, network is at `/project1/pointcloud_viewer`.

**Status (Jul 2026):** v5 GPU point cloud works (scrub + play). Playback is **I/O-bound** at ~15 fps in Orbit mode with EXR/PNG sequences. See [docs/pitfalls.md](docs/pitfalls.md#playback--io) and [docs/blender-parity.md](docs/blender-parity.md#playback--performance).
