import numpy as np
import OpenImageIO as oiio

path = r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614\depth_aligned\frame_000001.exr"
inp = oiio.ImageInput.open(path)
spec = inp.spec()
print("channels", spec.channelnames, "size", spec.width, spec.height)
buf = inp.read_image(format=oiio.FLOAT)
inp.close()
arr = np.array(buf, copy=False)
print("arr", type(arr), arr.shape if hasattr(arr,'shape') else len(arr), arr.dtype if hasattr(arr,'dtype') else 'n/a')
if isinstance(arr, np.ndarray):
    if arr.ndim == 1:
        depth = arr.reshape(spec.height, spec.width)
    elif arr.ndim == 2:
        depth = arr
    else:
        depth = arr[:, :, 0]
    print("depth", depth.shape, float(depth.min()), float(depth.max()))
