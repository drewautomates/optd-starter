#!/bin/bash
# Deploy ACSIL study sources into a Sierra Chart ACS_Source folder.
#
# Copies every .cpp and .h in sierra/studies/ into the ACS_Source folder of a
# Sierra Chart installation. Afterwards, rebuild inside Sierra Chart:
#   Analysis > Build Custom Studies DLL
#
# There is deliberately NO default target. Sierra Chart installs somewhere
# different on every machine, so the target must come from one of:
#
#   1. argument 1
#   2. the OPTD_SC_ACS_SOURCE environment variable
#
# If neither is set the script stops and tells you how to set one. It never
# guesses a path.
#
# Usage:
#   bash sierra/scripts/deploy.sh "/path/to/SierraChart/ACS_Source"
#   OPTD_SC_ACS_SOURCE="/path/to/SierraChart/ACS_Source" bash sierra/scripts/deploy.sh
#
# On Windows under Git Bash a path looks like /c/SierraChart/ACS_Source;
# under WSL, /mnt/c/SierraChart/ACS_Source.

set -u

# Resolve the source folder relative to this script, never from a fixed path,
# so the repo works wherever it is cloned.
SIERRA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE_DIR="$SIERRA_DIR/studies"

TARGET="${1:-${OPTD_SC_ACS_SOURCE:-}}"

if [ -z "$TARGET" ]; then
    echo "ERROR: no target ACS_Source folder specified."
    echo ""
    echo "  Pass it as argument 1:"
    echo "    bash sierra/scripts/deploy.sh \"/path/to/SierraChart/ACS_Source\""
    echo ""
    echo "  Or set it once for the session:"
    echo "    export OPTD_SC_ACS_SOURCE=\"/path/to/SierraChart/ACS_Source\""
    echo ""
    echo "  ACS_Source sits inside your Sierra Chart installation folder. It is the"
    echo "  folder Analysis > Build Custom Studies DLL compiles from."
    exit 1
fi

echo "Source : $SOURCE_DIR"
echo "Target : $TARGET"
echo ""

if [ ! -d "$SOURCE_DIR" ]; then
    echo "ERROR: source folder not found: $SOURCE_DIR"
    exit 1
fi
if [ ! -d "$TARGET" ]; then
    echo "ERROR: target ACS_Source not found: $TARGET"
    echo "       Check the path, or point argument 1 at the right Sierra Chart install."
    exit 1
fi

count=0
for src in "$SOURCE_DIR"/*.cpp "$SOURCE_DIR"/*.h; do
    [ -f "$src" ] || continue
    name=$(basename "$src")
    cp "$src" "$TARGET/$name"
    printf "  deployed    %-34s %8s bytes\n" "$name" "$(wc -c < "$src" | tr -d ' ')"
    count=$((count + 1))
done

echo ""
if [ "$count" -eq 0 ]; then
    echo "Nothing to deploy - no .cpp or .h files in sierra/studies/."
    exit 0
fi

echo "Deployed $count file(s) to $TARGET"
echo ""
echo "Next: in Sierra Chart -> Analysis > Build Custom Studies DLL > Build > OPTD_Studies"
echo "      Then on the chart -> Analysis > Studies > Add Custom Study."
echo "      A study already on the chart picks up new CODE on rebuild, but changed"
echo "      DEFAULTS/colors/draw styles only appear if you remove and re-add it."
