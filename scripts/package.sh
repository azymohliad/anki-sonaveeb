#!/bin/bash

REPO_DIR="$(dirname "$0")/.."
ADDON_DIR="$REPO_DIR/anki_addon"
VERSION=$(cd "$REPO_DIR" && git describe)

cd "$ADDON_DIR"
rm -rf **/__pycache__ __pycache__ meta.json
zip -r ../sonaveeb_integration_$VERSION.ankiaddon *

