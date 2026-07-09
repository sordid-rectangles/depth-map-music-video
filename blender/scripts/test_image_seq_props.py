import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
path = r"C:/Users/bonk/repos/chippy-crybb-vid/kinect-exports/take-02-20260623-150614/color/frame_000001.png"
img = bpy.data.images.load(path, check_existing=False)
img.source = 'SEQUENCE'
for p in sorted(dir(img)):
    if 'frame' in p.lower() or 'sequence' in p.lower() or 'offset' in p.lower():
        try:
            print(p, getattr(img, p))
        except Exception as e:
            print(p, e)
