#!/bin/bash
# Construit l'archive distribuée aux utilisateurs : dist/Kit-migration-Arc-Chrome-vX.Y.Z.zip
# Usage : bash scripts/construire-archive.sh
set -euo pipefail

cd "$(dirname "$0")/.."
VERSION="$(python3 -c 'import migrer_arc_chrome as m; print(m.__version__)')"
NAME="Kit-migration-Arc-Chrome"
ARCHIVE="dist/$NAME-v$VERSION.zip"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$STAGE/$NAME" dist
cp migrer-arc-vers-chrome.sh remplacer-tous-les-espaces.sh diagnostic-favoris.sh migrer_arc_chrome.py \
  correspondance.txt LISEZMOI.txt README.md CLAUDE.md LICENSE "$STAGE/$NAME/"
chmod +x "$STAGE/$NAME/"*.sh
rm -f "$ARCHIVE"
(cd "$STAGE" && zip -rqX - "$NAME") > "$ARCHIVE"
echo "$ARCHIVE"
