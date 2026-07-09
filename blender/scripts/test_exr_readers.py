import bpy
print("blender ok")
try:
    import OpenImageIO as oiio
    print("OIIO", oiio.VERSION_STRING)
except Exception as e:
    print("OIIO fail", e)

try:
    import OpenEXR
    print("OpenEXR", OpenEXR.__file__)
except Exception as e:
    print("OpenEXR fail", e)

path = r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614\depth_aligned\frame_000001.exr"

try:
    import OpenImageIO as oiio
    inp = oiio.ImageInput.open(path)
    spec = inp.spec()
    print("spec", spec.width, spec.height, spec.channelnames, spec.format)
    pixels = inp.read_image(format=oiio.FLOAT)
    print("pixels type", type(pixels), len(pixels) if hasattr(pixels,'__len__') else pixels)
    inp.close()
except Exception as e:
    import traceback; traceback.print_exc()

print("done")
