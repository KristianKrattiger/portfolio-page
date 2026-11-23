#!/usr/bin/env bash
# Nightly encrypted offsite backup of /srv/hosted-layer configs, secrets, and stateful data.
# Install path: /srv/hosted-layer/scripts/backup-restic.sh
# Runs as root via systemd timer (hosted-layer-backup.timer).
# Expects /etc/hosted-layer/restic.env (chmod 600, root:root).

set -euo pipefail

ENV_FILE="/etc/hosted-layer/restic.env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: missing ${ENV_FILE}" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

SNAP_DIR="$(mktemp -d /tmp/hosted-layer-backup-XXXXXX)"
cleanup() {
  rm -rf "$SNAP_DIR"
}
trap cleanup EXIT

# Consistent SQLite snapshot for Uptime Kuma (never back up a live SQLite DB mid-write).
KUMA_DB="/srv/hosted-layer/data/uptime-kuma/kuma.db"
if [[ -f "$KUMA_DB" ]] && command -v sqlite3 >/dev/null 2>&1; then
  sqlite3 "$KUMA_DB" ".backup '${SNAP_DIR}/kuma.db'"
fi

BACKUP_PATHS=(
  "/srv/hosted-layer"
  "/etc/hosted-layer"
  "/etc/docker/daemon.json"
  "/etc/ssh/sshd_config.d/99-hardening.conf"
  "$SNAP_DIR"
)

restic backup \
  --verbose \
  --exclude="/srv/hosted-layer/portfolio/releases" \
  --exclude="/srv/hosted-layer/portfolio/repo" \
  --exclude="/srv/hosted-layer/data/uptime-kuma/kuma.db*" \
  --exclude="*.tmp" \
  "${BACKUP_PATHS[@]}"

restic forget \
  --keep-daily 7 \
  --keep-weekly 4 \
  --keep-monthly 6 \
  --prune

if [[ -n "${HEALTHCHECKS_BACKUP_URL:-}" ]]; then
  curl -fsS --max-time 10 --retry 3 "$HEALTHCHECKS_BACKUP_URL" > /dev/null
fi
