#!/bin/bash
# First start of the full portal fork in the LXC aed-demo (docs/wdrozenie-pve.md). Run once, as root, from the
# repository at /opt/aed. Later deploys go through aed-deploy.timer.
#   deploy/pve/bootstrap.sh aed.heckyeah.pl aed-api.heckyeah.pl aed-admin.heckyeah.pl aed-cms.heckyeah.pl
set -euo pipefail
domain=${1:?"podaj domenę frontendu"} api=${2:?"podaj host API"} admin=${3:?"podaj host panelu"} cms=${4:?"podaj host CMS"}
repo=$(cd "$(dirname "$0")/../.." && pwd)
cd "$repo/backend"
# Ignored by git, but Django opens its log files there at start-up, also in the image build (compilemessages).
mkdir -p logs

sh aed-domain/init-env.sh "$domain"
sed -i 's/^COMPOSE_FILE=.*/COMPOSE_FILE=docker-compose.local.yml:docker-compose.aed-domain.yml:docker-compose.aed-tunnel.yml/' .env
cat >> .env <<ENV
# --- AED: Proxmox + Cloudflare Tunnel (deploy/pve/, docker-compose.aed-tunnel.yml) ---
# Flat host names: the free Cloudflare certificate covers one level of subdomains only.
AED_API_HOST=$api
AED_ADMIN_HOST=$admin
AED_CMS_HOST=$cms
# The hosts share only the whole zone as a parent domain: keep the panel's cookies host-only.
AED_COOKIE_DOMAIN=
ENV

manage() { docker compose exec -T mcod-local-admin python manage.py "$@"; }
# Caddy last: init_mcod_db creates accounts with passwords known from the start data.
docker compose up -d --build --scale caddy=0
until manage check >/dev/null 2>&1; do sleep 5; done
manage init_mcod_db
manage search_index --rebuild -f
manage compilemessages >/dev/null

creds=/root/aed-credentials.txt
umask 077
: > "$creds"
for email in admin@mcod.local pelnomocnik@mcod.local; do
    pw=$(openssl rand -base64 18)
    manage shell -c "from django.contrib.auth import get_user_model as m; u=m().objects.get(email='$email'); u.set_password('$pw'); u.save()"
    echo "$email $pw" >> "$creds"
done
echo "Hasła panelu: $creds"

manage shell -c "from mcod.organizations.models import Organization as O; o=O.objects.get(pk=2838); o.title='Ministerstwo Cyfryzacji'; o.save()"
manage seed_aed_demo
manage create_main_aed_resource

docker compose up -d caddy
install -m 0644 "$repo/deploy/pve/aed-deploy.service" "$repo/deploy/pve/aed-deploy.timer" /etc/systemd/system/
systemctl daemon-reload
# The running tree is deployed; the timer takes over from the next commit on origin/main (needs the deploy key).
mkdir -p /var/lib/aed-deploy
git -C "$repo" rev-parse HEAD > /var/lib/aed-deploy/deployed
systemctl enable --now aed-deploy.timer
echo "Gotowe: https://$domain/pl/aed, https://$admin, https://$api/aed-aggregated"
