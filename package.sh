#!/usr/bin/env bash
# Build the Linux package: dist/pac-man-linux/ and dist/pac-man-linux.tar.gz.
# Usage: make package, or PYTHON=/path/to/python ./package.sh
set -euo pipefail
# Work from the repository root wherever the script is started from, so
# only this project's build/ and dist/ folders are ever deleted.
cd -- "$(dirname -- "$0")"
PYTHON="${PYTHON:-python3}"

# Stop before deleting anything if a dependency is missing: PyInstaller
# would otherwise build a game that cannot start.
"$PYTHON" -c "import pygame, mazegenerator, PyInstaller" 2>/dev/null || {
    echo "Error: missing build dependencies, run make install" >&2
    exit 1
}

# Start from scratch, so no score file from a test run is shipped.
rm -rf build dist

# Build the game folder dist/pac-man (onedir) from the spec.
"$PYTHON" -m PyInstaller --noconfirm --clean pac-man.spec

# Create the package folder.
mkdir -p dist/pac-man-linux

# The launcher players start (it keeps its executable bit).
cp packaging/run.sh dist/pac-man-linux/run.sh

# Settings, instructions and credits, next to the game so players can
# read and edit them.
cp config.json dist/pac-man-linux/config.json
cp packaging/INSTRUCTIONS.txt dist/pac-man-linux/INSTRUCTIONS.txt
cp packaging/CREDITS.txt dist/pac-man-linux/CREDITS.txt

# Move the game folder into the package (no second copy is left behind).
mv dist/pac-man dist/pac-man-linux/pac-man

# tar.gz keeps the executable bits; files owned by root (uid 0) can be
# extracted by anyone, including root.
tar --owner=0 --group=0 -czf dist/pac-man-linux.tar.gz \
    -C dist pac-man-linux

echo "Package created: dist/pac-man-linux.tar.gz"
