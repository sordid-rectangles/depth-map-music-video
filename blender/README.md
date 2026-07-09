# Kinect Point Cloud — Blender

Load exported Kinect takes for preview, cameras, and stylized point-cloud renders.  
Pairs with [`kinect/export/`](../kinect/export/) — no export changes needed.

**→ Artists start here: [`ARTIST_GUIDE.md`](ARTIST_GUIDE.md)** (install, test run, pitfalls)

## Layout

```
KINECT/
  CloudData     ← add-on writes timed points (hidden)
  CloudRender   ← default viewport look (Geometry Nodes)
  Cameras/Orbit ← optional starter rig
```

Default CloudRender: `Object Info (CloudData) → Mesh to Points → Output`

## Dev

- Add-on: [`kinect_pointcloud/`](kinect_pointcloud/)
- Package zip: `scripts/package_addon.ps1`
- TouchDesigner parity: [`../touchdesigner/docs/blender-parity.md`](../touchdesigner/docs/blender-parity.md)
