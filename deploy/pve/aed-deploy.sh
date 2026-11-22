#!/bin/bash
# Auto-deploy of the full portal fork (backend/docker-compose.aed-*.yml) from origin/main.
# Runs in the LXC aed-demo on Proxmox, started every 2 minutes by aed-deploy.timer (docs/wdrozenie-pve.md).
#   aed-deploy.sh            deploy origin/main if it differs from the last deployed commit
#   aed-deploy.sh --force    deploy again even if nothing changed or the commit failed before
# A commit that fails is not retried until a newer one appears (or --force). Logs: journalctl -u aed-deploy.
#
# Two stages: this file as it was before the update fetches and checks out the new commit, then hands over to the
# new commit's copy of itself (--apply), so a change to the deploy steps takes effect in the same deploy.
# Each stage is one function: git replaces this file during the run, bash must have parsed it already.
set -euo pipefail
repo=${AED_REPO_DIR:-/opt/aed}
branch=${AED_BRANCH:-main}
state=${AED_STATE_DIR:-/var/lib/aed-deploy}

update() {
    local force=0
    [ "${1:-}" = "--force" ] && force=1
    mkdir -p "$state"
    exec 9>"$state/lock"  # kept open across exec into the --apply stage
    flock -n 9 || { echo "Wdrożenie już trwa."; return 0; }

    cd "$repo"
    git fetch --quiet origin "$branch"
    local new cur failed
    new=$(git rev-parse "origin/$branch")
    cur=$(cat "$state/deployed" 2>/dev/null || true)
    failed=$(cat "$state/failed" 2>/dev/null || true)
    if [ "$force" = 0 ] && { [ "$new" = "$cur" ] || [ "$new" = "$failed" ]; }; then
        return 0
    fi
    # A commit without the tunnel overlay (e.g. main before this setup was merged) would take the site down.
    if ! git cat-file -e "$new:backend/docker-compose.aed-tunnel.yml" 2>/dev/null \
        || ! git cat-file -e "$new:deploy/pve/aed-deploy.sh" 2>/dev/null; then
        echo "${new:0:7} nie ma nakładki tunelu albo skryptu wdrożenia - pomijam." >&2
        echo "$new" > "$state/failed"
        return 1
    fi
    echo "Wdrożenie ${cur:0:7} -> ${new:0:7}: $(git log -1 --format=%s "$new")"
    # Untracked and ignored files stay: backend/.env, mcod/settings/local.py, media/, logs/, compiled translations.
    git -c advice.detachedHead=false checkout --quiet --force --detach "$new"
    exec bash "$repo/deploy/pve/aed-deploy.sh" --apply "$new"
}

apply() {
    local new=$1
    trap 'echo "$new" > "$state/failed"; echo "Wdrożenie ${new:0:7} NIEUDANE" >&2' ERR
    cd "$repo/backend"
    mkdir -p logs ../video/out  # ignored by git; Django's file log handlers need logs/, Caddy serves the video from out/

    # aed-domain/settings.py is appended to local.py (init-env.sh); rebuild it so changes in git take effect.
    sed '/"timeout": 1,/d' mcod/settings/local.py.sample | cat - aed-domain/settings.py > mcod/settings/local.py.new
    mv mcod/settings/local.py.new mcod/settings/local.py

    docker compose up -d --build  # no --remove-orphans: env.sample sets COMPOSE_IGNORE_ORPHANS
    # Portal code and the Caddyfile are bind-mounted, so unchanged containers keep the old files: restart them.
    docker compose restart mcod-local-admin mcod-local-api mcod-local-cms mcod-local-celery caddy
    docker compose exec -T mcod-local-admin python manage.py migrate --noinput
    docker compose exec -T mcod-local-admin python manage.py compilemessages >/dev/null

    local domain api admin i
    domain=$(env_value AED_DOMAIN)
    api=$(env_value AED_API_HOST); api=${api:-api.$domain}
    admin=$(env_value AED_ADMIN_HOST); admin=${admin:-admin.$domain}
    for i in $(seq 60); do
        if [ "$(status "$domain" /pl/aed)" = 200 ] && [ "$(status "$domain" /api/aed/statystyki)" = 200 ] \
            && [ "$(status "$api" /aed-aggregated)" -lt 500 ] && [ "$(status "$admin" /)" -lt 500 ]; then
            echo "$new" > "$state/deployed"
            rm -f "$state/failed"
            trap - ERR
            echo "Wdrożono ${new:0:7}."
            return 0
        fi
        sleep 5
    done
    echo "Strony nie odpowiadają po 5 minutach." >&2
    false
}

env_value() { sed -n "s/^$1=//p" .env | tail -1; }
# HTTP status of a page through Caddy on 127.0.0.1:8080 (the tunnel's origin); 000 when nothing answers.
status() { curl -s -o /dev/null --max-time 20 -w '%{http_code}' -H "Host: $1" -H 'X-Forwarded-Proto: https' "http://127.0.0.1:8080$2" || true; }

if [ "${1:-}" = "--apply" ]; then
    apply "$2"
else
    update "$@"
fi
exit
