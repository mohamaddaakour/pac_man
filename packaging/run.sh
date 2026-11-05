#!/bin/sh
# Start Pac-Man with the config.json next to this script, or with the
# configuration file given as the first argument. Works from any folder.

# Absolute path of the folder holding this script.
here="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
game="$here/pac-man/pac-man"
# Some download or unzip tools drop the executable bit: restore it.
[ -x "$game" ] || chmod +x "$game"
# exec replaces this shell with the game, so the game's exit code is
# the script's.
exec "$game" "${1:-$here/config.json}"
