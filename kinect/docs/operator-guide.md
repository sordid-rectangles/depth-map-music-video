# Operator Guide — Azure Kinect DK

For non-technical team members. The short version is in [`kinect/README.md`](../README.md).

---

## One-time setup (done by a technical team member)

**1. Confirm the SDK is installed.**
The tool expects `k4arecorder.exe` at:
```
C:\Program Files\Azure Kinect SDK v1.4.2\tools\k4arecorder.exe
```
If the SDK version on the machine differs, open `operator-config.json` (next to `operator.exe`) in Notepad and update the `recorder_path` value.

**2. Set the output folder.**
Launch `operator.exe`, press **4**, and paste in the path to the recording folder (e.g. `E:\CHIPPYKINECT`). Press Enter to save. This persists across sessions.

**3. Choose a recording preset (optional).**
Press **3** in the menu to select a preset. The default is **Long Take** (1080p / 30fps).

**4. Install `uv` (only needed for exporting takes).**
Exporting takes to image sequences runs a Python script via [`uv`](https://docs.astral.sh/uv/) — install it once (e.g. `winget install astral-sh.uv`). Not needed just to record.

---

## On set

1. Plug the Kinect into a **USB 3** port (blue — not USB 2, not a hub).
2. Wait for Windows to recognize the device (USB connect sound).
3. Double-click **`operator.exe`**.

---

## Recording a take

**Open-ended recording:**

1. Press `1`.
2. Enter a take number (e.g. `3`), press Enter.
3. The file name and output path are shown on screen. Recording starts immediately.
4. Press **Q** to stop. The tool finalizes the file before returning to the menu — wait for it.

**Timed recording:**

1. Press `2`.
2. Enter a take number, press Enter.
3. Enter a duration in seconds (e.g. `30`), press Enter.
4. Recording stops and saves automatically.

Files are saved as `take-03-20260622-175023.mkv` — take number plus a timestamp for uniqueness.

---

## Presets

| Preset | Color | Depth | FPS | Use for |
|--------|-------|-------|-----|---------|
| Primary | 1440p | WFOV 2×2 | 30 | General use |
| Hero Shot | 2160p (4K) | WFOV 2×2 | 30 | Key close-ups |
| Long Take | 1080p | WFOV 2×2 | 30 | Extended takes, smaller files |
| Depth Ref | Off | WFOV 2×2 | 30 | Depth-only VFX pass |

Change preset with **3** in the main menu. Takes effect immediately — no restart needed.

---

## Exporting takes

Converts recorded `.mkv` takes into the depth/color image sequences Blender and TouchDesigner use.

1. Press **5** (or `e`) from the main menu.
2. **Input folder** — where the `.mkv` takes live (usually the external drive from set).
3. **Output folder** — where the exported image sequences are written.
4. You'll see every take found in the input folder, marked:
   - `pending` — not exported yet
   - `exported` — already done, matches what's in the output folder
   - `stale (re-recorded)` — a take with this name was exported before, but the source file has since changed (re-shot under the same take number)
5. Select takes and export:
   - `↑↓` / `j` `k` — move
   - `Space` — select/deselect a take
   - `a` — select all pending + stale takes
   - `x` — export the selected takes (or just the highlighted one if nothing's selected)
   - `r` — rescan the input folder
   - `Esc` — back to the main menu
6. Progress shows per-take as `exporting N/total`. Large takes can take a while — let it finish rather than closing the window.

Requires `uv` installed (see one-time setup above) and the Azure Kinect SDK.

---

## Troubleshooting

| Problem | Try this |
|---------|----------|
| "Failed to start recorder" | The `recorder_path` in `operator-config.json` doesn't match the installed SDK. Update the path. |
| Kinect not responding | Unplug and replug into a USB 3 (blue) port. Avoid USB hubs. |
| Black color image | Open **Azure Kinect Viewer** (`k4aviewer.exe` in the SDK tools folder) and adjust exposure before recording. |
| "File already exists" | The tool detected a name collision — edit the take number and try again. |
| Recording stops immediately | Check available disk space on the output drive. |
| Export fails immediately | Confirm `uv` is installed and on PATH (open a new terminal after installing). |
| Export errors partway through | Usually a bad/incomplete `.mkv` (drive unplugged during recording, etc.) — check the error message shown on screen. |

---

## After the shoot

Copy `.mkv` files to the shared drive as soon as possible. They are large files and should not stay on the local machine.
