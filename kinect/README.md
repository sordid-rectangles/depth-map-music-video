# Kinect

CLI tools wrapping `k4arecorder.exe` from the Azure Kinect SDK for on-set use by non-technical operators.

## Prerequisites

- Azure Kinect SDK installed on the Windows machine
- `k4arecorder.exe` in your PATH (typically `C:\Program Files\Azure Kinect SDK v1.4.x\tools\`)
- Azure Kinect DK plugged in via USB 3

## Scripts

| Script | Use |
|--------|-----|
| [`scripts/list-devices.bat`](scripts/list-devices.bat) | Confirm the Kinect is recognized before shooting |
| [`scripts/record.bat`](scripts/record.bat) | Start recording until you press Ctrl-C |
| [`scripts/record-timed.bat`](scripts/record-timed.bat) | Record for a set number of seconds |

## Non-technical operators

See the full step-by-step guide: [`docs/operator-guide.md`](docs/operator-guide.md)
