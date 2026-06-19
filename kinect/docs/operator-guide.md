# On-set Operator Guide — Azure Kinect DK

This guide is written for non-technical team members operating the Kinect camera on set.

---

## Before you start (one-time setup by a technical team member)

Open `kinect\scripts\config.bat` in Notepad and confirm the path matches where the Azure Kinect SDK is installed on this machine. The default is:

```
C:\Program Files\Azure Kinect SDK v1.4.1\tools\k4arecorder.exe
```

If the SDK was installed to a different folder, update that line and save. Operators don't need to touch this file again.

## On set

1. Plug the Kinect into a **USB 3** port (the blue ones).
2. Make sure the device is recognized by Windows (you'll hear the usual USB connect sound).
3. Open **File Explorer** and navigate to the `kinect\scripts` folder.

---

## Step 1 — Confirm the Kinect is connected

Double-click **`list-devices.bat`**.

You should see something like:

```
Found 1 connected devices:
  Device 0: ...
```

If it says "Found 0 connected devices", unplug and replug the Kinect and try again.

---

## Step 2 — Record a take

### Option A: Record until you're done (open-ended)

Double-click **`record.bat`**.

- Type a filename when asked, e.g. `scene-02-take-01`, then press Enter.
- Recording starts immediately.
- **Press Ctrl-C** to stop.
- The file is saved as `scene-02-take-01.mkv` in the same folder.

### Option B: Record for a fixed number of seconds

Double-click **`record-timed.bat`**.

- Type a filename, press Enter.
- Type the number of seconds (e.g. `30`), press Enter.
- Recording stops automatically.

---

## File naming convention

Use lowercase with hyphens:

```
scene-<number>-take-<number>.mkv
```

Examples: `scene-01-take-01.mkv`, `scene-03-take-02.mkv`

---

## What gets recorded

Each `.mkv` file contains:

| Stream | Settings |
|--------|----------|
| RGB color | 1440p @ 30fps |
| Depth | WFOV 2×2 binned @ 30fps |
| IMU (motion sensor) | Off |
| Audio | Not recorded (k4arecorder never captures audio) |

---

## Troubleshooting

| Problem | Try this |
|---------|----------|
| "The system cannot find the path specified" | The path in `scripts\config.bat` doesn't match where the SDK is installed on this machine. A technical team member should open `config.bat` in Notepad and update the path. |
| "Found 0 connected devices" | Unplug and replug. Use USB 3 (blue port). Avoid USB hubs. |
| Black color image | Try the Azure Kinect Viewer app to adjust exposure before recording. |
| Recording stops immediately | Check available disk space. |

---

## After the shoot

Copy the `.mkv` files to the shared drive as soon as possible — they are large files and should not stay on the local machine.
