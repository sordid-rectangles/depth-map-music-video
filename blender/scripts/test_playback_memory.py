"""Hunt for a memory leak during playback.

Scrubs many frames (driving the real frame_change handler -> rebuild) and prints
the process working-set every 100 frames. Flat memory = no leak; steady growth
= a leak to bisect.

Run: blender --background --python test_playback_memory.py
"""
import ctypes
import ctypes.wintypes as wt
import sys
from pathlib import Path

for n in list(sys.modules):
    if n.startswith("kinect_pointcloud"):
        del sys.modules[n]

sys.path.insert(0, r"C:\Users\bonk\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons")

import bpy


class PMC(ctypes.Structure):
    _fields_ = [
        ("cb", wt.DWORD),
        ("PageFaultCount", wt.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


_GetProcessMemoryInfo = ctypes.windll.psapi.GetProcessMemoryInfo
_GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]
_GetProcessMemoryInfo.restype = wt.BOOL
_GetCurrentProcess = ctypes.windll.kernel32.GetCurrentProcess
_GetCurrentProcess.restype = wt.HANDLE


def rss_mb():
    c = PMC()
    c.cb = ctypes.sizeof(PMC)
    ok = _GetProcessMemoryInfo(_GetCurrentProcess(), ctypes.byref(c), c.cb)
    if not ok:
        return -1.0
    return c.WorkingSetSize / (1024 * 1024)


def datablock_counts():
    return {
        "images": len(bpy.data.images),
        "meshes": len(bpy.data.meshes),
        "materials": len(bpy.data.materials),
        "node_groups": len(bpy.data.node_groups),
        "objects": len(bpy.data.objects),
    }


bpy.ops.wm.read_factory_settings(use_empty=True)

import kinect_pointcloud as addon
from kinect_pointcloud import import_take

addon.register()

TAKE = Path(r"C:\Users\bonk\repos\chippy-crybb-vid\kinect-exports\take-02-20260623-150614")
scene = bpy.context.scene
settings = scene.kinect_take
settings.take_path = str(TAKE)
import_take.load_take(bpy.context)

print("build", addon.ADDON_BUILD)


def run(label, n):
    print(f"=== {label} (baked_cache={settings.use_baked_cache}) ===")
    print("  start rss:", round(rss_mb(), 1), "MB", datablock_counts())
    for f in range(1, n + 1):
        scene.frame_set(f if f <= settings.frame_count else settings.frame_count)
        if f % 200 == 0:
            print(f"  frame {f}: rss {round(rss_mb(),1)} MB", datablock_counts())
    print(f"  end rss: {round(rss_mb(),1)} MB")


settings.use_baked_cache = True
run("BAKED playback", 1500)

settings.use_baked_cache = False
run("LIVE decode playback", 400)

print("DONE")
