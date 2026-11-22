#!/bin/sh
# Creates backend/.env for the full-portal deployment under a domain, with fresh random secrets.
# Usage (in backend/):  sh aed-domain/init-env.sh aed.example.pl
# Instruction: docs/wdrozenie-serwer.md
set -eu
cd "$(dirname "$0")/.."
domain=${1:?"podaj domenę, np.: sh aed-domain/init-env.sh aed.example.pl"}
if [ -e .env ]; then
    echo "backend/.env już istnieje - usuń go albo zmień ręcznie (hasło bazy działa tylko przy pierwszym starcie)." >&2
    exit 1
fi
rnd() { openssl rand -hex 32; }

# env.sample is the portal's own template; only its well-known secrets and the private forum image are changed.
sed -e "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(rnd)/" \
    -e "s/^SPARQL_PASSWORD=.*/SPARQL_PASSWORD=$(rnd)/" \
    -e "s/^FIELD_ENCRYPTION_KEYS=.*/FIELD_ENCRYPTION_KEYS=$(rnd)/" \
    -e "s/^DISCOURSE_FORUM_ENABLED=.*/DISCOURSE_FORUM_ENABLED=false/" \
    env.sample > .env

cat >> .env <<EOF

# --- AED: public deployment (aed-domain/, docker-compose.aed-domain.yml) ---
# Plain "docker compose ..." in backend/ uses both files.
COMPOSE_FILE=docker-compose.local.yml:docker-compose.aed-domain.yml
AED_DOMAIN=$domain
DJANGO_SECRET_KEY=$(rnd)
JWT_SECRET_KEY=$(rnd)
# Password of the three AED demo accounts (ministerstwo@, pulsar@, serwis@aed.example); give it to the jury.
AED_DEMO_PASSWORD=$(openssl rand -hex 6)
# Owner of the national AED list dataset: institution 2838 from the portal's start data (rename it in the panel).
MAIN_AED_DATASET_OWNER_ORGANIZATION_PK=2838
EOF
chmod 600 .env
echo "Utworzono backend/.env dla https://$domain"
grep '^AED_DEMO_PASSWORD=' .env
