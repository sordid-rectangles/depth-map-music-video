# Depth Map Music Video

Two parallel pipelines for depth-aware footage:

| Folder | What it does |
|--------|-------------|
| [`kinect/`](kinect/) | Recording tool for the Azure Kinect DK — for on-set operators |
| [`depth-anything/`](depth-anything/) | Processing regular camera footage through Depth Anything to generate depth maps |
| [`touchdesigner/`](touchdesigner/) | TouchDesigner viewer for exported Kinect depth takes — see [`touchdesigner/docs/`](touchdesigner/docs/) |
| [`blender/`](blender/) | Blender add-on for Kinect point clouds — artists: [`blender/ARTIST_GUIDE.md`](blender/ARTIST_GUIDE.md) |

## Quick start

- **On-set team (Windows)** → double-click `kinect/operator.exe`, or see [`kinect/README.md`](kinect/README.md)
- **Post / depth processing** → see [`depth-anything/README.md`](depth-anything/README.md)
