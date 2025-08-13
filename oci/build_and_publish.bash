#!/bin/bash
set -euo pipefail

# Enable debug output if DEBUG env var is set
[[ "${DEBUG:-}" == "1" ]] && set -x

# Functions
log()    { echo "[INFO] $*"; }
warn()   { echo "[WARN] $*" >&2; }
error()  { echo "[ERROR] $*" >&2; exit 1; }

require_command() {
    command -v "$1" >/dev/null 2>&1 || error "Missing required command: $1"
}

# Check prerequisites
require_command podman
require_command systemctl

# Enable podman.socket for user
log "Enabling podman.socket for user"
systemctl --user enable --now podman.socket

# Variables
NOW="$(date +"%Y%m%dT%H%M")"
IMG_NAME="idrac_to_kafka"
DOCKERFILE="Dockerfile.idrac_to_kafka"
IMG_REGISTRY="my_registry"
FULL_IMAGE="$IMG_REGISTRY/$IMG_NAME:$NOW"

echo '[>>] Are we using a sock5 proxy to the image registry? (e.g. PROXY="socks5://127.0.0.1:1926"'
if [[ -v PROXY ]]; then
  echo "[OK] Found Proxy"
  export https_proxy=$PROXY
else
  echo "[--] No proxy"
fi

# Login check
if podman search --list-tags --limit 1 "$IMG_REGISTRY/$IMG_NAME" >/dev/null 2>&1; then
  log "Registry $IMG_REGISTRY is accessible."
else
  warn "Not logged in to $IMG_REGISTRY. Attempting login..."
  podman login "$IMG_REGISTRY" --username "jstile" || error "Failed to login to $IMG_REGISTRY"
fi

# Build image
log "Building image $IMG_NAME:$NOW"
# Need to disable the proxy during image build
http_proxys= podman build --no-cache . -f "$DOCKERFILE" --tag "$IMG_NAME:$NOW"

# Tag image
log "Tagging image as $FULL_IMAGE"
podman tag "$IMG_NAME:$NOW" "$FULL_IMAGE"

CHAR_VALUES_FILE="../values/idrac-to-kafka.yaml"
echo "[>>] UPDATE image in $CHAR_VALUES_FILE"
if [ -f "$CHAR_VALUES_FILE" ]; then
  (
    sed -i "s|image:.*|image: $FULL_IMAGE|g" "$CHAR_VALUES_FILE" 
    echo "Chart Values file patched"
  )
else
    echo "Chart Values file not found"
fi

# Push image
read -p "[>>] PUSH to $FULL_IMAGE? [y/N]" DO_PUSH_REMOTE
if [ "$DO_PUSH_REMOTE" == 'y' ]; then
  log "[>>] Pushing image to $FULL_IMAGE"
  podman push --format=docker "$FULL_IMAGE"
  log "[OK] Image pushed: $FULL_IMAGE"
fi

echo "[--] DONE"
