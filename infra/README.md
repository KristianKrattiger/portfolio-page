# Hosted Layer — Headless EndeavourOS Beelink SER

Infrastructure configs, scripts, systemd units, and CI/CD workflow for self-hosting `~/portfolio` (and future containerized demos or Tailscale research nodes) on a headless **EndeavourOS** Beelink SER mini PC.

## Layout

| Repo path | Install path on Beelink SER | Purpose |
|---|---|---|
| `infra/compose.yaml` | `/srv/hosted-layer/compose.yaml` | Core stack (`caddy`, `cloudflared`, opt-in `uptime-kuma`) |
| `infra/.env.example` | `/srv/hosted-layer/.env` (`chmod 600`) | Cloudflare Tunnel token |
| `infra/caddy/Caddyfile` | `/srv/hosted-layer/caddy/Caddyfile` | Static serving, security headers, `/healthz` |
| `infra/scripts/deploy-portfolio.sh` | `/srv/hosted-layer/scripts/deploy-portfolio.sh` | Atomic release staging, loopback smoke check, rollback |
| `infra/scripts/rebuild-stale.sh` | `/srv/hosted-layer/scripts/rebuild-stale.sh` | Weekly `STALE` date rebuild (stdlib Python, no Docker) |
| `infra/scripts/backup-restic.sh` | `/srv/hosted-layer/scripts/backup-restic.sh` | Nightly encrypted `restic` backup |
| `infra/host/daemon.json` | `/etc/docker/daemon.json` | `live-restore` + 10 MB x 3 container log rotation |
| `infra/host/99-hardening.conf` | `/etc/ssh/sshd_config.d/99-hardening.conf` | Key-only SSH, no root login |
| `infra/host/journald-size.conf` | `/etc/systemd/journald.conf.d/size.conf` | 500 MB NVMe journal cap |
| `infra/host/restic.env.example` | `/etc/hosted-layer/restic.env` (`chmod 600`) | Encrypted backup & Healthchecks.io URLs |
| `infra/host/tailscale-acl.example.json` | Tailscale Admin Console | Restricts `tag:ci` to SSH on `tag:beelink` only |
| `infra/systemd/*` | `/etc/systemd/system/` | Weekly `STALE` timer, nightly backup, 15m heartbeat |
| `.github/workflows/deploy.yml` | GitHub Actions | `unittest` + `build.py` + `verify.py` + Tailscale SSH deploy |

---

## Phase 0 — New GitHub Repo & Domain (Optional Until Ready)

1. Create a new GitHub repository (`KristianKrattiger/portfolio-page`) and push `portfolio`:
   ```bash
   git remote add origin https://github.com/KristianKrattiger/portfolio-page.git
   git branch -M main
   git push -u origin main
   ```
2. **Domain note:** You can set up and test the entire Beelink stack before picking a domain — Caddy listens on `:80` and responds immediately on loopback (`http://127.0.0.1:8787`) and Tailscale. Once you pick a domain and add it to Cloudflare DNS, create the Tunnel public hostname pointing to `http://caddy:80` and set the optional `PORTFOLIO_DOMAIN` GitHub Actions repository variable.

---

## Phase 1 — Beelink BIOS & Headless EndeavourOS Setup

1. **BIOS (with temporary monitor/keyboard):**
   - Enable **Restore on AC Power Loss → Power On**.
   - Disable **Wait for F1 if Error**.
   - Use wired Ethernet (assign a static DHCP lease on your router) and disable Wi-Fi/Bluetooth.
   - Select **Balanced / Quiet** TDP profile.
2. **Install EndeavourOS:**
   - Choose **"No Desktop"** (headless minimal), **Btrfs** filesystem (with `@`, `@home`, `@var_log`, `@srv`, `@snapshots`), and **no full-disk root LUKS** so power-loss reboots recover unattended.
3. **Install baseline server packages & pin `linux-lts` as default kernel:**
   ```bash
   sudo pacman -Syu --needed \
     linux-lts linux-lts-headers \
     snapper snap-pac grub-btrfs \
     docker docker-compose \
     tailscale ufw \
     restic sqlite curl git python \
     smartmontools lm_sensors zram-generator
   ```
   - Set `linux-lts` as the default boot entry (GRUB or `systemd-boot`), reboot, and verify `uname -r` ends in `-lts`.
   - Disable sleep/suspend and enable core timers/services:
     ```bash
     sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
     sudo systemctl enable --now systemd-timesyncd fstrim.timer docker tailscaled smartd
     ```

---

## Phase 2 — Host Hardening, Users & Tailscale

1. Create the unprivileged `deploy` user (no `sudo`, no `docker` group):
   ```bash
   sudo useradd -m -s /usr/bin/bash deploy
   sudo install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
   ```
2. Install host configs:
   ```bash
   sudo install -Dm644 infra/host/daemon.json /etc/docker/daemon.json
   sudo install -Dm644 infra/host/99-hardening.conf /etc/ssh/sshd_config.d/99-hardening.conf
   sudo install -Dm644 infra/host/journald-size.conf /etc/systemd/journald.conf.d/size.conf
   sudo sshd -t && sudo systemctl reload sshd
   sudo systemctl restart systemd-journald docker
   ```
3. Join Tailscale with the server tag and lock down host firewall (replace `192.168.1.0/24` with your LAN CIDR):
   ```bash
   sudo tailscale up --advertise-tags=tag:beelink --ssh=false
   sudo ufw default deny incoming
   sudo ufw default allow outgoing
   sudo ufw allow in on tailscale0 to any port 22 proto tcp
   sudo ufw allow from 192.168.1.0/24 to any port 22 proto tcp
   sudo ufw allow 41641/udp
   sudo ufw enable
   ```
4. Apply the ACL snippet from `infra/host/tailscale-acl.example.json` in your Tailscale Admin Console and create a Tailscale OAuth client with scope `devices:core` (write) tagged `tag:ci`.

---

## Phase 3 — Runtime Stack (`caddy` + `cloudflared`)

1. Provision `/srv/hosted-layer`:
   ```bash
   sudo install -d -m 755 /srv/hosted-layer/{caddy,scripts,data/uptime-kuma}
   sudo install -d -m 755 -o deploy -g deploy /srv/hosted-layer/portfolio/releases
   sudo install -Dm644 infra/compose.yaml /srv/hosted-layer/compose.yaml
   sudo install -Dm644 infra/caddy/Caddyfile /srv/hosted-layer/caddy/Caddyfile
   sudo install -Dm755 infra/scripts/deploy-portfolio.sh /srv/hosted-layer/scripts/deploy-portfolio.sh
   sudo install -Dm755 infra/scripts/rebuild-stale.sh /srv/hosted-layer/scripts/rebuild-stale.sh
   sudo install -Dm700 infra/scripts/backup-restic.sh /srv/hosted-layer/scripts/backup-restic.sh
   sudo install -Dm600 infra/.env.example /srv/hosted-layer/.env
   ```
2. Edit `/srv/hosted-layer/.env` with your `CLOUDFLARE_TUNNEL_TOKEN`, then start the stack:
   ```bash
   cd /srv/hosted-layer
   sudo docker compose up -d
   # Optional: enable Tailscale-only internal monitoring
   # sudo docker compose --profile monitoring up -d
   ```
3. **Cloudflare Dashboard Edge Hygiene (mandatory for `~/portfolio`'s CSP and zero-tracking policy):**
   - **OFF:** Web Analytics / RUM
   - **OFF:** Scrape Shield → Email Address Obfuscation
   - **OFF:** Speed → Optimization → Rocket Loader
   - **OFF:** Speed → Optimization → Speed Brain
   - **ON:** Always Use HTTPS, TLS 1.3, Respect Origin `Cache-Control`
   - Route `<yourdomain.com>` → `http://caddy:80` in the Tunnel's Public Hostname settings.

---

## Phase 4 — GitHub Actions CI/CD & Weekly `STALE` Timer

1. Generate a dedicated Ed25519 deploy keypair on your workstation (`ssh-keygen -t ed25519 -f deploy_beelink -N ""`) and add the public key to `/home/deploy/.ssh/authorized_keys` on the Beelink with a forced-command restriction:
   ```text
   restrict,command="/srv/hosted-layer/scripts/deploy-portfolio.sh" ssh-ed25519 AAAA... github-actions-deploy
   ```
2. Configure GitHub Actions **Repository Secrets** and **Variables**:
   - **Secrets:**
     - `TS_OAUTH_CLIENT_ID` — Tailscale OAuth client ID (`tag:ci`)
     - `TS_OAUTH_SECRET` — Tailscale OAuth client secret
     - `BEELINK_TS_HOST` — Beelink Tailscale MagicDNS name or `100.x.y.z` IP
     - `BEELINK_SSH_HOST_KEY` — Output of `ssh-keyscan -t ed25519 <BEELINK_TS_HOST>` (key portion: `ssh-ed25519 AAAA...`)
     - `DEPLOY_SSH_KEY` — Contents of private key `deploy_beelink`
     - *(Optional once domain is chosen)* `CF_ZONE_ID`, `CF_API_TOKEN`
   - **Variables:**
     - `ENABLE_BEELINK_DEPLOY` — set to `true` once the Beelink SER & secrets above are ready (keeps `main` CI green while only running `verify` beforehand)
     - *(Optional once domain is chosen)* `PORTFOLIO_DOMAIN`
3. Clone the repo once as `deploy` for the weekly `STALE` rebuild timer and enable systemd timers:
   ```bash
   sudo -u deploy git clone https://github.com/KristianKrattiger/portfolio-page.git /srv/hosted-layer/portfolio/repo
   sudo install -Dm644 infra/systemd/* /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now portfolio-stale-rebuild.timer hosted-layer-backup.timer hosted-layer-heartbeat.timer
   ```

---

## Phase 5 — Backups, Rollback & Monthly Maintenance

1. **Initialize encrypted `restic` repo:**
   ```bash
   sudo install -d -m 700 /etc/hosted-layer
   sudo install -Dm600 infra/host/restic.env.example /etc/hosted-layer/restic.env
   # Edit /etc/hosted-layer/restic.env with R2/B2 credentials & Healthchecks.io URLs
   sudo bash -c 'source /etc/hosted-layer/restic.env && restic init'
   sudo systemctl start hosted-layer-backup.service
   ```
2. **Instant rollback (if ever needed):**
   ```bash
   ls -1 /srv/hosted-layer/portfolio/releases
   sudo -u deploy bash -c 'ln -sfn releases/<prev-release> /srv/hosted-layer/portfolio/current.next && mv -Tf /srv/hosted-layer/portfolio/current.next /srv/hosted-layer/portfolio/current'
   ```
3. **Monthly attended Arch maintenance (never unattended cron):**
   - Check `https://archlinux.org/news/`.
   - Run `sudo pacman -Syu` (`snap-pac` creates automatic Btrfs rollback snapshots).
   - Pull updated container images: `cd /srv/hosted-layer && sudo docker compose pull && sudo docker compose up -d`.
   - Reboot if `linux-lts`, `systemd`, `glibc`, or `docker` updated; confirm `curl -sf http://127.0.0.1:8787/healthz`.
