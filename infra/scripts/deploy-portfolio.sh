#!/usr/bin/env bash
# Atomic zero-downtime deployment script for ~/portfolio on the Beelink SER.
# Install path: /srv/hosted-layer/scripts/deploy-portfolio.sh
# Runs as the unprivileged `deploy` user (no root, no docker group required).
#
# Usage:
#   1. From GitHub Actions over SSH (tar.gz on stdin):
#        ssh deploy@beelink "/srv/hosted-layer/scripts/deploy-portfolio.sh <sha>" < dist.tar.gz
#   2. With SSH authorized_keys forced-command restriction:
#        restrict,command="/srv/hosted-layer/scripts/deploy-portfolio.sh" ssh-ed25519 ...
#   3. From local rebuild-stale.sh:
#        deploy-portfolio.sh --from-dir /tmp/staged-dist <release-id>

set -euo pipefail
umask 022

BASE="${PORTFOLIO_BASE:-/srv/hosted-layer/portfolio}"
RELEASES_DIR="${BASE}/releases"
CURRENT_LINK="${BASE}/current"
LOCK_FILE="${BASE}/.deploy.lock"
LOOPBACK_URL="${PORTFOLIO_LOOPBACK_URL:-http://127.0.0.1:8787}"
KEEP_RELEASES="${KEEP_RELEASES:-5}"

FROM_DIR=""
RELEASE_ID=""

if [[ "${1:-}" == "--from-dir" ]]; then
  FROM_DIR="${2:-}"
  RELEASE_ID="${3:-}"
elif [[ -n "${1:-}" ]]; then
  RELEASE_ID="$1"
elif [[ -n "${SSH_ORIGINAL_COMMAND:-}" ]]; then
  # Support restricted authorized_keys: extract final token as release ID.
  read -r -a orig_parts <<< "${SSH_ORIGINAL_COMMAND}"
  RELEASE_ID="${orig_parts[-1]:-}"
fi

if [[ -z "$RELEASE_ID" ]]; then
  RELEASE_ID="manual"
fi

if [[ ! "$RELEASE_ID" =~ ^[A-Za-z0-9._-]{1,64}$ ]]; then
  echo "ERROR: invalid release id: ${RELEASE_ID}" >&2
  exit 1
fi

mkdir -p "$RELEASES_DIR"

exec 9>"$LOCK_FILE"
flock -w 60 9 || { echo "ERROR: could not acquire deploy lock" >&2; exit 1; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RELEASE_NAME="${STAMP}-${RELEASE_ID}"
STAGE_DIR="${RELEASES_DIR}/.staging-${RELEASE_NAME}"
TARGET_DIR="${RELEASES_DIR}/${RELEASE_NAME}"

cleanup() {
  rm -rf "$STAGE_DIR" "${BASE}/current.next"
}
trap cleanup EXIT

mkdir -p "$STAGE_DIR"

if [[ -n "$FROM_DIR" ]]; then
  if [[ ! -d "$FROM_DIR" ]]; then
    echo "ERROR: --from-dir does not exist: ${FROM_DIR}" >&2
    exit 1
  fi
  cp -a "${FROM_DIR}/." "$STAGE_DIR/"
else
  # Extract dist tarball streamed on stdin without honoring archive uid/gid/mode.
  tar --no-same-owner --no-same-permissions -xzf - -C "$STAGE_DIR"
fi

# Verify mandatory static files exist before touching live traffic.
REQUIRED_FILES=(
  "index.html"
  "ledger.json"
  "style.css"
  "not-done/index.html"
  "ledger/index.html"
  "projects/index.html"
  "about/index.html"
  "fonts/BarlowCondensed-SemiBold.ttf"
  "fonts/BarlowCondensed-ExtraBold.ttf"
)
for rel in "${REQUIRED_FILES[@]}"; do
  if [[ ! -f "${STAGE_DIR}/${rel}" ]]; then
    echo "ERROR: staged release missing required file: ${rel}" >&2
    exit 1
  fi
done

tree_hash() {
  (
    cd "$1"
    LC_ALL=C find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}'
  )
}

NEW_HASH="$(tree_hash "$STAGE_DIR")"
PREV_TARGET=""
if [[ -L "$CURRENT_LINK" && -d "$CURRENT_LINK" ]]; then
  PREV_TARGET="$(readlink "$CURRENT_LINK")"
  OLD_HASH="$(tree_hash "$CURRENT_LINK")"
  if [[ "$NEW_HASH" == "$OLD_HASH" ]]; then
    echo "No content change detected (tree sha256 ${NEW_HASH:0:16}); skipping swap."
    exit 0
  fi
fi

# Ensure world-readable static assets for the Caddy container.
chmod -R a+rX "$STAGE_DIR"
mv "$STAGE_DIR" "$TARGET_DIR"

# Relative symlink so Caddy's parent bind mount (/srv/portfolio:ro) follows swaps atomically.
ln -sfn "releases/${RELEASE_NAME}" "${BASE}/current.next"
mv -Tf "${BASE}/current.next" "$CURRENT_LINK"

# Loopback smoke check against live Caddy container; auto-rollback on failure.
SMOKE_ROUTES=(
  "/healthz"
  "/"
  "/ledger/"
  "/not-done/"
  "/projects/"
  "/about/"
  "/ledger.json"
  "/style.css"
)

smoke_ok=1
for route in "${SMOKE_ROUTES[@]}"; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "${LOOPBACK_URL}${route}" || echo "000")"
  if [[ "$code" != "200" ]]; then
    echo "ERROR: loopback smoke check failed: ${LOOPBACK_URL}${route} -> HTTP ${code}" >&2
    smoke_ok=0
    break
  fi
done

if [[ "$smoke_ok" -ne 1 ]]; then
  if [[ -n "$PREV_TARGET" ]]; then
    echo "Rolling back current -> ${PREV_TARGET}" >&2
    ln -sfn "$PREV_TARGET" "${BASE}/current.next"
    mv -Tf "${BASE}/current.next" "$CURRENT_LINK"
  fi
  rm -rf "$TARGET_DIR"
  exit 1
fi

# Prune old releases, retaining newest KEEP_RELEASES and never removing active release.
ACTIVE_BASENAME="$(basename "$(readlink "$CURRENT_LINK")")"
mapfile -t ALL_RELEASES < <(find "$RELEASES_DIR" -mindepth 1 -maxdepth 1 -type d ! -name '.staging-*' -printf '%f\n' | sort -r)
count=0
for dir in "${ALL_RELEASES[@]}"; do
  count=$((count + 1))
  if [[ "$count" -gt "$KEEP_RELEASES" && "$dir" != "$ACTIVE_BASENAME" ]]; then
    rm -rf "${RELEASES_DIR}/${dir}"
  fi
done

echo "Deployed ${RELEASE_NAME} (tree sha256 ${NEW_HASH:0:16}; kept up to ${KEEP_RELEASES} releases)."
