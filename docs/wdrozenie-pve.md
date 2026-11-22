# Wdrożenie demonstracyjne na Proxmoxie z automatycznym deploymentem

Pełny fork portalu (wariant z `docs/wdrozenie-serwer.md`) działa w kontenerze LXC na serwerze Proxmox zespołu i jest wystawiony do internetu przez Cloudflare Tunnel. Każdy nowy commit na `main` wdraża się sam w ciągu ok. 2 minut (plus czas budowy).

| Adres | Co tam jest |
|---|---|
| `https://aed.heckyeah.pl/pl/aed` | prototyp AED (usługa AED + frontend z forka) |
| `https://aed.heckyeah.pl/pl` | portal z forka |
| `https://aed-api.heckyeah.pl/aed-aggregated` | wykaz AED do odczytu |
| `https://aed-admin.heckyeah.pl` | panel administracyjny (konto jury: `docs/wdrozenie-serwer.md`, rozdział 8) |
| `https://aed-cms.heckyeah.pl` | CMS (Wagtail) |
| `https://aed.heckyeah.pl/prezentacja.html` | prezentacja (`prezentacja-html/prezentacja.html` z wdrożonego commitu) |
| `https://aed.heckyeah.pl/film.mp4` | film (`video/out/misja-aed-pitch.mp4`, wgrywany ręcznie – niżej) |

## Jak to jest zbudowane

```
internet ─► Cloudflare (TLS) ─► tunel aed-demo ─► cloudflared w LXC 118 ─► 127.0.0.1:8080 Caddy (HTTP) ─► kontenery portalu
GitHub fidok15/AED main ◄── git fetch co 2 min (aed-deploy.timer, klucz deploy tylko do odczytu)
```

- **LXC 118 `aed-demo`** na `ssh pve`: Debian 13, 20 rdzeni, 24 GB RAM, 80 GB dysku, nieuprzywilejowany z `nesting` i `keyctl`, `lxc.prlimit.memlock: unlimited` (Elasticsearch), start z hostem. Docker CE i cloudflared z repozytoriów producentów. Repozytorium w `/opt/aed`.
- **Cloudflare Tunnel `aed-demo`** (konfiguracja zdalna, token w `/etc/cloudflared/token`): cztery nazwy → `http://localhost:8080`, rekordy CNAME w strefie `heckyeah.pl`. Na serwerze nie jest otwarty żaden port.
- **Nazwy hostów jednopoziomowe** (`aed-api.` zamiast `api.aed.`): darmowy certyfikat Cloudflare obejmuje tylko `*.heckyeah.pl`. Nakładka domenowa bierze je z `AED_API_HOST`, `AED_ADMIN_HOST`, `AED_CMS_HOST` w `backend/.env`; bez tych zmiennych zostaje dawny układ `api.<domena>`.
- **`backend/docker-compose.aed-tunnel.yml`** – trzeci plik w `COMPOSE_FILE`: Caddy tylko po HTTP na `127.0.0.1:8080`, bez Let's Encrypt, z zaufaniem do `X-Forwarded-Proto` od tunelu (`aed-domain/Caddyfile.tunnel`), żeby Django widziało HTTPS.
- **Ciasteczka panelu tylko dla własnego hosta** (`AED_COOKIE_DOMAIN=` puste): wspólnym rodzicem hostów jest cała strefa `heckyeah.pl`, a w niej działają inne serwisy. Skutek: logowanie we frontendzie nie loguje do panelu (osobne logowanie na `aed-admin.`). Logowanie kont portalu we frontendzie i tak jest wyłączone w buildzie `aed`.

## Automatyczny deployment

`deploy/pve/aed-deploy.sh`, uruchamiany przez `aed-deploy.timer` co 2 minuty (`aed-deploy.service`, limit 1 h na budowę):

1. `git fetch origin main`; nic nie robi, jeśli commit jest już wdrożony albo wcześniej się nie udał.
2. Odrzuca commit bez `backend/docker-compose.aed-tunnel.yml` (bez nakładki tunelu strona by padła).
3. `git checkout --force` na nowy commit i przekazanie dalszych kroków skryptowi z nowego commitu (`--apply`), więc zmiana samego skryptu działa już w tym wdrożeniu. Pliki nieśledzone zostają: `backend/.env`, `mcod/settings/local.py`, `backend/media/`, skompilowane tłumaczenia.
4. Odtwarza `mcod/settings/local.py` z `local.py.sample` i `aed-domain/settings.py` (zmiany ustawień domeny z gita działają od razu).
5. `docker compose up -d --build` (bez `--remove-orphans`: `env.sample` portalu ustawia `COMPOSE_IGNORE_ORPHANS`), restart panelu, API, CMS i Celery (kod portalu jest montowany, więc bez restartu działałby stary), `migrate`, `compilemessages`.
6. Sprawdza przez Caddy: `/pl/aed` i `/api/aed/statystyki` (200), `aed-api./aed-aggregated` i `aed-admin./` (poniżej 500). Dopiero wtedy zapisuje commit jako wdrożony (`/var/lib/aed-deploy/deployed`).

Nieudany commit trafia do `/var/lib/aed-deploy/failed` i nie jest ponawiany, dopóki nie przyjdzie nowszy. Nie ma automatycznego cofania: po nieudanej budowie działają stare kontenery, po nieudanej migracji – nowe kontenery z kodem nowego commitu. Poprawka idzie kolejnym commitem.

Obsługa (`ssh pve`, potem `pct enter 118`):

```sh
journalctl -u aed-deploy -f                       # log wdrożeń
systemctl list-timers aed-deploy.timer            # kiedy następne sprawdzenie
/opt/aed/deploy/pve/aed-deploy.sh --force         # wdrożenie teraz, także ponownie ten sam commit
systemctl disable --now aed-deploy.timer          # wstrzymanie automatu (np. na czas pokazu)
cat /var/lib/aed-deploy/deployed                  # wdrożony commit
cd /opt/aed/backend && docker compose ps          # kontenery
```

Zmiana gałęzi: `systemctl edit aed-deploy.service` i `Environment=AED_BRANCH=<gałąź>`.

## Prezentacja i film

Caddy podaje `/prezentacja.html` wprost z katalogu `prezentacja-html/` repozytorium, więc każde wdrożenie wystawia wersję z `main` bez restartu. Filmu nie ma w gicie (`video/out/` jest w `.gitignore`), dlatego renderuje się go na laptopie i kopiuje na serwer; wdrożenia go nie ruszają:

```sh
cd video && npm ci && npm run render                       # out/misja-aed-pitch.mp4
scp out/misja-aed-pitch.mp4 pve:/tmp/ && ssh pve 'pct push 118 /tmp/misja-aed-pitch.mp4 /opt/aed/video/out/misja-aed-pitch.mp4 && rm /tmp/misja-aed-pitch.mp4'
```

## Klucz deploy (do zrobienia przez właściciela repozytorium)

Repozytorium jest prywatne. LXC pobiera je kluczem `/root/.ssh/aed_deploy` (ed25519, bez hasła, tylko na tym kontenerze). Do czasu dodania klucza timer kończy się błędem `git fetch`, a strona działa na stanie z pierwszego uruchomienia.

Właściciel repozytorium (fidok15): GitHub → `fidok15/AED` → Settings → Deploy keys → Add deploy key, tytuł `aed-demo (Proxmox)`, **bez** „Allow write access”, klucz:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGZLKyRGY9p9APgbpmaWjSJVS+/aQGI8p3O/59KS3emB aed-demo-deploy
```

Sprawdzenie w LXC: `git -C /opt/aed fetch origin main`.

## Pierwsze uruchomienie (wykonane 22.11)

```sh
# na pve
pct create 118 local:vztmpl/debian-13-standard_13.6-1_amd64.tar.zst --hostname aed-demo --cores 20 --memory 24576 \
  --swap 4096 --rootfs local-lvm:80 --net0 name=eth0,bridge=vmbr0,ip=dhcp,type=veth --features nesting=1,keyctl=1 \
  --unprivileged 1 --onboot 1 --tags hacknation
# Elasticsearch żąda memlock bez limitu; bez tego Docker w nieuprzywilejowanym LXC kończy się
# "error setting rlimit type 8: operation not permitted"
echo "lxc.prlimit.memlock: unlimited" >> /etc/pve/lxc/118.conf
# w LXC: docker-ce, docker-compose-plugin, git, cloudflared; repozytorium w /opt/aed (origin git@github.com:fidok15/AED.git)
deploy/pve/bootstrap.sh aed.heckyeah.pl aed-api.heckyeah.pl aed-admin.heckyeah.pl aed-cms.heckyeah.pl
```

`bootstrap.sh` robi kroki z `docs/wdrozenie-serwer.md`, rozdziały 5 i 6, bez ręcznych pytań: `.env` z nowymi sekretami i nazwami hostów, budowa bez Caddy, `init_mcod_db`, indeksy, tłumaczenia, **losowe** hasła `admin@mcod.local` i `pelnomocnik@mcod.local` (zapisane w `/root/aed-credentials.txt` w LXC, nie w repozytorium), nazwa instytucji 2838 „Ministerstwo Cyfryzacji”, `seed_aed_demo`, `create_main_aed_resource`, dopiero na końcu Caddy i włączenie timera. Bez Caddy tunel zwraca 502, więc konta ze znanymi hasłami nie są osiągalne z internetu.

Harmonogram Celery (scalanie wykazów o 03:45 UTC) jest wyłączony jak w nakładce domenowej; włączenie: `AED_CELERY_OPTS` w `backend/.env` (`docs/wdrozenie-serwer.md`, rozdział 4), potem `aed-deploy.sh --force`.

## Wyłączenie

```sh
pct exec 118 -- systemctl disable --now aed-deploy.timer cloudflared   # strona znika z internetu
pct stop 118                                                            # wszystko stoi, dane zostają
pct destroy 118                                                         # usunięcie kontenera z danymi
```

Po `pct destroy` usuń w Cloudflare tunel `aed-demo` i cztery rekordy CNAME `aed*.heckyeah.pl`, a w GitHubie klucz deploy.

## Ograniczenia

- **Jawne hasła demo** (konta usługi AED `…-demo`, `jury@aed.example`) – decyzja 22.11; na serwerze tylko dane otwarte i fikcyjne.
- **Link „Panel” w „Moim pulpicie” frontendu** prowadzi w buildzie `aed` pod `admin.dev.dane.gov.pl` (`frontend/src/app/app.config.ts`) – tak samo było lokalnie; jury wchodzi do panelu adresem `aed-admin.`.
- **Cloudflare przerywa żądanie po 100 s** (plan darmowy, błąd 524). Długie operacje panelu (duże pliki) mogą się nie skończyć w przeglądarce; zadania Celery działają dalej.
- **Wdrożenie bez cofania** (wyżej) i bez testów przed wdrożeniem – timer wdraża to, co jest na `main`.
