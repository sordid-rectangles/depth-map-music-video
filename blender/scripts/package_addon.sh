#!/usr/bin/env bash
# Package the add-on for Blender: Install -> select this zip.
# macOS/Linux counterpart of package_addon.ps1.
set -euo pipefail

out_zip="${1:-kinect_pointcloud.zip}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(dirname "$script_dir")"
addon="$root/kinect_pointcloud"
zip_path="$root/$out_zip"

if [ ! -f "$addon/__init__.py" ]; then
    echo "Expected $addon/__init__.py" >&2
    exit 1
fi

rm -f "$zip_path"

# Zip from the add-on's parent so the archive root is kinect_pointcloud/...
# Drop Python bytecode caches and any baked cache so the handoff zip is clean.
( cd "$root" && zip -r "$zip_path" kinect_pointcloud \
    -x '*/__pycache__/*' \
    -x '*.pyc' \
    -x '*/blender_cache/*' )

echo "Created $zip_path"
echo "In Blender: Edit -> Preferences -> Add-ons -> Install -> pick this zip"
echo "Then fully quit and restart Blender (required after updates)."
