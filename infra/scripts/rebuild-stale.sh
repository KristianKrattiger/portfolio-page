#!/usr/bin/env bash
# Scheduled build-date refresh for ~/portfolio so 90-day STALE badges stay accurate
# even during periods without git commits.
# Install path: /srv/hosted-layer/scripts/rebuild-stale.sh
# Runs weekly via systemd timer (portfolio-stale-rebuild.timer) as the `deploy` user.
# Requires only Python 3 stdlib (no Docker socket, no root).

set -euo pipefail

BASE="${PORTFOLIO_BASE:-/srv/hosted-layer/portfolio}"
REPO_DIR="${BASE}/repo"
DEPLOY_SCRIPT="/srv/hosted-layer/scripts/deploy-portfolio.sh"
BUILD_DATE="$(date +%F)"

if [[ ! -d "${REPO_DIR}/.git" ]]; then
  echo "ERROR: portfolio git checkout not found at ${REPO_DIR}" >&2
  echo "Clone your repo once as deploy: git clone <repo-url> ${REPO_DIR}" >&2
  exit 1
fi

# Fast-forward clean checkout from origin/main.
git -C "$REPO_DIR" fetch --quiet origin main
git -C "$REPO_DIR" reset --hard --quiet origin/main

TMP_OUT="$(mktemp -d "${BASE}/releases/.stale-build-XXXXXX")"
cleanup() {
  rm -rf "$TMP_OUT"
}
trap cleanup EXIT

# Build deterministically for today's date (fails non-zero on any bad ledger).
python3 "${REPO_DIR}/build.py" --out "$TMP_OUT" --date "$BUILD_DATE"

# Verify offline/CI-safe invariants before promoting.
(
  cd "$REPO_DIR"
  python3 verify/verify.py --skip-local-repos --no-write --date "$BUILD_DATE"
)

# deploy-portfolio.sh hashes the staged tree against current and skips swapping if unchanged.
"$DEPLOY_SCRIPT" --from-dir "$TMP_OUT" "stale-${BUILD_DATE//-/}"

if [[ -n "${HEALTHCHECKS_STALE_URL:-}" ]]; then
  curl -fsS --max-time 10 --retry 3 "$HEALTHCHECKS_STALE_URL" > /dev/null
fi
